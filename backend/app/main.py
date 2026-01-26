"""
Sentinel Audit API - FastAPI backend for agent audit trail capture
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from .models import AuditEvent, AuditEventResponse
from .db import get_db, init_db, AuditEventDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sentinel Audit API",
    description="Agent audit trail capture and retrieval",
    version="0.1.0"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "service": "Sentinel Audit API",
        "status": "operational",
        "version": "0.1.0"
    }


@app.post("/v1/events", status_code=201)
def create_event(event: AuditEvent, db: Session = Depends(get_db)):
    """
    Capture a new audit event
    
    Privacy-first: metadata is redacted by default
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
            metadata=event.metadata
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Event captured: {event.event_id} for agent {event.agent_instance_id}")
        
        return {"event_id": event.event_id, "status": "captured"}
    
    except Exception as e:
        logger.error(f"Error capturing event: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to capture event: {str(e)}")


@app.get("/v1/agents/{agent_id}/events", response_model=AuditEventResponse)
def get_agent_events(
    agent_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve audit events for a specific agent
    
    Returns events in reverse chronological order (newest first)
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
                metadata=e.metadata or {}
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
        raise HTTPException(status_code=500, detail=f"Failed to retrieve events: {str(e)}")

