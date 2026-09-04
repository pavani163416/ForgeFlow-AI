from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SecurityFinding(BaseModel):
    finding_id: str
    organization_id: str
    project_id: str
    migration_id: str
    source_version: str
    scanner: str
    rule_id: str
    category: str
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW, INFO")
    title: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    redacted_evidence: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: str = Field(..., description="HIGH, MEDIUM, LOW")
    status: str = "OPEN"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
