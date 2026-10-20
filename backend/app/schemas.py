from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(ORM):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DiseaseIn(BaseModel):
    name: str
    scientific_name: str
    crop: str
    severity: str
    description: str
    causes: str
    care: str
    notes: str = ""


class DiseaseUpdate(BaseModel):
    name: str | None = None
    scientific_name: str | None = None
    crop: str | None = None
    severity: str | None = None
    description: str | None = None
    causes: str | None = None
    care: str | None = None
    notes: str | None = None


class DiseaseOut(ORM, DiseaseIn):
    id: int
    validated: bool
    validated_at: datetime | None = None


class PhotoOut(ORM):
    id: int
    width: int
    height: int
    size_bytes: int
    url: str


class FeedbackIn(BaseModel):
    is_correct: bool
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackOut(ORM, FeedbackIn):
    created_at: datetime


class DiagnosticOut(ORM):
    id: int
    crop: str
    severity: str | None
    confidence: float
    needs_review: bool
    model_version: str
    captured_at: datetime
    created_at: datetime
    disease: DiseaseOut | None
    photos: list[PhotoOut]
    feedback: FeedbackOut | None


class RoleUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
