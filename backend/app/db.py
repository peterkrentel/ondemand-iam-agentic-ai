"""
Database setup and models for SQLite
"""
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aimgentix.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AuditEventDB(Base):
    """SQLAlchemy model for audit events"""
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    agent_instance_id = Column(String, index=True, nullable=False)
    trace_id = Column(String, index=True, nullable=False)
    actor = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    status = Column(String, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    event_metadata = Column(JSON, nullable=True)


def init_db():
    """Initialize the database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

