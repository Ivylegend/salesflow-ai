from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import Stage, Temperature

class LeadCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    company: str = Field(min_length=2, max_length=180)
    job_title: str = Field(min_length=2, max_length=160)
    company_size: str = Field(min_length=1, max_length=80)
    industry: str = Field(min_length=2, max_length=120)
    interest: str = Field(min_length=10, max_length=2000)
    budget: str = Field(min_length=1, max_length=80)
    timeline: str = Field(min_length=1, max_length=80)
    message: str | None = Field(default=None, max_length=3000)
    source: str = Field(default="Website", max_length=80)
    is_demo: bool = False
    @field_validator("full_name", "company", "job_title", "industry", "interest", "message")
    @classmethod
    def strip_text(cls, value): return value.strip() if isinstance(value, str) else value

class QualificationIn(BaseModel):
    score: int = Field(ge=0, le=100)
    classification: Temperature
    intent: Literal["low", "medium", "high"]
    fit: Literal["low", "medium", "high"]
    urgency: Literal["low", "medium", "high"]
    conversion_likelihood: int = Field(ge=0, le=100)
    summary: str = Field(min_length=10, max_length=2000)
    needs: list[str] = Field(min_length=1, max_length=8)
    objections: list[str] = Field(default_factory=list, max_length=8)
    recommended_action: str = Field(min_length=5, max_length=1000)
    follow_up: str = Field(min_length=10, max_length=3000)
    @field_validator("classification")
    @classmethod
    def score_matches(cls, value, info):
        score = info.data.get("score")
        expected = Temperature.COLD if score is not None and score < 40 else Temperature.WARM if score is not None and score < 70 else Temperature.HOT
        if score is not None and value != expected: raise ValueError("classification must match score")
        return value

class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; full_name: str; email: str; company: str; job_title: str; company_size: str; industry: str
    interest: str; budget: str; timeline: str; message: str | None; source: str; is_demo: bool; stage: Stage
    score: int | None; classification: Temperature | None; estimated_value: float; created_at: datetime; updated_at: datetime

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StageUpdate(BaseModel): stage: Stage
class NoteCreate(BaseModel): body: str = Field(min_length=1, max_length=3000)
class AppointmentIn(BaseModel):
    external_id: str = Field(min_length=2, max_length=180)
    email: EmailStr
    starts_at: datetime
    ends_at: datetime | None = None
    status: str = Field(default="scheduled", max_length=40)
    booking_url: str | None = None

class EmailLogIn(BaseModel):
    provider_id: str | None = None
    subject: str = Field(min_length=2, max_length=255)
    status: Literal["queued", "sent", "delivered", "failed"]
    error: str | None = Field(default=None, max_length=1000)

class AutomationRunIn(BaseModel):
    workflow: str = Field(min_length=2, max_length=120)
    status: Literal["pending", "running", "succeeded", "failed"]
    idempotency_key: str = Field(min_length=3, max_length=180)
    error: str | None = Field(default=None, max_length=1000)
