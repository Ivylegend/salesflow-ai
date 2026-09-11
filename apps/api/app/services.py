import asyncio
import hashlib
import hmac
from datetime import datetime, timezone
import httpx
from openai import OpenAI
from sqlalchemy.orm import Session
from app.config import settings
from app.models import AutomationRun, Lead, LeadActivity, LeadQualification, RunStatus, Stage, Temperature
from app.schemas import QualificationIn

QUALIFICATION_SCHEMA = {
  "type": "object", "additionalProperties": False,
  "properties": {
    "score": {"type":"integer","minimum":0,"maximum":100},
    "classification": {"type":"string","enum":["Cold","Warm","Hot"]},
    "intent": {"type":"string","enum":["low","medium","high"]},
    "fit": {"type":"string","enum":["low","medium","high"]},
    "urgency": {"type":"string","enum":["low","medium","high"]},
    "conversion_likelihood": {"type":"integer","minimum":0,"maximum":100},
    "summary": {"type":"string"}, "needs": {"type":"array","items":{"type":"string"}},
    "objections": {"type":"array","items":{"type":"string"}},
    "recommended_action": {"type":"string"}, "follow_up": {"type":"string"}
  },
  "required":["score","classification","intent","fit","urgency","conversion_likelihood","summary","needs","objections","recommended_action","follow_up"]
}

def verify_secret(received: str | None, expected: str) -> bool:
    return bool(received) and hmac.compare_digest(received, expected)

def add_activity(db: Session, lead_id: str, type_: str, title: str, description: str = "", metadata: dict | None = None):
    db.add(LeadActivity(lead_id=lead_id, type=type_, title=title, description=description, metadata_json=metadata or {}))

async def trigger_n8n(lead: Lead):
    if not settings.n8n_lead_webhook_url: return
    payload = {"lead_id": lead.id, "email": lead.email, "full_name": lead.full_name, "company": lead.company, "job_title": lead.job_title, "company_size": lead.company_size, "industry": lead.industry, "interest": lead.interest, "budget": lead.budget, "timeline": lead.timeline, "message": lead.message}
    headers = {"X-SalesFlow-Secret": settings.n8n_webhook_secret, "Idempotency-Key": f"lead:{lead.id}"}
    async with httpx.AsyncClient(timeout=10) as client:
        for attempt in range(3):
            try:
                response = await client.post(settings.n8n_lead_webhook_url, json=payload, headers=headers)
                response.raise_for_status(); return
            except Exception:
                if attempt == 2: raise
                await asyncio.sleep(2 ** attempt)

def qualify_with_openai(lead: Lead) -> QualificationIn:
    client = OpenAI(api_key=settings.openai_api_key, timeout=30, max_retries=2)
    result = client.responses.create(
        model=settings.openai_model,
        instructions="You qualify B2B SaaS sales leads. Score evidence conservatively. Classification must be Cold for 0-39, Warm for 40-69, Hot for 70-100. Provide concise, useful sales guidance.",
        input=f"Lead: {lead.full_name}, {lead.job_title} at {lead.company}. Company size: {lead.company_size}. Industry: {lead.industry}. Need: {lead.interest}. Budget: {lead.budget}. Timeline: {lead.timeline}. Message: {lead.message or 'None'}",
        text={"format":{"type":"json_schema","name":"lead_qualification","strict":True,"schema":QUALIFICATION_SCHEMA}},
    )
    return QualificationIn.model_validate_json(result.output_text)

def persist_qualification(db: Session, lead: Lead, data: QualificationIn, model: str):
    qualification = LeadQualification(lead_id=lead.id, model=model, **data.model_dump())
    lead.score, lead.classification = data.score, data.classification
    if lead.stage == Stage.NEW and data.score >= 40: lead.stage = Stage.QUALIFIED
    db.add(qualification)
    add_activity(db, lead.id, "qualification_completed", "AI qualification completed", f"Scored {data.score}/100 · {data.classification.value}")
    db.commit(); db.refresh(lead)
    return qualification

