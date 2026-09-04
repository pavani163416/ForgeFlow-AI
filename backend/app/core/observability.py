import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger("observability")

class ObservabilityEvent:
    def __init__(self, request_id: str, organization_id: str, project_id: str, migration_id: str):
        self.request_id = request_id
        self.organization_id = organization_id
        self.project_id = project_id
        self.migration_id = migration_id

    def emit(self, event_type: str, stage: Optional[str] = None, status: str = "IN_PROGRESS", duration_ms: Optional[int] = None, extra: Optional[Dict[str, Any]] = None):
        """
        Emits a structured JSON lifecycle event.
        NEVER pass secrets, passwords, or raw source code into extra.
        """
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "request_id": self.request_id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "migration_id": self.migration_id,
            "status": status,
        }
        if stage:
            payload["stage"] = stage
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if extra:
            payload.update(extra)
            
        logger.info(json.dumps(payload))
