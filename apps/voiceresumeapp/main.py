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
from platform_auth import hash_password, verify_password, create_session_token, verify_token, hash_token


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class HealthResponse(BaseModel):
    status: str
    db: str


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
