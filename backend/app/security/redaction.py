import re

class SecretRedactor:
    """
    Redacts sensitive information before sending context to AI providers.
    Uses best-effort regexes to find and replace secrets with [REDACTED].
    """
    # Simple regex examples for testing/foundation purposes
    PATTERNS = [
        (re.compile(r'(?i)(api_key|apikey|secret|token|password)[\s]*[=:][\s]*[\'"]?([a-zA-Z0-9_\-\.]{10,})[\'"]?'), r'\1=[REDACTED]'),
        (re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]+'), 'Bearer [REDACTED]'),
        (re.compile(r'mongodb(\+srv)?:\/\/[^\s]+'), 'mongodb://[REDACTED]'),
        (re.compile(r'postgres:\/\/[^\s]+'), 'postgres://[REDACTED]'),
    ]

    @classmethod
    def redact(cls, text: str) -> str:
        if not text:
            return text
            
        redacted_text = text
        for pattern, replacement in cls.PATTERNS:
            redacted_text = pattern.sub(replacement, redacted_text)
            
        return redacted_text
