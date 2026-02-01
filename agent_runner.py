#!/usr/bin/env python3
"""
GitHub Actions Agent Runner

This script implements the investigate → approve → act pattern for GitHub Actions.
It integrates with AIMgentix for complete audit trails.

Usage:
  python agent_runner.py investigate --resource <resource> --trace-id <trace-id>
  python agent_runner.py act --resource <resource> --trace-id <trace-id> --action <action>

Environment Variables:
  AIMGENTIX_API_URL: URL of AIMgentix backend (default: http://localhost:8000)
  TRACE_ID: Unique trace ID for audit correlation
  AGENT_INSTANCE_ID: Agent instance identifier (e.g., gh-actions-123456)
  TARGET_RESOURCE: Resource to investigate/act on
  ACTION_CONTEXT: Additional context as JSON string
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional

# Import AIMgentix SDK (if available)
try:
    from aimgentix import ActionType, ActorType, AuditClient, AuditEvent, EventStatus
    AIMGENTIX_AVAILABLE = True
except ImportError:
    AIMGENTIX_AVAILABLE = False
    logging.warning("AIMgentix SDK not available. Running without audit trail.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class InvestigationResult:
    """Result of an investigation"""
    timestamp: str
    resource: str
    status: str
    risk_level: str
    issues_found: list
    recommendation: str
    confidence: float
    analysis: Dict[str, Any]
    safe_to_proceed: bool


@dataclass
class ActionResult:
    """Result of an action execution"""
    timestamp: str
    resource: str
    action: str
    status: str
    latency_ms: int
    details: Dict[str, Any]


class AgentRunner:
    """GitHub Actions agent runner with AIMgentix integration"""
    
    def __init__(
        self,
        trace_id: str,
        agent_instance_id: str,
        audit_api_url: Optional[str] = None
    ):
        self.trace_id = trace_id
        self.agent_instance_id = agent_instance_id
        self.audit_client = None
        
        if AIMGENTIX_AVAILABLE:
            api_url = audit_api_url or os.getenv('AIMGENTIX_API_URL', 'http://localhost:8000')
            try:
                self.audit_client = AuditClient(api_url=api_url)
                logger.info(f"✅ AIMgentix audit client initialized: {api_url}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize audit client: {e}")
    
    def _capture_event(
        self,
        action_type: str,
        resource: str,
        status: str,
        latency_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Capture an audit event (fail-open if audit unavailable)"""
        if not self.audit_client:
            return
        
        try:
            event = AuditEvent(
                agent_instance_id=self.agent_instance_id,
                trace_id=self.trace_id,
                actor=ActorType.AGENT,
                action_type=getattr(ActionType, action_type.upper()),
                resource=resource,
                status=getattr(EventStatus, status.upper()),
                latency_ms=latency_ms,
                metadata=metadata or {}
            )
            self.audit_client.capture(event)
            logger.debug(f"📊 Audit event captured: {action_type} on {resource}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to capture audit event: {e}")
    
    def investigate(
        self,
        resource: str,
        context: Optional[Dict[str, Any]] = None
    ) -> InvestigationResult:
        """
        Investigate a resource (read-only analysis)
        
        This is a simulation. In a real implementation:
        - Check resource health/status
        - Analyze logs and metrics
        - Detect issues and anomalies
        - Provide recommendation
        """
        logger.info(f"🔍 Starting investigation of resource: {resource}")
        
        start_time = time.time()
        
        # Capture investigation start event
        self._capture_event(
            action_type="tool_call",
            resource=f"investigate:{resource}",
            status="pending",
            metadata={"phase": "investigate_start", "context": context}
        )
        
        try:
            # Simulate investigation logic
            # In real implementation, this would:
            # - Query monitoring systems
            # - Check service health
            # - Analyze recent logs
            # - Check dependencies
            time.sleep(1)  # Simulate API calls
            
            # Example analysis
            analysis = {
                "resource_exists": True,
                "last_modified": datetime.utcnow().isoformat() + "Z",
                "health_status": "healthy",
                "error_rate_1h": 0.001,
                "latency_p99_1h": 250,
                "dependencies_healthy": True,
                "recent_deployments": 0,
                "current_load": 0.45
            }
            
            # Determine risk level
            error_rate = analysis["error_rate_1h"]
            if error_rate < 0.01:
                risk_level = "low"
                confidence = 0.95
            elif error_rate < 0.05:
                risk_level = "medium"
                confidence = 0.80
            else:
                risk_level = "high"
                confidence = 0.70
            
            # Generate recommendation
            if risk_level == "low":
                recommendation = "safe_to_proceed"
            elif risk_level == "medium":
                recommendation = "proceed_with_caution"
            else:
                recommendation = "manual_review_required"
            
            safe_to_proceed = risk_level in ["low", "medium"] and confidence > 0.70
            
            result = InvestigationResult(
                timestamp=datetime.utcnow().isoformat() + "Z",
                resource=resource,
                status="completed",
                risk_level=risk_level,
                issues_found=[],
                recommendation=recommendation,
                confidence=confidence,
                analysis=analysis,
                safe_to_proceed=safe_to_proceed
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Capture investigation completion event
            self._capture_event(
                action_type="tool_call",
                resource=f"investigate:{resource}",
                status="success",
                latency_ms=latency_ms,
                metadata={
                    "phase": "investigate_complete",
                    "recommendation": recommendation,
                    "risk_level": risk_level,
                    "confidence": confidence
                }
            )
            
            logger.info(f"✅ Investigation complete:")
            logger.info(f"   Risk Level: {risk_level}")
            logger.info(f"   Confidence: {confidence:.2%}")
            logger.info(f"   Recommendation: {recommendation}")
            logger.info(f"   Safe to Proceed: {safe_to_proceed}")
            logger.info(f"   Latency: {latency_ms}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Investigation failed: {e}")
            
            # Capture failure event
            self._capture_event(
                action_type="tool_call",
                resource=f"investigate:{resource}",
                status="error",
                metadata={"phase": "investigate_error", "error": str(e)}
            )
            raise
    
    def act(
        self,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """
        Execute an action on a resource (with elevated permissions)
        
        This is a simulation. In a real implementation:
        - Restart a service
        - Deploy a fix
        - Update configuration
        - Execute remediation
        """
        logger.info(f"🚀 Executing action '{action}' on resource: {resource}")
        
        start_time = time.time()
        
        # Capture action start event
        self._capture_event(
            action_type="api_call",
            resource=f"{action}:{resource}",
            status="pending",
            metadata={"phase": "action_start", "action": action, "context": context}
        )
        
        try:
            # Simulate action execution
            # In real implementation, this would:
            # - Call external APIs
            # - Update configurations
            # - Restart services
            # - Deploy changes
            time.sleep(2)  # Simulate work
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            result = ActionResult(
                timestamp=datetime.utcnow().isoformat() + "Z",
                resource=resource,
                action=action,
                status="success",
                latency_ms=latency_ms,
                details={
                    "action_type": action,
                    "affected_resources": [resource],
                    "rollback_available": True,
                    "changes_made": [
                        f"Executed {action} on {resource}"
                    ]
                }
            )
            
            # Capture action completion event
            self._capture_event(
                action_type="api_call",
                resource=f"{action}:{resource}",
                status="success",
                latency_ms=latency_ms,
                metadata={
                    "phase": "action_complete",
                    "action": action,
                    "status": "success"
                }
            )
            
            logger.info(f"✅ Action completed successfully:")
            logger.info(f"   Action: {action}")
            logger.info(f"   Resource: {resource}")
            logger.info(f"   Status: {result.status}")
            logger.info(f"   Latency: {latency_ms}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Action failed: {e}")
            
            # Capture failure event
            self._capture_event(
                action_type="api_call",
                resource=f"{action}:{resource}",
                status="error",
                metadata={"phase": "action_error", "action": action, "error": str(e)}
            )
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='GitHub Actions Agent Runner with AIMgentix integration'
    )
    parser.add_argument(
        'command',
        choices=['investigate', 'act'],
        help='Command to execute'
    )
    parser.add_argument(
        '--resource',
        required=True,
        help='Target resource to investigate/act on'
    )
    parser.add_argument(
        '--trace-id',
        help='Trace ID for audit correlation (defaults to env var TRACE_ID)'
    )
    parser.add_argument(
        '--agent-id',
        help='Agent instance ID (defaults to env var AGENT_INSTANCE_ID)'
    )
    parser.add_argument(
        '--action',
        help='Action to execute (required for "act" command)'
    )
    parser.add_argument(
        '--context',
        help='Additional context as JSON string'
    )
    parser.add_argument(
        '--output-file',
        help='Output file for results (JSON)'
    )
    
    args = parser.parse_args()
    
    # Get trace ID
    trace_id = args.trace_id or os.getenv('TRACE_ID')
    if not trace_id:
        trace_id = f"trace-{int(time.time())}"
        logger.warning(f"No trace ID provided, generated: {trace_id}")
    
    # Get agent instance ID
    agent_id = args.agent_id or os.getenv('AGENT_INSTANCE_ID', f"agent-{uuid.uuid4().hex[:8]}")
    
    # Parse context
    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in --context")
            sys.exit(1)
    
    # Initialize agent runner
    runner = AgentRunner(
        trace_id=trace_id,
        agent_instance_id=agent_id
    )
    
    try:
        if args.command == 'investigate':
            result = runner.investigate(args.resource, context)
            output = asdict(result)
            
        elif args.command == 'act':
            if not args.action:
                logger.error("--action is required for 'act' command")
                sys.exit(1)
            result = runner.act(args.resource, args.action, context)
            output = asdict(result)
        
        # Save output
        output_file = args.output_file
        if not output_file:
            if args.command == 'investigate':
                output_file = 'investigation-report.json'
            else:
                output_file = 'action-result.json'
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"📄 Results saved to: {output_file}")
        
        # Print to stdout for GitHub Actions
        print(json.dumps(output, indent=2))
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
