from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Construct SQLAlchemy database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # Verifies connection health before checks
    pool_recycle=3600         # Recycle connections after an hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency injection helper yielding active database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_connection() -> bool:
    """Execute raw query 'SELECT 1' to verify connection is alive."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
