import os
os.environ["DATABASE_URL"]="sqlite:///./test-salesflow.db"
os.environ["JWT_SECRET"]="test-secret-with-enough-length"
os.environ["N8N_WEBHOOK_SECRET"]="test-webhook"
os.environ["CALCOM_WEBHOOK_SECRET"]="test-cal"
from fastapi.testclient import TestClient
import pytest
from app.database import Base, engine, SessionLocal
from app.main import app
from app.models import User
from app.security import hash_password

@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(User(email="admin@test.com",password_hash=hash_password("strong-test-password")))
        db.commit()
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth(client):
    response=client.post('/api/auth/login',data={'username':'admin@test.com','password':'strong-test-password'})
    return {'Authorization':f"Bearer {response.json()['access_token']}"}

@pytest.fixture
def lead_payload():
    return {"full_name":"Amara Okafor","email":"amara@northstar.example","company":"Northstar Labs","job_title":"Operations Director","company_size":"51–200","industry":"B2B Software","interest":"Automate inbound qualification and sales follow-up","budget":"$15k–$50k","timeline":"This month","message":"We need this before our next campaign.","is_demo":True}

