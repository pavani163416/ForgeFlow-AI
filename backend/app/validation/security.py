from typing import Any, Dict
from app.validation.interfaces import ValidatorInterface, ValidationResult
from app.security.redaction import SecretRedactor

class SecretLeakValidator(ValidatorInterface):
    """
    Scans generated output for secret leakage using the same patterns 
    that the SecretRedactor uses to redact input.
    """
    def validate(self, target: Any) -> ValidationResult:
        # Assuming target is a dictionary mapping filepath -> content
        if not isinstance(target, dict):
            return ValidationResult(is_valid=True)
            
        errors = []
        for path, content in target.items():
            for pattern, _ in SecretRedactor.PATTERNS:
                if pattern.search(content):
                    errors.append(f"Secret leakage detected in generated file: {path}")
                    break
                    
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        return ValidationResult(is_valid=True)
