import pytest
from app.security.redaction import SecretRedactor

def test_secret_redaction():
    source = "const API_KEY = 'sk_live_1234567890abcdef';"
    redacted = SecretRedactor.redact(source)
    assert "sk_live" not in redacted
    assert "[REDACTED]" in redacted
    
    source_bearer = "Authorization: Bearer eYjhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    redacted_bearer = SecretRedactor.redact(source_bearer)
    assert "eYjhb" not in redacted_bearer
    assert "Bearer [REDACTED]" in redacted_bearer
