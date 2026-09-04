import os
import pytest
import psycopg2
import uuid

# Connection string for test DB
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forgeflow_test")

def is_db_available():
    try:
        conn = psycopg2.connect(DB_URL)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

@pytest.fixture(scope="module")
def rls_db_connection(setup_database):
    if not is_db_available():
        if os.getenv("REQUIRE_INTEGRATION_TESTS") == "1":
            pytest.fail("PostgreSQL unavailable but REQUIRE_INTEGRATION_TESTS is set.")
        pytest.skip("PostgreSQL unavailable. Skipping RLS integration tests.")
    
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False # Keep tests in a transaction that we can rollback
    yield conn
    conn.rollback()
    conn.close()

def test_rls_tenant_isolation(rls_db_connection):
    cursor = rls_db_connection.cursor()
    
    # 1. Create two test organizations
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, %s)", (org_a, "Org A"))
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, %s)", (org_b, "Org B"))
    
    # 2. Create users and memberships
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO auth.users (id) VALUES (%s), (%s)", (user_a, user_b))
    
    cursor.execute("INSERT INTO organization_members (organization_id, user_id, role) VALUES (%s, %s, 'MEMBER')", (org_a, user_a))
    cursor.execute("INSERT INTO organization_members (organization_id, user_id, role) VALUES (%s, %s, 'MEMBER')", (org_b, user_b))
    
    # 3. Insert projects for both orgs (Bypassing RLS as admin for setup)
    proj_a_id = str(uuid.uuid4())
    proj_b_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO projects (id, organization_id, name, framework) VALUES (%s, %s, 'Proj A', 'react')", (proj_a_id, org_a))
    cursor.execute("INSERT INTO projects (id, organization_id, name, framework) VALUES (%s, %s, 'Proj B', 'react')", (proj_b_id, org_b))
    
    # 4. Set session variable to simulate User A being authenticated via JWT sub
    # In Supabase, RLS policies use auth.uid() which reads from request.jwt.claim.sub
    cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, TRUE)", (user_a,))
    # Role must be authenticated for RLS to apply correctly
    cursor.execute("SET ROLE authenticated")
    
    # ==========================
    # VERIFY SELECT ISOLATION
    # ==========================
    cursor.execute("SELECT id FROM projects")
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0][0] == proj_a_id # Only sees Org A's project
    
    # ==========================
    # VERIFY INSERT ISOLATION
    # ==========================
    # User A tries to insert into Org A (Should succeed)
    cursor.execute("INSERT INTO projects (organization_id, name, framework) VALUES (%s, 'Proj A2', 'flutter')", (org_a,))
    
    # User A tries to insert into Org B (Should fail/throw error due to RLS)
    with pytest.raises(psycopg2.errors.InsufficientPrivilege):
        cursor.execute("INSERT INTO projects (organization_id, name, framework) VALUES (%s, 'Malicious Proj B', 'flutter')", (org_b,))
    
    # Reset transaction state after an expected failure
    cursor.execute("ROLLBACK")
    # Must re-apply configs after rollback
    cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, TRUE)", (user_a,))
    cursor.execute("SET ROLE authenticated")
    
    # ==========================
    # VERIFY UPDATE ISOLATION
    # ==========================
    # User A updates Org A project
    cursor.execute("UPDATE projects SET name = 'Updated Proj A' WHERE id = %s", (proj_a_id,))
    
    # User A tries to update Org B project (Zero rows affected, because they can't see it)
    cursor.execute("UPDATE projects SET name = 'Hacked Proj B' WHERE id = %s", (proj_b_id,))
    assert cursor.rowcount == 0
    
    # ==========================
    # VERIFY DELETE ISOLATION
    # ==========================
    # User A tries to delete Org B project (Zero rows affected)
    cursor.execute("DELETE FROM projects WHERE id = %s", (proj_b_id,))
    assert cursor.rowcount == 0
    
    # User A deletes their own project
    cursor.execute("DELETE FROM projects WHERE id = %s", (proj_a_id,))
    assert cursor.rowcount == 1
    
    # Clean up session
    cursor.execute("RESET ROLE")
    cursor.close()

def test_rls_phase4_generation_isolation(rls_db_connection):
    cursor = rls_db_connection.cursor()
    
    # 1. Create two test organizations
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, %s)", (org_a, "Phase 4 Org A"))
    cursor.execute("INSERT INTO organizations (id, name) VALUES (%s, %s)", (org_b, "Phase 4 Org B"))
    
    # 2. Create users and memberships
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO auth.users (id) VALUES (%s), (%s)", (user_a, user_b))
    
    cursor.execute("INSERT INTO organization_members (organization_id, user_id, role) VALUES (%s, %s, 'MEMBER')", (org_a, user_a))
    cursor.execute("INSERT INTO organization_members (organization_id, user_id, role) VALUES (%s, %s, 'MEMBER')", (org_b, user_b))
    
    # 3. Create dummy project and migration job (Admin mode)
    proj_a = str(uuid.uuid4())
    proj_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO projects (id, organization_id, name, framework) VALUES (%s, %s, 'Proj A', 'react')", (proj_a, org_a))
    cursor.execute("INSERT INTO projects (id, organization_id, name, framework) VALUES (%s, %s, 'Proj B', 'react')", (proj_b, org_b))
    
    mig_a = str(uuid.uuid4())
    mig_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO migration_jobs (id, project_id, organization_id) VALUES (%s, %s, %s)", (mig_a, proj_a, org_a))
    cursor.execute("INSERT INTO migration_jobs (id, project_id, organization_id) VALUES (%s, %s, %s)", (mig_b, proj_b, org_b))
    
    # Insert Phase 4 data
    run_a = str(uuid.uuid4())
    run_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO generation_runs (id, migration_job_id, organization_id, status) VALUES (%s, %s, %s, 'GENERATING')", (run_a, mig_a, org_a))
    cursor.execute("INSERT INTO generation_runs (id, migration_job_id, organization_id, status) VALUES (%s, %s, %s, 'GENERATING')", (run_b, mig_b, org_b))
    
    file_a = str(uuid.uuid4())
    file_b = str(uuid.uuid4())
    cursor.execute("INSERT INTO generation_files (id, generation_run_id, organization_id, file_path, checksum) VALUES (%s, %s, %s, 'lib/main.dart', 'chk')", (file_a, run_a, org_a))
    cursor.execute("INSERT INTO generation_files (id, generation_run_id, organization_id, file_path, checksum) VALUES (%s, %s, %s, 'lib/main.dart', 'chk')", (file_b, run_b, org_b))
    
    # 4. Set session variable to User A
    cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, TRUE)", (user_a,))
    cursor.execute("SET ROLE authenticated")
    
    # SELECT ISOLATION: generation_runs
    cursor.execute("SELECT id FROM generation_runs")
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0][0] == run_a
    
    # SELECT ISOLATION: generation_files
    cursor.execute("SELECT id FROM generation_files")
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0][0] == file_a
    
    # INSERT ISOLATION
    # User A tries to insert run into Org B (Should fail)
    with pytest.raises(psycopg2.errors.InsufficientPrivilege):
        cursor.execute("INSERT INTO generation_runs (migration_job_id, organization_id, status) VALUES (%s, %s, 'GENERATING')", (mig_b, org_b))
        
    cursor.execute("ROLLBACK")
    cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, TRUE)", (user_a,))
    cursor.execute("SET ROLE authenticated")
    
    # UPDATE ISOLATION
    cursor.execute("UPDATE generation_runs SET status = 'COMPLETED' WHERE id = %s", (run_b,))
    assert cursor.rowcount == 0  # Cannot see or update Org B's run
    
    # DELETE ISOLATION
    cursor.execute("DELETE FROM generation_runs WHERE id = %s", (run_b,))
    assert cursor.rowcount == 0  # Cannot see or delete Org B's run
    
    cursor.execute("RESET ROLE")
    cursor.close()
