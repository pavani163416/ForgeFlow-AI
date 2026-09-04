import pytest
import os
import tempfile
import json
from app.orchestration.pipeline import OrchestrationPipeline
from app.core.interfaces import StorageProvider

class MockStorageService(StorageProvider):
    def __init__(self):
        self.artifacts = {}
        
    async def upload(self, bucket: str, path: str, file_content: bytes, organization_id: str) -> str:
        self.artifacts[path] = file_content
        return path
        
    async def download(self, bucket: str, path: str, organization_id: str) -> bytes:
        if path not in self.artifacts:
            raise FileNotFoundError(f"Artifact {path} not found")
        return self.artifacts[path]

    async def delete(self, bucket: str, path: str, organization_id: str) -> bool:
        pass

    async def generate_access_url(self, bucket: str, path: str, organization_id: str, expires_in: int = 3600) -> str:
        pass

@pytest.fixture
def mock_source_dir():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "package.json"), "w") as f:
            f.write('{"dependencies": {"react": "^18.0.0"}}')
        yield d

@pytest.mark.asyncio
async def test_pipeline_execution(mock_source_dir):
    storage = MockStorageService()
    pipeline = OrchestrationPipeline("org_1", "proj_1", "mig_1", storage)
    
    # 1. Run Analysis
    await pipeline.run_analysis_stage(mock_source_dir)
    assert "org_1/proj_1/mig_1/air.json" in storage.artifacts
    
    # 2. Run Security
    await pipeline.run_security_stage(mock_source_dir)
    assert "org_1/proj_1/mig_1/security_findings.json" in storage.artifacts
    
    # 3. Run Planning
    await pipeline.run_planning_stage()
    assert "org_1/proj_1/mig_1/migration_plan.json" in storage.artifacts
    
    plan_data = json.loads(storage.artifacts["org_1/proj_1/mig_1/migration_plan.json"].decode('utf-8'))
    assert plan_data["target_platform"] == "Flutter"
