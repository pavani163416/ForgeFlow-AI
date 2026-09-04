import os
import pytest
import psycopg2
import uuid
from datetime import datetime, timezone, timedelta
from app.worker import acquire_lease, release_lease, process_migration_job
from app.core.state_machine import MigrationState

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forgeflow_test")

def is_db_available():
    try:
        conn = psycopg2.connect(DB_URL)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

@pytest.fixture(scope="module")
def worker_db_connection(setup_database):
    if not is_db_available():
        if os.getenv("REQUIRE_INTEGRATION_TESTS") == "1":
            pytest.fail("PostgreSQL unavailable but REQUIRE_INTEGRATION_TESTS is set.")
        pytest.skip("PostgreSQL unavailable. Skipping Worker integration tests.")
    
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    yield conn
    conn.close()

def create_mock_job(cursor, org_id, status=MigrationState.QUEUED.value, expires_at=None):
    job_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO migration_jobs (id, organization_id, status, lease_expires_at) VALUES (%s, %s, %s, %s)",
        (job_id, org_id, status, expires_at)
    )
    return job_id

def test_atomic_lease_claim(worker_db_connection):
    cursor = worker_db_connection.cursor()
    org_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, 'Test Org Worker')", (org_id,))
    
    job_id = create_mock_job(cursor, org_id)
    
    # 1. Worker A attempts to claim
    worker_a_success = acquire_lease(job_id, "worker-A", 300)
    assert worker_a_success is True
    
    # Verify DB state
    cursor.execute("SELECT worker_id, status FROM migration_jobs WHERE id = %s", (job_id,))
    res = cursor.fetchone()
    assert res[0] == "worker-A"
    assert res[1] == MigrationState.ANALYZING.value
    
    # 2. Worker B attempts to claim same job concurrently
    worker_b_success = acquire_lease(job_id, "worker-B", 300)
    assert worker_b_success is False # Must not double claim
    
    # DB state should remain Worker A
    cursor.execute("SELECT worker_id FROM migration_jobs WHERE id = %s", (job_id,))
    assert cursor.fetchone()[0] == "worker-A"

def test_lease_recovery(worker_db_connection):
    """
    Test that a job can be reclaimed if the lease has expired (simulating a crash).
    """
    cursor = worker_db_connection.cursor()
    org_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, 'Test Org Worker 2')", (org_id,))
    
    # Create a job that is ANALYZING but its lease expired 1 hour ago
    expired_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    job_id = create_mock_job(cursor, org_id, status=MigrationState.ANALYZING.value, expires_at=expired_time)
    
    # Manually set the worker to a "crashed" worker
    cursor.execute("UPDATE migration_jobs SET worker_id = 'crashed-worker' WHERE id = %s", (job_id,))
    
    # Worker B attempts to claim the expired job
    worker_b_success = acquire_lease(job_id, "worker-B", 300)
    assert worker_b_success is True
    
    # Verify Worker B stole the lease
    cursor.execute("SELECT worker_id FROM migration_jobs WHERE id = %s", (job_id,))
    assert cursor.fetchone()[0] == "worker-B"

def test_true_idempotency_duplicate_execution(worker_db_connection):
    """
    Test that if process_migration_job runs twice on the same job logically, 
    the second run aborts without duplicate business effects.
    """
    cursor = worker_db_connection.cursor()
    org_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, 'Test Org Idempotency')", (org_id,))
    
    job_id = create_mock_job(cursor, org_id)
    
    # Simulate Worker A running the task
    # We patch validate_transition to avoid needing full app state setup
    import app.worker
    from unittest.mock import patch
    
    # Real DB claim succeeds, the job goes to COMPLETED
    process_migration_job(job_id, org_id)
    
    # Verify it completed
    cursor.execute("SELECT status FROM migration_jobs WHERE id = %s", (job_id,))
    assert cursor.fetchone()[0] == MigrationState.COMPLETED.value
    
    # Simulate Celery redelivering the same task (acks_late, timeout, etc.)
    with patch("app.worker.validate_transition") as mock_validate:
        # Worker B tries to process
        process_migration_job(job_id, org_id)
        
        # Should abort early, validate_transition shouldn't even be called
        mock_validate.assert_not_called()
    
    # Status should still be COMPLETED, not FAILED
    cursor.execute("SELECT status FROM migration_jobs WHERE id = %s", (job_id,))
    assert cursor.fetchone()[0] == MigrationState.COMPLETED.value
