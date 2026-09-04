from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

class ValidationResult:
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []

class ValidatorInterface(ABC):
    @abstractmethod
    def validate(self, target: Any) -> ValidationResult:
        pass
