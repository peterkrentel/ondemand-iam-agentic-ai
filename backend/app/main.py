"""
AIMgentix API - FastAPI backend for agent audit trail capture
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
import os

from .models import AuditEvent, AuditEventResponse
from .db import get_db, init_db, AuditEventDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown (if needed)


# Initialize FastAPI app
app = FastAPI(
    title="AIMgentix API",
    description="""
    ## Lightweight audit layer for AI agents
    
    **Privacy-first. Production-ready.**
    
    Capture what your AI agents do - tool calls, API requests, file access - 
    and get a complete audit trail for visibility, compliance, and security.
    
    ### Features
    - ✅ Non-blocking event capture
    - ✅ Privacy-first (redacts sensitive data by default)
    - ✅ Framework agnostic
    - ✅ Simple integration
    
    ### Authentication
    Currently no authentication required (development mode).
    Production deployments should implement proper authentication.
    """,
    version="0.1.0",
    contact={
        "name": "Peter Krentel",
        "url": "https://github.com/peterkrentel/ondemand-iam-agentic-ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - configured based on environment
# In production, set ALLOWED_ORIGINS environment variable
if ENVIRONMENT == "development":
    # Development: Allow localhost origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
else:
    # Production: Strict CORS policy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )


@app.get("/", tags=["Health"])
def root():
    """
    Health check endpoint
    
    Returns the service status and version information.
    """
    return {
        "service": "AIMgentix API",
        "status": "operational",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.post("/v1/events", status_code=201, tags=["Events"])
def create_event(event: AuditEvent, db: Session = Depends(get_db)):
    """
    Capture a new audit event
    
    **Privacy-first**: metadata is redacted by default. Only capture what you need.
    
    ### Request Body
    - **event_id**: Unique event identifier (UUID)
    - **timestamp**: ISO8601 timestamp (auto-generated if not provided)
    - **agent_instance_id**: Unique agent instance identifier
    - **trace_id**: Trace ID for correlating related events
    - **actor**: Type of actor (agent, human, system)
    - **action_type**: Type of action performed
    - **resource**: Resource being accessed (URL, file path, etc.)
    - **status**: Status of the action (success, error, pending)
    - **latency_ms**: Latency in milliseconds (optional)
    - **metadata**: Additional context, redacted by default (optional)
    
    ### Response
    Returns the event_id and capture status.
    """
    try:
        # Create database record
        db_event = AuditEventDB(
            event_id=event.event_id,
            timestamp=event.timestamp,
            agent_instance_id=event.agent_instance_id,
            trace_id=event.trace_id,
            actor=event.actor.value,
            action_type=event.action_type.value,
            resource=event.resource,
            status=event.status.value,
            latency_ms=event.latency_ms,
            event_metadata=event.metadata
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Event captured: {event.event_id} for agent {event.agent_instance_id}")
        
        return {"event_id": event.event_id, "status": "captured"}
    
    except Exception as e:
        logger.error(f"Error capturing event: {str(e)}")
        db.rollback()
        # Don't expose internal error details to client
        raise HTTPException(status_code=500, detail="Failed to capture event")


@app.get("/v1/agents/{agent_id}/events", response_model=AuditEventResponse, tags=["Events"])
def get_agent_events(
    agent_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve audit events for a specific agent
    
    Returns events in reverse chronological order (newest first).
    
    ### Path Parameters
    - **agent_id**: Unique agent instance identifier
    
    ### Query Parameters
    - **limit**: Maximum number of events to return (default: 100, max: 1000)
    
    ### Response
    Returns list of events, total count, and agent_instance_id.
    """
    try:
        # Query events for this agent
        events = db.query(AuditEventDB).filter(
            AuditEventDB.agent_instance_id == agent_id
        ).order_by(
            AuditEventDB.timestamp.desc()
        ).limit(limit).all()
        
        # Convert to response model
        audit_events = [
            AuditEvent(
                event_id=e.event_id,
                timestamp=e.timestamp,
                agent_instance_id=e.agent_instance_id,
                trace_id=e.trace_id,
                actor=e.actor,
                action_type=e.action_type,
                resource=e.resource,
                status=e.status,
                latency_ms=e.latency_ms,
                metadata=e.event_metadata or {}
            )
            for e in events
        ]
        
        total = db.query(AuditEventDB).filter(
            AuditEventDB.agent_instance_id == agent_id
        ).count()
        
        logger.info(f"Retrieved {len(audit_events)} events for agent {agent_id}")
        
        return AuditEventResponse(
            events=audit_events,
            total=total,
            agent_instance_id=agent_id
        )
    
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        # Don't expose internal error details to client
        raise HTTPException(status_code=500, detail="Failed to retrieve events")

