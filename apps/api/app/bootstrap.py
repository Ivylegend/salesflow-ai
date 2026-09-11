from sqlalchemy import select
from app.config import settings
from app.database import SessionLocal
from app.models import Lead, LeadActivity, LeadQualification, Stage, Temperature, User
from app.security import hash_password

def main():
    with SessionLocal() as db:
        if settings.admin_password and not db.scalar(select(User).where(User.email == settings.admin_email.lower())):
            db.add(User(email=settings.admin_email.lower(), password_hash=hash_password(settings.admin_password)))
            db.commit(); print("Administrator created")
        if settings.seed_demo_data and not db.scalar(select(Lead).where(Lead.is_demo.is_(True))):
            rows=[("Amara Okafor","Northstar Labs","Operations Director",86,Temperature.HOT,Stage.QUALIFIED,"This month","$15k–$50k"),("Daniel Brooks","Harbor & Field","Revenue Lead",73,Temperature.HOT,Stage.CONTACTED,"1–3 months","$15k–$50k"),("Lina Chen","Orbitline Studio","Founder",61,Temperature.WARM,Stage.NEW,"3–6 months","$5k–$15k"),("Malik Evans","Canopy Works","Sales Manager",54,Temperature.WARM,Stage.MEETING,"1–3 months","$5k–$15k"),("Sofia Martins","Kitewell Health","Growth Manager",34,Temperature.COLD,Stage.NEW,"Exploring","Under $5k")]
            for name,company,title,score,temp,stage,timeline,budget in rows:
                lead=Lead(full_name=name,email=f"{name.lower().replace(' ','.')}@example.com",company=company,job_title=title,company_size="51–200",industry="B2B Services",interest="Improve inbound lead qualification and create a reliable follow-up process.",budget=budget,timeline=timeline,message="Seeded portfolio demonstration record.",source="Sample data",is_demo=True,stage=stage,score=score,classification=temp,estimated_value=10000)
                db.add(lead);db.flush()
                db.add(LeadQualification(lead_id=lead.id,score=score,classification=temp,intent="high" if score>=70 else "medium" if score>=40 else "low",fit="high" if score>=70 else "medium",urgency="high" if timeline=="This month" else "medium",conversion_likelihood=max(score-7,5),summary=f"{name} represents a {temp.value.lower()} opportunity with a clearly stated interest in sales process automation.",needs=["Faster lead response","Consistent qualification","Visible follow-up history"],objections=["Implementation effort","Team adoption"],recommended_action="Share a concise workflow recommendation and invite the buyer to a discovery call.",follow_up="Thanks for sharing your current process. We have a practical way to make qualification and follow-up much more consistent.",model="seeded-demo"))
                db.add(LeadActivity(lead_id=lead.id,type="lead_submitted",title="Sample lead created",description="Seeded portfolio demonstration record"));db.add(LeadActivity(lead_id=lead.id,type="qualification_completed",title="AI qualification completed",description=f"Scored {score}/100 · {temp.value}"))
            db.commit();print("Demo data seeded")
if __name__ == "__main__": main()
