import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.core.security import supabase_client, User
from app.core.logger import get_logger

logger = get_logger(__name__)

class AIRunAudit(BaseModel):
    organization_id: str
    project_id: str
    migration_id: str
    provider: str
    model: str
    model_version: str
    prompt_version: str
    request_id: str
    operation: str
    input_tokens: int
    output_tokens: int
    usage_accuracy: str = "ESTIMATED"
    latency: float
    estimated_cost: float
    status: str
    error_code: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def log_audit_event(
    action: str, 
    resource_type: str, 
    organization_id: str,
    resource_id: Optional[str] = None, 
    user: Optional[User] = None,
    result: str = "SUCCESS",
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Persists an audit event to the database.
    """
    try:
        payload = {
            "organization_id": organization_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,
            "metadata": metadata or {}
        }
        
        if user:
            payload["user_id"] = user.id

        response = supabase_client.table("audit_logs").insert(payload).execute()
        
        if not response.data:
            logger.error("Failed to insert audit log entry (no data returned)")

    except Exception as e:
        logger.error(f"Failed to persist audit log: {str(e)}")

def log_ai_run(audit: AIRunAudit) -> None:
    """
    Specialized logger for AI runs avoiding logging of prompts or responses.
    """
    try:
        # For phase 3 foundation, we may just log it to the audit_logs table with a specific structure.
        payload = audit.model_dump(mode="json")
        log_audit_event(
            action="AI_RUN",
            resource_type="migration",
            organization_id=audit.organization_id,
            resource_id=audit.migration_id,
            metadata=payload
        )
    except Exception as e:
        logger.error(f"Failed to persist AI run audit: {str(e)}")
