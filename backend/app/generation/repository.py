import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Dict, Any, Optional

class GenerationRepository:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=DictCursor)

    def set_auth_context(self, cursor, user_id: str):
        """Sets the RLS context for the current transaction."""
        cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, TRUE)", (user_id,))
        cursor.execute("SET ROLE authenticated")

    def create_generation_run(self, migration_job_id: str, organization_id: str, spec_version: str, user_id: str, generation_stage: str = 'initial', input_identity: str = 'unknown') -> str:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                self.set_auth_context(cur, user_id)
                # Atomic INSERT... ON CONFLICT DO NOTHING to ensure race-safe idempotency
                cur.execute(
                    """
                    INSERT INTO generation_runs 
                    (migration_job_id, organization_id, status, generation_spec_version, generation_stage, input_identity) 
                    VALUES (%s, %s, 'PLANNING', %s, %s, %s) 
                    ON CONFLICT (organization_id, migration_job_id, generation_stage, generation_spec_version, input_identity) DO NOTHING
                    RETURNING id
                    """,
                    (migration_job_id, organization_id, spec_version, generation_stage, input_identity)
                )
                row = cur.fetchone()
                
                if row:
                    run_id = row['id']
                else:
                    # If conflict occurred, retrieve the existing completed/generating run
                    cur.execute(
                        """
                        SELECT id FROM generation_runs
                        WHERE migration_job_id = %s 
                          AND organization_id = %s
                          AND generation_stage = %s
                          AND generation_spec_version = %s
                          AND input_identity = %s
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (migration_job_id, organization_id, generation_stage, spec_version, input_identity)
                    )
                    existing_row = cur.fetchone()
                    run_id = existing_row['id'] if existing_row else None
                    
                conn.commit()
                return run_id

    def atomic_update_generation_status(self, run_id: str, expected_current_status: str, new_status: str, user_id: str) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                self.set_auth_context(cur, user_id)
                # Atomic update enforcing expected current status
                if new_status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                    cur.execute(
                        "UPDATE generation_runs SET status = %s, completed_at = NOW() WHERE id = %s AND status = %s RETURNING id",
                        (new_status, run_id, expected_current_status)
                    )
                else:
                    cur.execute(
                        "UPDATE generation_runs SET status = %s WHERE id = %s AND status = %s RETURNING id",
                        (new_status, run_id, expected_current_status)
                    )
                row = cur.fetchone()
                conn.commit()
                return row is not None



    def record_generated_files(self, run_id: str, organization_id: str, files: List[Dict[str, Any]], user_id: str):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                self.set_auth_context(cur, user_id)
                for f in files:
                    cur.execute(
                        """
                        INSERT INTO generation_files 
                        (generation_run_id, organization_id, file_path, checksum, language, purpose, generation_stage, validation_status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (run_id, organization_id, f['path'], f['checksum'], f.get('language', 'dart'), 
                         f.get('purpose', ''), f.get('generation_stage', ''), f.get('validation_status', 'PENDING'))
                    )
                conn.commit()

    def check_idempotency(self, organization_id: str, migration_job_id: str, generation_stage: str, spec_version: str, input_identity: str, user_id: str) -> Optional[str]:
        """
        Checks if a logically equivalent generation run has already successfully COMPLETED.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                self.set_auth_context(cur, user_id)
                cur.execute(
                    """
                    SELECT id FROM generation_runs
                    WHERE organization_id = %s 
                      AND migration_job_id = %s 
                      AND generation_stage = %s 
                      AND generation_spec_version = %s 
                      AND input_identity = %s 
                      AND status = 'COMPLETED'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (organization_id, migration_job_id, generation_stage, spec_version, input_identity)
                )
                row = cur.fetchone()
                return row['id'] if row else None

    def record_validation_run(self, run_id: str, organization_id: str, validator_name: str, status: str, findings: str, user_id: str):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                self.set_auth_context(cur, user_id)
                cur.execute(
                    """
                    INSERT INTO validation_runs 
                    (generation_run_id, organization_id, validator_name, status, findings) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (run_id, organization_id, validator_name, status, findings)
                )
                conn.commit()
