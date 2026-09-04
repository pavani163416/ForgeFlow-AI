import logging
import json
import contextvars
from datetime import datetime, timezone
from typing import Any, Dict

# Context variables for tracing
request_id_var = contextvars.ContextVar("request_id", default=None)
organization_id_var = contextvars.ContextVar("organization_id", default=None)
migration_id_var = contextvars.ContextVar("migration_id", default=None)

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Inject context if available
        req_id = request_id_var.get()
        if req_id:
            log_obj["request_id"] = req_id

        org_id = organization_id_var.get()
        if org_id:
            log_obj["organization_id"] = org_id

        mig_id = migration_id_var.get()
        if mig_id:
            log_obj["migration_id"] = mig_id

        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Do not log secrets. Sensitive loggers should be configured here if necessary.

def get_logger(name: str):
    return logging.getLogger(name)

def log_lifecycle_event(event_type: str, **kwargs):
    """
    Logs structured JSON lifecycle events for observability.
    Strictly filters out any raw secrets or source code.
    """
    safe_context = {k: v for k, v in kwargs.items() if "secret" not in k.lower() and "key" not in k.lower() and "source" not in k.lower() and "code" not in k.lower()}
    
    log_obj = {
        "event_type": event_type,
        **safe_context
    }
    logger = get_logger("forgeflow_ai.lifecycle")
    logger.info(json.dumps(log_obj))
