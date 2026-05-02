import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Cookie, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from uuid import UUID

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from platform_db import User, get_db, init_db
from platform_db.models import PasswordResetToken
from platform_auth import hash_password, verify_password, create_session_token, verify_token, hash_token, generate_reset_token, get_reset_token_expiry
from platform_auth.email import send_email, generate_reset_email


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class HealthResponse(BaseModel):
    status: str
    db: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="VoiceResume API",
    description="Voice memos to resume generation",
    version="0.1.0",
    lifespan=lifespan,
)

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")


def get_current_user(session_token: str | None = Cookie(None), db: Session = Depends(get_db)) -> User | None:
    if not session_token:
        return None

    token_data = verify_token(session_token, SECRET_KEY)
    if not token_data:
        return None

    user_id = token_data.get("sub")
    if not user_id:
        return None

    from platform_db.database import SessionLocal
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return user
    finally:
        session.close()


@app.get("/health", response_model=HealthResponse)
async def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    return HealthResponse(status="ok", db=db_status)


@app.post("/auth/signup")
async def signup(req: SignUpRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": str(user.id), "email": user.email, "created_at": user.created_at}


@app.post("/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session_token(user.id, SECRET_KEY)
    response = JSONResponse(content={"id": str(user.id), "email": user.email})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="strict",
        max_age=30 * 24 * 60 * 60,
    )
    return response


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Logged out"}


@app.post("/auth/password-reset-request")
async def request_password_reset(req: PasswordResetRequest, db: Session = Depends(get_db)):
    import asyncio
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        return {"message": "If email exists, a reset link will be sent"}

    reset_token = generate_reset_token()
    token_hash = hash_token(reset_token)

    existing_reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).first()
    if existing_reset:
        db.delete(existing_reset)

    password_reset = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=get_reset_token_expiry(),
    )
    db.add(password_reset)
    db.commit()

    reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
    subject, body = generate_reset_email(user.email, reset_url)
    asyncio.create_task(send_email(user.email, subject, body))

    return {"message": "If email exists, a reset link will be sent"}


@app.post("/auth/password-reset-confirm")
async def confirm_password_reset(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hash_token(req.token)

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()

    if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.password_hash = hash_password(req.new_password)
    db.delete(reset_token)
    db.commit()

    return {"message": "Password reset successful"}


@app.delete("/auth/sessions")
async def cleanup_expired_sessions(db: Session = Depends(get_db)):
    from platform_db.models import Session as SessionModel
    expired_sessions = db.query(SessionModel).filter(
        SessionModel.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit()
    return {"deleted_sessions": expired_sessions}


@app.get("/auth/sessions")
async def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from platform_db.models import Session as SessionModel
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).all()

    return {
        "sessions": [
            {
                "id": str(s.id),
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
            }
            for s in sessions
        ]
    }


@app.delete("/auth/sessions/{session_id}")
async def delete_session(session_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from platform_db.models import Session as SessionModel
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"message": "Session deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
