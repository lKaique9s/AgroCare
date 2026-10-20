from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

CROPS = ("Café", "Soja", "Milho")
ROLES = ("producer", "agronomist", "admin")
SEVERITIES = ("baixa", "moderada", "alta")


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):  # RF13, RF14, RF17
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="producer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Disease(Base):  # RF15, RF16, RF20
    __tablename__ = "diseases"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    scientific_name: Mapped[str] = mapped_column(String(200))
    crop: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    causes: Mapped[str] = mapped_column(Text)
    care: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Diagnostic(Base):  # RF01-RF07, RF10
    __tablename__ = "diagnostics"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    crop: Mapped[str] = mapped_column(String(20), index=True)
    disease_id: Mapped[int | None] = mapped_column(ForeignKey("diseases.id"), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str] = mapped_column(String(80))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    disease: Mapped[Disease | None] = relationship()
    photos: Mapped[list["DiagnosticPhoto"]] = relationship(
        cascade="all, delete-orphan", order_by="DiagnosticPhoto.id")
    feedback: Mapped["Feedback | None"] = relationship(uselist=False, cascade="all, delete-orphan")


class DiagnosticPhoto(Base):
    __tablename__ = "diagnostic_photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostic_id: Mapped[int] = mapped_column(ForeignKey("diagnostics.id"), index=True)
    path: Mapped[str] = mapped_column(String(300))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)  # probabilidades por classe

    @property
    def url(self) -> str:
        return f"/diagnostics/{self.diagnostic_id}/photos/{self.id}"


class Feedback(Base):  # RF19
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostic_id: Mapped[int] = mapped_column(ForeignKey("diagnostics.id"), unique=True)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
