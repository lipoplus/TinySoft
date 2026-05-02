from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="sessions")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


class VoiceMemo(Base):
    __tablename__ = "voice_memos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    transcription = relationship("Transcription", back_populates="memo", uselist=False)
    resume = relationship("GeneratedResume", back_populates="memo", uselist=False)


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    memo_id = Column(UUID(as_uuid=True), ForeignKey("voice_memos.id"), nullable=False, index=True, unique=True)
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    memo = relationship("VoiceMemo", back_populates="transcription")


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    memo_id = Column(UUID(as_uuid=True), ForeignKey("voice_memos.id"), nullable=False, index=True, unique=True)
    resume_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    memo = relationship("VoiceMemo", back_populates="resume")
