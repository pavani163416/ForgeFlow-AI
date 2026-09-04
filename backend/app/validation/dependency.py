import yaml
from typing import List, Dict, Any, Optional
from app.validation.engine import ValidationResult

from app.validation.interfaces import ValidatorInterface

class DependencyValidator(ValidatorInterface):
    """
    Validates Dart/Flutter dependencies from pubspec.yaml.
    """
    def __init__(self, allowed_packages: Optional[List[str]] = None, blocked_packages: Optional[List[str]] = None):
        self.allowed_packages = allowed_packages or []
        self.blocked_packages = blocked_packages or []

    def validate(self, target: Any) -> ValidationResult:
        if not isinstance(target, dict):
            return ValidationResult(is_valid=True)
            
        pubspec_content = target.get("pubspec.yaml")
        if not pubspec_content:
            return ValidationResult(is_valid=True)
            
        errors = []
        try:
            pubspec = yaml.safe_load(pubspec_content)
        except yaml.YAMLError as e:
            return ValidationResult(is_valid=False, errors=[f"Invalid YAML syntax: {e}"])
            
        if not isinstance(pubspec, dict):
            return ValidationResult(is_valid=False, errors=["pubspec.yaml must contain a top-level mapping"])
            
        dependencies = pubspec.get("dependencies", {})
        dev_dependencies = pubspec.get("dev_dependencies", {})
        
        if not isinstance(dependencies, dict) or not isinstance(dev_dependencies, dict):
            return ValidationResult(is_valid=False, errors=["dependencies and dev_dependencies must be mappings"])

        all_deps = {**dependencies, **dev_dependencies}
        
        for dep_name, dep_source in all_deps.items():
            # 1. Allowed / Blocked Check
            if self.blocked_packages and dep_name in self.blocked_packages:
                errors.append(f"Package '{dep_name}' is explicitly blocked.")
            if self.allowed_packages and dep_name not in self.allowed_packages:
                errors.append(f"Package '{dep_name}' is not in the allowed list.")
                
            # 2. Source Policy Check
            if isinstance(dep_source, dict):
                if 'path' in dep_source:
                    errors.append(f"Package '{dep_name}' uses blocked local path source: {dep_source['path']}")
                if 'git' in dep_source:
                    errors.append(f"Package '{dep_name}' uses blocked git source: {dep_source['git']}")

        # 3. Vulnerability Intelligence 
        # (As requested: do not invent vulnerability intelligence, use UNKNOWN if unavailable)
        vulnerability_status = "UNKNOWN"
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
            
        return ValidationResult(is_valid=True, errors=[])
