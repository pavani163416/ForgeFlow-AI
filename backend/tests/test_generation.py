import pytest
import os
from pathlib import Path
from app.generation.workspace import GenerationWorkspace, WorkspaceError
from app.generation.schema import GeneratedFile

def test_workspace_path_traversal(tmp_path):
    ws = GenerationWorkspace(str(tmp_path))
    file = GeneratedFile(
        path="../outside.dart",
        content="void main() {}",
        purpose="malicious",
        generation_stage="test",
        generation_run_id="test",
        checksum="chk"
    )
    with pytest.raises(WorkspaceError, match="Path traversal detected"):
        ws.write_file(file)

def test_workspace_forbidden_extension(tmp_path):
    ws = GenerationWorkspace(str(tmp_path))
    file = GeneratedFile(
        path="script.sh",
        content="echo hack",
        purpose="malicious",
        generation_stage="test",
        generation_run_id="test",
        checksum="chk"
    )
    with pytest.raises(WorkspaceError, match="Forbidden file extension"):
        ws.write_file(file)

def test_workspace_write_and_read(tmp_path):
    ws = GenerationWorkspace(str(tmp_path))
    file = GeneratedFile(
        path="lib/main.dart",
        content="void main() {}",
        purpose="app",
        generation_stage="test",
        generation_run_id="test",
        checksum="chk"
    )
    ws.write_file(file)
    
    read_content = ws.read_file("lib/main.dart")
    assert read_content == "void main() {}"
    
    files = ws.list_files()
    assert "lib/main.dart" in files

import concurrent.futures
from app.generation.repository import GenerationRepository
import uuid

def test_generation_idempotency_concurrency(db_connection):
    cursor = db_connection.cursor()
    org_id = str(uuid.uuid4())
    migration_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, 'Test Org Idempotency')", (org_id,))
    cursor.execute("INSERT INTO migration_jobs (id, organization_id, status) VALUES (%s, %s, 'GENERATING')", (migration_id, org_id))
    db_connection.commit()

    repo = GenerationRepository(os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forgeflow_test"))

    def attempt_create():
        return repo.create_generation_run(
            migration_job_id=migration_id,
            organization_id=org_id,
            spec_version="1.0",
            user_id="user-id",
            generation_stage="initial",
            input_identity="input123"
        )

    # Run 5 concurrent attempts
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: attempt_create(), range(5)))

    # Ensure all returned run_ids are identical
    run_ids = set(results)
    assert len(run_ids) == 1
    assert list(run_ids)[0] is not None

    # Check DB directly to ensure exactly 1 row exists
    cursor.execute("SELECT COUNT(*) FROM generation_runs WHERE migration_job_id = %s", (migration_id,))
    count = cursor.fetchone()[0]
    assert count == 1
