import os
import sys
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
            return "name: test_app\ndescription: app\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter:\n    sdk: flutter\ndev_dependencies:\n  flutter_test:\n    sdk: flutter\n"
        return "void main() { print('hello'); }"

def main():
    workspace_dir = "test_workspace"
    archive_dir = "test_archives"
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)
    
    ws = GenerationWorkspace(workspace_dir)
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
    files = orchestrator.run_generation(spec, run_id)
    
    from app.validation.engine import FlutterStructureValidator
    from app.validation.dependency import DependencyValidator
    engine = ValidationEngine([FlutterStructureValidator(), DependencyValidator()])
    
    workspace_content = {}
    for f in ws.list_files():
        workspace_content[f] = ws.read_file(f)
        
    val_result = engine.run_pipeline(workspace_content)
    rev_result = ReviewResult(status="ACCEPTED", confidence=0.99)
    sandbox_result = {"status": "SUCCESS"}
    
    finalizer = GenerationFinalizer(archive_dir)
    artifact_path = finalizer.finalize_generation(
        run_id, ws, val_result, rev_result, sandbox_result
    )
    print(f"ZIP path: {artifact_path}")

if __name__ == '__main__':
    main()
