from typing import List, Dict, Any
from app.validation.interfaces import ValidatorInterface, ValidationResult
from app.sandbox.provider import SandboxProvider

class FlutterExecutionValidator(ValidatorInterface):
    """
    Validates Flutter project using real `flutter analyze` and `flutter test`
    inside the secure sandbox.
    """
    def __init__(self, sandbox: SandboxProvider, workspace_dir: str):
        self.sandbox = sandbox
        self.workspace_dir = workspace_dir

    def validate(self, target: Any) -> ValidationResult:
        if not self.sandbox.is_available():
            # If sandbox is not available, we SKIP (do not return a false success)
            # In actual orchestration, skipping due to missing sandbox will be caught if REQUIRE_INTEGRATION_TESTS=1
            return ValidationResult(is_valid=False, errors=["Sandbox execution = NOT AVAILABLE"])
            
        errors = []
        
        # 1. pub get
        pub_get = self.sandbox.execute(self.workspace_dir, "flutter pub get")
        if pub_get.status != "SUCCESS" or pub_get.exit_code != 0:
            errors.append(f"flutter pub get failed: {pub_get.stderr}")
            return ValidationResult(is_valid=False, errors=errors)
            
        # 2. analyze
        analyze = self.sandbox.execute(self.workspace_dir, "flutter analyze")
        if analyze.status != "SUCCESS" or analyze.exit_code != 0:
            errors.append(f"flutter analyze failed: {analyze.stdout}")
            
        # 3. test
        test_run = self.sandbox.execute(self.workspace_dir, "flutter test")
        if test_run.status != "SUCCESS" or test_run.exit_code != 0:
            errors.append(f"flutter test failed: {test_run.stdout}")
            
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
            
        return ValidationResult(is_valid=True)
