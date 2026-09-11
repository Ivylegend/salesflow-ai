from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./salesflow.db"
    jwt_secret: str = "local-development-only-change-me"
    admin_email: str = "admin@example.com"
    admin_password: str = ""
    access_token_minutes: int = 480
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    n8n_lead_webhook_url: str = ""
    n8n_webhook_secret: str = "local-webhook-secret"
    resend_api_key: str = ""
    resend_from_email: str = "SalesFlow AI <hello@example.com>"
    calcom_booking_url: str = ""
    calcom_webhook_secret: str = ""
    seed_demo_data: bool = True
    cors_origins: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
