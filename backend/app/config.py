import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Invoice Verification Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # DB Configuration: PostgreSQL with SQLite local fallback
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./invoice_db.sqlite3"
    )
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-invoice-agent-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    USE_MOCK_LLM_IF_NO_KEY: bool = True
    
    # Verification Thresholds
    PO_PRICE_DEVIATION_THRESHOLD_PERCENT: float = 5.0 # Flag if >5% higher than PO price
    VENDOR_AVG_DEVIATION_THRESHOLD_PERCENT: float = 40.0 # Flag if >40% higher than historical avg
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
