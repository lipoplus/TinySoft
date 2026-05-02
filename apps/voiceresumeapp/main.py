import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import openai
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "packages"))

from platform_auth import (
    create_session_token,
    generate_reset_token,
    get_reset_token_expiry,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
)
from platform_auth.email import generate_reset_email, send_email
from platform_db import (
    GeneratedResume,
    Transcription,
    User,
    VoiceMemo,
    get_db,
    init_db,
)
from platform_db.models import PasswordResetToken


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


class MemoUploadResponse(BaseModel):
    id: str
    file_name: str
    status: str
    created_at: datetime


class TranscriptionResponse(BaseModel):
    id: str
    memo_id: str
    text: str
    language: str | None
    created_at: datetime


class ResumeResponse(BaseModel):
    id: str
    memo_id: str
    resume_text: str
    created_at: datetime


class MemoDetailResponse(BaseModel):
    id: str
    file_name: str
    status: str
    created_at: datetime
    transcription: TranscriptionResponse | None
    resume: ResumeResponse | None


MEMOS_DIR = Path("/tmp/voice_memos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    MEMOS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="VoiceResume API",
    description="Voice memos to resume generation",
    version="0.1.0",
    lifespan=lifespan,
)

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

ALLOWED_AUDIO_FORMATS = {"audio/mpeg", "audio/wav", "audio/webm", "audio/ogg"}
MAX_FILE_SIZE = 25 * 1024 * 1024


def get_current_user(
    session_token: str | None = Cookie(None), db: Session = Depends(get_db)
) -> User | None:
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

    existing_reset = (
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()
    )
    if existing_reset:
        db.delete(existing_reset)

    password_reset = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=get_reset_token_expiry(),
    )
    db.add(password_reset)
    db.commit()

    reset_url = (
        f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
    )
    subject, body = generate_reset_email(user.email, reset_url)
    asyncio.create_task(send_email(user.email, subject, body))

    return {"message": "If email exists, a reset link will be sent"}


@app.post("/auth/password-reset-confirm")
async def confirm_password_reset(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hash_token(req.token)

    reset_token = (
        db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    )

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

    expired_sessions = (
        db.query(SessionModel).filter(SessionModel.expires_at < datetime.now(timezone.utc)).delete()
    )
    db.commit()
    return {"deleted_sessions": expired_sessions}


@app.get("/auth/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from platform_db.models import Session as SessionModel

    sessions = db.query(SessionModel).filter(SessionModel.user_id == current_user.id).all()

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
async def delete_session(
    session_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from platform_db.models import Session as SessionModel

    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id,
            SessionModel.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"message": "Session deleted"}


@app.post("/memos/upload", response_model=MemoUploadResponse)
async def upload_memo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if file.content_type not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format. Allowed: {', '.join(ALLOWED_AUDIO_FORMATS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    memo = VoiceMemo(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=str(MEMOS_DIR / f"{uuid4().hex}_{file.filename}"),
        status="uploaded",
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)

    file_path = Path(memo.file_path)
    file_path.write_bytes(content)

    return MemoUploadResponse(
        id=str(memo.id), file_name=memo.file_name, status=memo.status, created_at=memo.created_at
    )


@app.post("/memos/{memo_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_memo(
    memo_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    memo = (
        db.query(VoiceMemo)
        .filter(VoiceMemo.id == memo_id, VoiceMemo.user_id == current_user.id)
        .first()
    )

    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    existing_transcription = (
        db.query(Transcription).filter(Transcription.memo_id == memo_id).first()
    )

    if existing_transcription:
        return TranscriptionResponse(
            id=str(existing_transcription.id),
            memo_id=str(existing_transcription.memo_id),
            text=existing_transcription.text,
            language=existing_transcription.language,
            created_at=existing_transcription.created_at,
        )

    try:
        with open(memo.file_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, language="en"
            )

        transcription = Transcription(memo_id=memo_id, text=transcript.text, language="en")
        db.add(transcription)
        memo.status = "transcribed"
        db.commit()
        db.refresh(transcription)

        return TranscriptionResponse(
            id=str(transcription.id),
            memo_id=str(transcription.memo_id),
            text=transcription.text,
            language=transcription.language,
            created_at=transcription.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/memos/{memo_id}/generate-resume", response_model=ResumeResponse)
async def generate_resume(
    memo_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    memo = (
        db.query(VoiceMemo)
        .filter(VoiceMemo.id == memo_id, VoiceMemo.user_id == current_user.id)
        .first()
    )

    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    transcription = db.query(Transcription).filter(Transcription.memo_id == memo_id).first()

    if not transcription:
        raise HTTPException(status_code=400, detail="Memo must be transcribed first")

    existing_resume = db.query(GeneratedResume).filter(GeneratedResume.memo_id == memo_id).first()

    if existing_resume:
        return ResumeResponse(
            id=str(existing_resume.id),
            memo_id=str(existing_resume.memo_id),
            resume_text=existing_resume.resume_text,
            created_at=existing_resume.created_at,
        )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Convert the provided voice memo transcript into a professional resume. Format it as a well-structured resume with sections for contact info, summary, experience, skills, and education if mentioned.",
                },
                {
                    "role": "user",
                    "content": f"Please convert this voice memo transcript into a professional resume:\n\n{transcription.text}",
                },
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        resume_text = response.choices[0].message.content

        resume = GeneratedResume(memo_id=memo_id, resume_text=resume_text)
        db.add(resume)
        memo.status = "completed"
        db.commit()
        db.refresh(resume)

        return ResumeResponse(
            id=str(resume.id),
            memo_id=str(resume.memo_id),
            resume_text=resume.resume_text,
            created_at=resume.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")


@app.get("/memos")
async def list_memos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    memos = (
        db.query(VoiceMemo)
        .filter(VoiceMemo.user_id == current_user.id)
        .order_by(VoiceMemo.created_at.desc())
        .all()
    )

    return {
        "memos": [
            {
                "id": str(memo.id),
                "file_name": memo.file_name,
                "status": memo.status,
                "created_at": memo.created_at,
                "has_transcription": memo.transcription is not None,
                "has_resume": memo.resume is not None,
            }
            for memo in memos
        ]
    }


@app.get("/memos/{memo_id}", response_model=MemoDetailResponse)
async def get_memo_detail(
    memo_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    memo = (
        db.query(VoiceMemo)
        .filter(VoiceMemo.id == memo_id, VoiceMemo.user_id == current_user.id)
        .first()
    )

    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    transcription_data = None
    if memo.transcription:
        transcription_data = TranscriptionResponse(
            id=str(memo.transcription.id),
            memo_id=str(memo.transcription.memo_id),
            text=memo.transcription.text,
            language=memo.transcription.language,
            created_at=memo.transcription.created_at,
        )

    resume_data = None
    if memo.resume:
        resume_data = ResumeResponse(
            id=str(memo.resume.id),
            memo_id=str(memo.resume.memo_id),
            resume_text=memo.resume.resume_text,
            created_at=memo.resume.created_at,
        )

    return MemoDetailResponse(
        id=str(memo.id),
        file_name=memo.file_name,
        status=memo.status,
        created_at=memo.created_at,
        transcription=transcription_data,
        resume=resume_data,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
