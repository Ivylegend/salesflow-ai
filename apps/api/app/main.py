from datetime import datetime, timezone
import asyncio
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload
from app.config import settings
from app.database import get_db
from app.models import Appointment, AutomationRun, Email, Lead, LeadActivity, Note, RunStatus, Stage, Temperature, User
from app.schemas import AppointmentIn, AutomationRunIn, EmailLogIn, LeadCreate, LeadOut, NoteCreate, QualificationIn, StageUpdate, TokenOut
from app.security import create_token, current_user, verify_password
from app.services import add_activity, persist_qualification, qualify_with_openai, trigger_n8n, verify_secret

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="SalesFlow AI API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"status":"ok","service":"salesflow-api"}

@app.post("/api/auth/login", response_model=TokenOut)
@limiter.limit("10/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return TokenOut(access_token=create_token(user.id))

async def on_new_lead(lead_id: str):
    from app.database import SessionLocal
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        try:
            if settings.n8n_lead_webhook_url: await trigger_n8n(lead)
            elif settings.openai_api_key:
                data = await asyncio.to_thread(qualify_with_openai, lead); persist_qualification(db, lead, data, settings.openai_model)
        except Exception as exc:
            add_activity(db, lead.id, "automation_failed", "Lead automation failed", str(exc)[:500]); db.commit()

@app.post("/api/public/leads", response_model=LeadOut, status_code=201)
@limiter.limit("8/hour")
def create_lead(request: Request, payload: LeadCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    lead = Lead(**payload.model_dump(), estimated_value={"Under $5k":2500,"$5k–$15k":10000,"$15k–$50k":30000,"$50k+":60000}.get(payload.budget,0))
    db.add(lead); db.flush(); add_activity(db, lead.id, "lead_submitted", "Lead submitted", f"Captured from {lead.source}")
    db.commit(); db.refresh(lead); background.add_task(on_new_lead, lead.id); return lead

@app.get("/api/leads")
def list_leads(q: str = "", classification: Temperature | None = None, stage: Stage | None = None, db: Session = Depends(get_db), _: User = Depends(current_user)):
    stmt = select(Lead).options(selectinload(Lead.emails), selectinload(Lead.appointments)).order_by(Lead.created_at.desc())
    if q: stmt = stmt.where((Lead.full_name.ilike(f"%{q}%")) | (Lead.company.ilike(f"%{q}%")) | (Lead.email.ilike(f"%{q}%")))
    if classification: stmt = stmt.where(Lead.classification == classification)
    if stage: stmt = stmt.where(Lead.stage == stage)
    return db.scalars(stmt).all()

@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    stmt = select(Lead).options(selectinload(Lead.qualification), selectinload(Lead.activities), selectinload(Lead.notes), selectinload(Lead.emails), selectinload(Lead.appointments)).where(Lead.id == lead_id)
    lead = db.scalar(stmt)
    if not lead: raise HTTPException(404, "Lead not found")
    return lead

@app.patch("/api/leads/{lead_id}/stage")
def change_stage(lead_id: str, payload: StageUpdate, db: Session = Depends(get_db), _: User = Depends(current_user)):
    lead = db.get(Lead, lead_id)
    if not lead: raise HTTPException(404, "Lead not found")
    previous = lead.stage; lead.stage = payload.stage
    add_activity(db, lead.id, "pipeline_changed", "Pipeline stage changed", f"{previous.value} → {payload.stage.value}")
    db.commit(); db.refresh(lead); return lead

@app.post("/api/leads/{lead_id}/notes", status_code=201)
def add_note(lead_id: str, payload: NoteCreate, db: Session = Depends(get_db), _: User = Depends(current_user)):
    if not db.get(Lead, lead_id): raise HTTPException(404, "Lead not found")
    note = Note(lead_id=lead_id, body=payload.body.strip()); db.add(note); add_activity(db, lead_id, "note_added", "Note added", payload.body[:200]); db.commit(); db.refresh(note); return note

@app.post("/api/internal/leads/{lead_id}/qualification")
def save_qualification(lead_id: str, payload: QualificationIn, x_salesflow_secret: str | None = Header(None), db: Session = Depends(get_db)):
    if not verify_secret(x_salesflow_secret, settings.n8n_webhook_secret): raise HTTPException(401, "Invalid webhook secret")
    lead = db.get(Lead, lead_id)
    if not lead: raise HTTPException(404, "Lead not found")
    if lead.qualification: return {"status":"already_processed","lead_id":lead.id}
    persist_qualification(db, lead, payload, settings.openai_model); return {"status":"saved","lead_id":lead.id}

@app.post("/api/webhooks/calcom")
def calcom_webhook(payload: AppointmentIn, x_cal_signature_256: str | None = Header(None), x_salesflow_secret: str | None = Header(None), db: Session = Depends(get_db)):
    secret = x_salesflow_secret or x_cal_signature_256
    if not verify_secret(secret, settings.calcom_webhook_secret): raise HTTPException(401, "Invalid webhook secret")
    existing = db.scalar(select(Appointment).where(Appointment.external_id == payload.external_id))
    if existing: return {"status":"duplicate","appointment_id":existing.id}
    lead = db.scalar(select(Lead).where(func.lower(Lead.email) == payload.email.lower()).order_by(Lead.created_at.desc()))
    if not lead: raise HTTPException(404, "No lead matches booking email")
    appointment = Appointment(lead_id=lead.id, **payload.model_dump(exclude={"email"})); db.add(appointment)
    lead.stage = Stage.MEETING; add_activity(db, lead.id, "appointment_scheduled", "Appointment scheduled", payload.starts_at.isoformat())
    db.commit(); db.refresh(appointment); return {"status":"created","appointment_id":appointment.id,"lead_id":lead.id}

@app.post("/api/internal/leads/{lead_id}/emails")
def log_email(lead_id: str, payload: EmailLogIn, x_salesflow_secret: str | None = Header(None), db: Session = Depends(get_db)):
    if not verify_secret(x_salesflow_secret, settings.n8n_webhook_secret): raise HTTPException(401, "Invalid webhook secret")
    if not db.get(Lead, lead_id): raise HTTPException(404, "Lead not found")
    email=Email(lead_id=lead_id,provider_id=payload.provider_id,subject=payload.subject,status=payload.status,sent_at=datetime.now(timezone.utc) if payload.status in {"sent","delivered"} else None)
    db.add(email); add_activity(db,lead_id,"email_failed" if payload.status=="failed" else "email_sent","Email failed" if payload.status=="failed" else "Email sent",payload.error or payload.subject)
    db.commit(); db.refresh(email); return email

@app.post("/api/internal/automation-runs")
def record_run(payload: AutomationRunIn, lead_id: str | None = None, x_salesflow_secret: str | None = Header(None), db: Session = Depends(get_db)):
    if not verify_secret(x_salesflow_secret, settings.n8n_webhook_secret): raise HTTPException(401, "Invalid webhook secret")
    run=db.scalar(select(AutomationRun).where(AutomationRun.idempotency_key==payload.idempotency_key))
    if not run: run=AutomationRun(lead_id=lead_id,workflow=payload.workflow,idempotency_key=payload.idempotency_key);db.add(run)
    run.status=RunStatus(payload.status);run.error=payload.error
    if run.status in {RunStatus.SUCCEEDED,RunStatus.FAILED}: run.completed_at=datetime.now(timezone.utc)
    if lead_id: add_activity(db,lead_id,f"automation_{payload.status}",f"{payload.workflow} {payload.status}",payload.error or "")
    db.commit();db.refresh(run);return run

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(current_user)):
    total = db.scalar(select(func.count()).select_from(Lead)) or 0
    grouped = dict(db.execute(select(Lead.classification, func.count()).group_by(Lead.classification)).all())
    stages = [{"name": s.value, "value": db.scalar(select(func.count()).select_from(Lead).where(Lead.stage == s)) or 0} for s in Stage]
    appointments = db.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == "scheduled")) or 0
    avg_score = db.scalar(select(func.avg(Lead.score)).where(Lead.score.is_not(None))) or 0
    recent = db.scalars(select(Lead).order_by(Lead.created_at.desc()).limit(6)).all()
    activities = db.scalars(select(LeadActivity).order_by(LeadActivity.created_at.desc()).limit(8)).all()
    daily = db.execute(select(func.date(Lead.created_at), func.count()).group_by(func.date(Lead.created_at)).order_by(func.date(Lead.created_at)).limit(14)).all()
    return {"total":total,"hot":grouped.get(Temperature.HOT,0),"warm":grouped.get(Temperature.WARM,0),"cold":grouped.get(Temperature.COLD,0),"appointments":appointments,"average_score":round(float(avg_score),1),"conversion_rate":round(appointments/total*100,1) if total else 0,"pipeline":stages,"recent_leads":recent,"recent_activity":activities,"leads_over_time":[{"date":str(d),"value":c} for d,c in daily]}

@app.get("/api/automations")
def automations(db: Session = Depends(get_db), _: User = Depends(current_user)):
    definitions = [("New Lead Qualification","Lead submitted"),("Hot Lead Follow-Up","Lead classified Hot"),("Warm Lead Nurture","Lead classified Warm"),("Appointment Confirmation","Cal.com booking created"),("No Booking Follow-Up","Delay elapsed without booking"),("Post-Meeting Follow-Up","Meeting completed")]
    result=[]
    for name, trigger in definitions:
        runs=db.scalars(select(AutomationRun).where(AutomationRun.workflow==name)).all(); succeeded=sum(r.status==RunStatus.SUCCEEDED for r in runs)
        result.append({"name":name,"trigger":trigger,"status":"active","runs":len(runs),"success_rate":round(succeeded/len(runs)*100) if runs else None,"last_execution":max((r.started_at for r in runs),default=None)})
    return result
