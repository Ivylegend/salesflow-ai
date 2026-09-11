import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def now(): return datetime.now(timezone.utc)

class Stage(str, enum.Enum):
    NEW = "New Lead"
    QUALIFIED = "Qualified"
    CONTACTED = "Contacted"
    MEETING = "Meeting Scheduled"
    PROPOSAL = "Proposal"
    WON = "Won"
    LOST = "Lost"

class Temperature(str, enum.Enum):
    COLD = "Cold"
    WARM = "Warm"
    HOT = "Hot"

class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120), default="Demo Administrator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    company: Mapped[str] = mapped_column(String(180))
    job_title: Mapped[str] = mapped_column(String(160))
    company_size: Mapped[str] = mapped_column(String(80))
    industry: Mapped[str] = mapped_column(String(120))
    interest: Mapped[str] = mapped_column(Text)
    budget: Mapped[str] = mapped_column(String(80))
    timeline: Mapped[str] = mapped_column(String(80))
    message: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), default="Website")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    stage: Mapped[Stage] = mapped_column(Enum(Stage), default=Stage.NEW, index=True)
    score: Mapped[int | None] = mapped_column(Integer)
    classification: Mapped[Temperature | None] = mapped_column(Enum(Temperature), index=True)
    estimated_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    qualification: Mapped["LeadQualification | None"] = relationship(back_populates="lead", uselist=False, cascade="all, delete-orphan")
    activities: Mapped[list["LeadActivity"]] = relationship(back_populates="lead", cascade="all, delete-orphan", order_by="desc(LeadActivity.created_at)")
    notes: Mapped[list["Note"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    emails: Mapped[list["Email"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="lead", cascade="all, delete-orphan")

class LeadQualification(Base):
    __tablename__ = "lead_qualifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), unique=True, index=True)
    score: Mapped[int] = mapped_column(Integer)
    classification: Mapped[Temperature] = mapped_column(Enum(Temperature))
    intent: Mapped[str] = mapped_column(String(80))
    fit: Mapped[str] = mapped_column(String(80))
    urgency: Mapped[str] = mapped_column(String(80))
    conversion_likelihood: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    needs: Mapped[list] = mapped_column(JSON)
    objections: Mapped[list] = mapped_column(JSON)
    recommended_action: Mapped[str] = mapped_column(Text)
    follow_up: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(80), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    lead: Mapped[Lead] = relationship(back_populates="qualification")

class LeadActivity(Base):
    __tablename__ = "lead_activities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    lead: Mapped[Lead] = relationship(back_populates="activities")

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    lead: Mapped[Lead] = relationship(back_populates="notes")

class Email(Base):
    __tablename__ = "emails"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    provider_id: Mapped[str | None] = mapped_column(String(160))
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lead: Mapped[Lead] = relationship(back_populates="emails")

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (UniqueConstraint("external_id", name="uq_appointment_external_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(180))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default="scheduled")
    booking_url: Mapped[str | None] = mapped_column(Text)
    lead: Mapped[Lead] = relationship(back_populates="appointments")

class AutomationRun(Base):
    __tablename__ = "automation_runs"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_automation_idempotency"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"), index=True)
    workflow: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING)
    idempotency_key: Mapped[str] = mapped_column(String(180))
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

