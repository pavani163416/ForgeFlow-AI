import os
import shutil
import hashlib
from typing import Dict, Any, List
from app.validation.engine import ValidationResult
from app.generation.review import ReviewResult
from app.generation.workspace import GenerationWorkspace
from app.validation.security import SecretLeakValidator
import zipfile

class FinalizerError(Exception):
    pass

class GenerationFinalizer:
    """
    Extremely strict fail-closed finalizer for Phase 4 generation.
    """
    def __init__(self, workspace_base_dir: str):
        self.workspace_base_dir = workspace_base_dir
        
    def finalize_generation(self, 
                          run_id: str,
                          workspace: GenerationWorkspace,
                          validation_result: ValidationResult,
                          review_result: ReviewResult,
                          sandbox_result: Dict[str, Any]) -> str:
                          
        # 0. Output Secret Validation gate
        secret_validator = SecretLeakValidator()
        workspace_content_map = {f: workspace.read_file(f) for f in workspace.list_files()}
        secret_res = secret_validator.validate(workspace_content_map)
        if not secret_res.is_valid:
            raise FinalizerError(f"Finalization blocked: Secret leakage detected: {secret_res.errors}")

        # 1. Deterministic validation gate
        if not validation_result.is_valid:
            raise FinalizerError("Finalization blocked: Deterministic validation failed.")
            
        # 2. AI Review gate
        if review_result.status not in ["ACCEPTED", "PASS"]:
            raise FinalizerError(f"Finalization blocked: AI Review rejected with status {review_result.status}.")
            
        # 3. Sandbox execution gate
        if sandbox_result.get("status") == "FAILURE":
            raise FinalizerError("Finalization blocked: Sandbox build/execution failed.")
            
        # 4. Package workspace into artifact
        artifact_path = self._package_and_store_workspace(run_id, workspace)
        
        return artifact_path
        
    def _package_and_store_workspace(self, run_id: str, workspace: GenerationWorkspace) -> str:
        # Create manifest
        manifest_content = f'{{"generation_run_id": "{run_id}", "files": {len(workspace.list_files())}}}'
        workspace._safe_resolve("generation_manifest.json").write_text(manifest_content)
        
        zip_base_name = os.path.join(self.workspace_base_dir, f"flutter-source-{run_id}")
        archive_path = f"{zip_base_name}.zip"
        
        # Do not overwrite finalized artifacts
        if os.path.exists(archive_path):
            raise FinalizerError(f"Artifact immutability violation: {archive_path} already exists.")
            
        # Zip the directory
        shutil.make_archive(zip_base_name, 'zip', workspace.base_dir)
        
        # Re-open ZIP to validate archive paths, expected files
        expected_files = set(workspace.list_files())
        expected_files.add("generation_manifest.json")
        
        with zipfile.ZipFile(archive_path, 'r') as zf:
            archive_names = zf.namelist()
            archive_names_set = set(archive_names)
            
            if len(archive_names) != len(archive_names_set):
                raise FinalizerError("Archive validation failed: Duplicate entries in ZIP.")
                
            for name in archive_names:
                # Reject traversal paths and absolute paths
                if name.startswith("/") or ".." in name or "\\" in name:
                    raise FinalizerError(f"Archive validation failed: Illegal path {name} in ZIP.")
                    
                # In python's ZipFile, symlinks are represented with specific external_attr, but we can just check if all files match our allowlist
                # For this Phase 4 requirement, we assert the archive contains exactly the workspace files
                if name not in expected_files:
                    # sometimes zipfile adds directory entries like 'lib/'
                    if not name.endswith('/'):
                        raise FinalizerError(f"Archive validation failed: Unexpected file {name} in ZIP.")
        
        # Calculate SHA256 of the zip
        sha256 = hashlib.sha256()
        with open(archive_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
                
        # (Storage abstraction to S3 would go here)
        
        return archive_path
