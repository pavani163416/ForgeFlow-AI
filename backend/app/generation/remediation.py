from typing import List, Optional
from app.generation.workspace import GenerationWorkspace
from app.generation.schema import GenerationSpec
from app.generation.generator import FlutterGenerator
from app.validation.engine import ValidationResult

class RemediationEngine:
    """
    Handles bounded, patch-scoped remediation for validation failures.
    Does not allow full project regeneration.
    """
    MAX_REMEDIATION_ATTEMPTS = 3
    MAX_PATCH_FILES = 5

    def __init__(self, generator: FlutterGenerator):
        self.generator = generator

    def run_remediation(self, workspace: GenerationWorkspace, spec: GenerationSpec, validation_result: ValidationResult, attempt: int) -> bool:
        """
        Takes a validation failure, identifies affected files, and proposes patches.
        Returns True if patches were generated (caller should re-validate).
        Returns False if limits exceeded or patches could not be generated.
        """
        if attempt > self.MAX_REMEDIATION_ATTEMPTS:
            return False
            
        affected_files = self._extract_affected_files(validation_result)
        if len(affected_files) > self.MAX_PATCH_FILES:
            # Too many files affected, abort remediation to prevent sweeping unconstrained changes
            return False
            
        if not affected_files:
            return False
            
        patched = False
        for file_path in affected_files:
            error_context = self._extract_errors_for_file(validation_result, file_path)
            # Request patch from generator
            patched_file = self.generator.generate_patch(file_path, error_context, spec)
            if patched_file:
                workspace.write_file(patched_file)
                patched = True
                
        return patched
        
    def _extract_affected_files(self, validation_result: ValidationResult) -> List[str]:
        # Stub logic to extract file paths from error messages
        files = set()
        if hasattr(validation_result, 'errors'):
            for err in validation_result.errors:
                if ".dart" in err:
                    # simplistic extraction for demonstration
                    parts = err.split()
                    for p in parts:
                        if p.endswith(".dart"):
                            files.add(p)
        return list(files)

    def _extract_errors_for_file(self, validation_result: ValidationResult, file_path: str) -> str:
        # Stub logic to collect error messages related to a specific file
        return "\n".join([err for err in getattr(validation_result, 'errors', []) if file_path in err])
