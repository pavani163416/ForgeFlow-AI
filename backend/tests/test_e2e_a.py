import os
import pytest
import zipfile
from app.generation.orchestrator import GenerationOrchestrator
from app.generation.generator import FlutterGenerator
from app.generation.workspace import GenerationWorkspace
from app.generation.schema import GenerationSpec, GenerationTarget
from app.orchestration.finalizer import GenerationFinalizer
from app.validation.engine import ValidationResult, ValidationEngine
from app.generation.review import ReviewResult

class DummyAIProvider:
    def generate(self, prompt: str) -> str:
        if "pubspec" in prompt.lower():
            return "name: test_app\ndescription: app\ndependencies:\n  flutter:\n    sdk: flutter\n"
        return "void main() { print('hello'); }"

def test_e2e_a_real_pipeline(tmp_path):
    # Setup
    workspace_dir = tmp_path / "workspace"
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    
    ws = GenerationWorkspace(str(workspace_dir))
    generator = FlutterGenerator(DummyAIProvider())
    orchestrator = GenerationOrchestrator(generator, ws)
    
    spec = GenerationSpec(
        source_project_id="test",
        source_version_id="v1",
        air_version="1.0",
        plan_version="1.0",
        target=GenerationTarget(flutter_version="3.10.0", dart_version="3.0.0"),
        security_constraints=["no eval"]
    )
    
    run_id = "test_run_123"
    
    # 1. Generation
    files = orchestrator.run_generation(spec, run_id)
    assert len(files) > 0
    assert (workspace_dir / "lib" / "models" / "main.dart").exists()
    
    # 2. Validation (Use real validators)
    from app.validation.engine import FlutterStructureValidator
    from app.validation.dependency import DependencyValidator
    engine = ValidationEngine([FlutterStructureValidator(), DependencyValidator()])
    
    # We must load the workspace files as a dictionary for the ValidationEngine
    workspace_content = {}
    for f in ws.list_files():
        workspace_content[f] = ws.read_file(f)
        
    val_result = engine.run_pipeline(workspace_content)
    
    # Ensure our fake AI produced valid code (it produces "void main() { print('hello'); }")
    # which should pass the minimal Deterministic validation
    assert val_result.is_valid is True
    
    rev_result = ReviewResult(status="ACCEPTED", confidence=0.99)
    sandbox_result = {"status": "SUCCESS"}
    
    # 3. Finalization
    finalizer = GenerationFinalizer(str(archive_dir))
    artifact_path = finalizer.finalize_generation(
        run_id, ws, val_result, rev_result, sandbox_result
    )
    
    # Verify ZIP artifact
    assert os.path.exists(artifact_path)
    assert artifact_path.endswith("test_run_123.zip")
    
    # Verify zip contents
    with zipfile.ZipFile(artifact_path, 'r') as zf:
        namelist = zf.namelist()
        assert "generation_manifest.json" in namelist
        # Depending on path structure in zip, ensure no absolute paths
        for name in namelist:
            assert not name.startswith("/")
            assert not name.startswith("..")
            
    # Verify immutability by trying to finalize again with same run_id
    from app.orchestration.finalizer import FinalizerError
    with pytest.raises(FinalizerError, match="Artifact immutability violation"):
        finalizer.finalize_generation(run_id, ws, val_result, rev_result, sandbox_result)
