import pytest
from app.security.engine import SecurityEngine

def test_security_engine_scan():
    engine = SecurityEngine("org_1", "proj_1", "mig_1", "v1")
    findings = engine.scan("/fake/dir")
    
    assert len(findings) >= 1
    finding = findings[0]
    
    assert finding.severity == "CRITICAL"
    assert finding.redacted_evidence is not None
    assert "[REDACTED]" in finding.redacted_evidence
    assert finding.confidence == "HIGH"
