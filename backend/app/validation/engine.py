import json
from typing import Any, List, Dict
from pydantic import ValidationError
from .interfaces import ValidatorInterface, ValidationResult

class SchemaValidator(ValidatorInterface):
    """
    Validates that AI output strictly conforms to the expected Pydantic schema.
    """
    def __init__(self, pydantic_model):
        self.pydantic_model = pydantic_model

    def validate(self, target: Any) -> ValidationResult:
        try:
            if isinstance(target, str):
                self.pydantic_model.model_validate_json(target)
            else:
                self.pydantic_model.model_validate(target)
            return ValidationResult(is_valid=True)
        except ValidationError as e:
            return ValidationResult(is_valid=False, errors=[str(e)])
        except json.JSONDecodeError as e:
            return ValidationResult(is_valid=False, errors=[f"Invalid JSON: {str(e)}"])

class PolicyValidator(ValidatorInterface):
    """
    Validates that the AI output does not violate fundamental system policies.
    """
    def validate(self, target: Any) -> ValidationResult:
        if isinstance(target, str):
            if "sk_live_" in target or ("API_KEY" in target.upper() and "[REDACTED]" not in target.upper()):
                return ValidationResult(is_valid=False, errors=["Policy Violation: Raw server secrets or API keys detected in target output."])
            if "service_role" in target.lower():
                return ValidationResult(is_valid=False, errors=["Policy Violation: Supabase service-role credentials detected."])
        return ValidationResult(is_valid=True)

class SecurityValidator(ValidatorInterface):
    """
    Inspects security findings associated with an artifact and blocks if CRITICAL or HIGH.
    """
    def __init__(self, findings: List[Dict], override_approved: bool = False):
        self.findings = findings
        self.override_approved = override_approved

    def validate(self, target: Any) -> ValidationResult:
        errors = []
        for finding in self.findings:
            sev = finding.get("severity", "INFO")
            if sev in ["CRITICAL", "HIGH"]:
                if not self.override_approved:
                    errors.append(f"Security Gate Blocked: {sev} finding '{finding.get('title')}' is unresolved.")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        return ValidationResult(is_valid=True)

class FileValidator(ValidatorInterface):
    """
    Validates target artifacts for path traversal, extensions, and limits.
    """
    def __init__(self, max_files: int = 1000):
        self.max_files = max_files

    def validate(self, target: Any) -> ValidationResult:
        # Assuming target is a dictionary mapping filepath -> content
        if not isinstance(target, dict):
            return ValidationResult(is_valid=True)
            
        if len(target) > self.max_files:
            return ValidationResult(is_valid=False, errors=[f"File count {len(target)} exceeds maximum allowed {self.max_files}."])
            
        for path in target.keys():
            if ".." in path or path.startswith("/") or path.startswith("\\") or ":" in path:
                return ValidationResult(is_valid=False, errors=[f"Path traversal or absolute path detected: {path}"])
            if path.endswith(".exe") or path.endswith(".sh"):
                return ValidationResult(is_valid=False, errors=[f"Forbidden file extension detected: {path}"])
        return ValidationResult(is_valid=True)

class DependencyValidator(ValidatorInterface):
    """
    Validates dependency structures by parsing pubspec.yaml.
    """
    def __init__(self, allowed_deps: List[str] = None, blocked_deps: List[str] = None):
        self.allowed_deps = allowed_deps or []
        self.blocked_deps = blocked_deps or ["eval", "exec", "dart:mirrors"]

    def validate(self, target: Any) -> ValidationResult:
        import yaml
        if not isinstance(target, dict):
            return ValidationResult(is_valid=True)
            
        pubspec_content = target.get("pubspec.yaml")
        if not pubspec_content:
            return ValidationResult(is_valid=True) # Let structure validator catch it
            
        try:
            parsed = yaml.safe_load(pubspec_content)
            if not isinstance(parsed, dict):
                return ValidationResult(is_valid=False, errors=["pubspec.yaml is not a valid YAML dictionary"])
                
            deps = parsed.get("dependencies", {})
            dev_deps = parsed.get("dev_dependencies", {})
            
            all_deps = list(deps.keys()) + list(dev_deps.keys())
            
            for dep in all_deps:
                for blocked in self.blocked_deps:
                    if blocked.lower() in str(dep).lower():
                        return ValidationResult(is_valid=False, errors=[f"Blocked dependency detected: {dep}"])
                
                # Vulnerability intelligence stub
                if dep == "known_vulnerable_pkg":
                    return ValidationResult(is_valid=False, errors=["Vulnerability UNKNOWN for pkg."])
                    
        except yaml.YAMLError as e:
            return ValidationResult(is_valid=False, errors=[f"Invalid YAML in pubspec.yaml: {str(e)}"])
            
        return ValidationResult(is_valid=True)

class APIContractValidator(ValidatorInterface):
    """
    Compares generated API usage against AIR to prevent hallucinated endpoints.
    """
    def __init__(self, air_endpoints: List[str]):
        self.air_endpoints = [e.lower() for e in air_endpoints]

    def validate(self, target: Any) -> ValidationResult:
        # Simple baseline: if target is a dict containing requested_endpoints
        if isinstance(target, dict) and "requested_endpoints" in target:
            for endpoint in target["requested_endpoints"]:
                if endpoint.lower() not in self.air_endpoints:
                    return ValidationResult(is_valid=False, errors=[f"API Contract Violation: Unknown endpoint {endpoint}."])
        return ValidationResult(is_valid=True)

class FlutterStructureValidator(ValidatorInterface):
    """
    Validates the structure of the generated Flutter project.
    """
    def validate(self, target: Any) -> ValidationResult:
        if isinstance(target, dict):
            if "pubspec.yaml" not in target:
                return ValidationResult(is_valid=False, errors=["Missing required file: pubspec.yaml"])
            if "lib/main.dart" not in target:
                return ValidationResult(is_valid=False, errors=["Missing required file: lib/main.dart"])
        return ValidationResult(is_valid=True)

class ValidationEngine:
    """
    Runs untrusted AI output through a strict pipeline of validators.
    Pipeline: Schema -> Semantic -> Security -> Policy
    """
    def __init__(self, validators: List[ValidatorInterface]):
        self.validators = validators

    def run_pipeline(self, target: Any) -> ValidationResult:
        all_errors = []
        for validator in self.validators:
            result = validator.validate(target)
            if not result.is_valid:
                all_errors.extend(result.errors)
                # Fail fast on the first validator that fails (e.g. if schema fails, 
                # semantic validation will definitely fail).
                return ValidationResult(is_valid=False, errors=all_errors)
                
        return ValidationResult(is_valid=True)
