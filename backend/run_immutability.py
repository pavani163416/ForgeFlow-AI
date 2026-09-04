import os
import hashlib
import time
from app.generation.orchestrator import GenerationOrchestrator
from app.generation.generator import FlutterGenerator
from app.generation.workspace import GenerationWorkspace
from app.generation.schema import GenerationSpec, GenerationTarget
from app.orchestration.finalizer import GenerationFinalizer, FinalizerError
from app.validation.engine import ValidationResult, ValidationEngine
from app.generation.review import ReviewResult
from app.validation.engine import FlutterStructureValidator
from app.validation.dependency import DependencyValidator

class DummyAIProvider:
    def generate(self, prompt: str) -> str:
        return "name: test_app\ndescription: app\ndependencies:\n  flutter:\n    sdk: flutter\n"

def get_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main():
    workspace_dir = "test_workspace_immutability"
    archive_dir = "test_archives_immutability"
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
    
    run_id_v1 = "run_v1"
    
    # 1. Generate V1
    orchestrator.run_generation(spec, run_id_v1)
    
    engine = ValidationEngine([FlutterStructureValidator(), DependencyValidator()])
    workspace_content = {f: ws.read_file(f) for f in ws.list_files()}
    val_result = engine.run_pipeline(workspace_content)
    rev_result = ReviewResult(status="ACCEPTED", confidence=0.99)
    sandbox_result = {"status": "SUCCESS"}
    
    finalizer = GenerationFinalizer(archive_dir)
    
    artifact_v1 = finalizer.finalize_generation(run_id_v1, ws, val_result, rev_result, sandbox_result)
    print(f"V1 Artifact created at: {artifact_v1}")
    
    # 2. Record V1 SHA-256
    hash_v1_initial = get_sha256(artifact_v1)
    print(f"V1 Initial SHA-256: {hash_v1_initial}")
    
    # 3. Attempt to overwrite V1
    print("Attempting to overwrite V1...")
    try:
        finalizer.finalize_generation(run_id_v1, ws, val_result, rev_result, sandbox_result)
        print("FAIL: Overwrite succeeded?!")
    except FinalizerError as e:
        # 4. Confirm overwrite is rejected
        print(f"SUCCESS: Overwrite rejected -> {e}")
        
    # 5. Perform remediation/generate V2
    run_id_v2 = "run_v2"
    orchestrator.run_generation(spec, run_id_v2)
    workspace_content_v2 = {f: ws.read_file(f) for f in ws.list_files()}
    val_result_v2 = engine.run_pipeline(workspace_content_v2)
    artifact_v2 = finalizer.finalize_generation(run_id_v2, ws, val_result_v2, rev_result, sandbox_result)
    
    # 6. Confirm V2 is a distinct artifact/version
    print(f"V2 Artifact created at: {artifact_v2}")
    if artifact_v1 != artifact_v2:
        print("SUCCESS: V2 is a distinct artifact")
    else:
        print("FAIL: V2 artifact path is same as V1")
        
    # 7. Recalculate V1 SHA-256
    hash_v1_final = get_sha256(artifact_v1)
    print(f"V1 Final SHA-256: {hash_v1_final}")
    
    # 8. Confirm V1 is byte-for-byte unchanged
    if hash_v1_initial == hash_v1_final:
        print("SUCCESS: V1 is byte-for-byte unchanged")
    else:
        print("FAIL: V1 was mutated!")

if __name__ == '__main__':
    main()
