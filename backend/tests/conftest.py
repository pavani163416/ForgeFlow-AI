import pytest
import psycopg2
import os

# Set required environment variables for test collection (Settings validation)
os.environ.setdefault("SUPABASE_URL", "http://localhost:8000")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

@pytest.fixture(scope="session")
def db_connection():
    # Setup test database connection
    # Note: In a real CI environment, migrations would be run via a tool like flyway or golang migrate.
    # Here we simulate running the SQL files directly for the test setup.
    conn_str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forgeflow_test")
    try:
        conn = psycopg2.connect(conn_str)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        yield conn
    except Exception as e:
        if os.getenv("REQUIRE_INTEGRATION_TESTS") == "1":
            pytest.fail(f"Database not available but REQUIRE_INTEGRATION_TESTS is set: {e}")
        pytest.skip(f"Database not available for integration tests: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

@pytest.fixture(scope="session")
def setup_database(db_connection):
    cursor = db_connection.cursor()
    
    # Minimal auth.users mock schema since we don't have full Supabase Auth running in this postgres container
    cursor.execute("CREATE SCHEMA IF NOT EXISTS auth;")
    cursor.execute("CREATE TABLE IF NOT EXISTS auth.users (id UUID PRIMARY KEY);")
    
    # We must mock the auth.uid() function for RLS testing
    cursor.execute('''
        CREATE OR REPLACE FUNCTION auth.uid() RETURNS UUID AS $$
        BEGIN
            RETURN current_setting('request.jwt.claim.sub', true)::UUID;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Read and execute migration files (Moved to CI step)
    # The CI pipeline now explicitly initializes the real PostgreSQL database
    # using the project's actual migration mechanism (psql) before running tests.
    
    cursor.close()
