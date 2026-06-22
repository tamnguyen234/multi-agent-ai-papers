from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "AI Paper Multi-Agent System"
    APP_ENV: str = "development"
    
    # Backend Gateway
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    
    # Database configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ai_papers"
    DB_USER: str = "root"
    DB_PASSWORD: str = "your_db_password"
    DATABASE_URL: Optional[str] = None
    
    # JWT security configs
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # SMTP configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "AI Papers Daily"
    
    # Backward compatibility fallbacks
    SMTP_USER: str = ""
    EMAIL_FROM: str = ""
    
    # Storage Directory configuration
    DATA_DIR: str = "./data"
    PAPER_PDF_DIR: str = "./data/paper_pdf"
    AUDIO_ABSTRACT_DIR: str = "./data/audio_abstract"
    FAISS_INDEX_DIR: str = "./data/indices_v2"
    
    # Agent service base URLs
    QA_AGENT_URL: str = "http://127.0.0.1:8103"
    TTS_AGENT_URL: str = "http://127.0.0.1:8104"
    
    # Daily scheduler configurations
    DAILY_DIGEST_CRON_HOUR: int = 2
    DAILY_DIGEST_CRON_MINUTE: int = 0
    ENABLE_SCHEDULER: bool = True
    TIMEZONE: str = "Asia/Bangkok"
    SCHEDULER_TIMEZONE: Optional[str] = None
    DAILY_DIGEST_HOUR: int = 2
    DAILY_DIGEST_MINUTE: int = 0

    # PDF Download configurations
    ENABLE_PDF_DOWNLOAD: bool = True
    PDF_DOWNLOAD_TIMEOUT_SECONDS: int = 30
    MAX_PDF_SIZE_MB: int = 50

    @property
    def database_url(self) -> str:
        """Construct SQLAlchemy database connection string for MySQL using PyMySQL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
