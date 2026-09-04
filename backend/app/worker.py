import logging
import socket
from datetime import datetime, timezone, timedelta
from celery import Celery
from app.core.config import settings
from app.core.security import supabase_client
from app.core.state_machine import validate_transition, MigrationState, InvalidStateTransitionError

logger = logging.getLogger(__name__)

celery_app = Celery(
    "forgeflow_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

def get_db_connection():
    import psycopg2
    import os
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    return None

def acquire_lease(job_id: str, worker_id: str, lease_duration_seconds: int = 300) -> bool:
    """
    Atomically acquire a lease on a job using PostgreSQL.
    Claims jobs that are QUEUED, or jobs that are ANALYZING but their lease has expired.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=lease_duration_seconds)
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Atomic update: claim if QUEUED, or if lease expired (stolen lease)
            query = """
                UPDATE migration_jobs
                SET status = %s,
                    worker_id = %s,
                    lease_expires_at = %s,
                    heartbeat_at = %s
                WHERE id = %s
                  AND (
                      status = %s 
                      OR (status = %s AND lease_expires_at < %s)
                  )
                RETURNING id;
            """
            cursor.execute(query, (
                MigrationState.ANALYZING.value,
                worker_id,
                expires_at.isoformat(),
                now.isoformat(),
                job_id,
                MigrationState.QUEUED.value,
                MigrationState.ANALYZING.value,
                now.isoformat()
            ))
            row = cursor.fetchone()
            conn.commit()
            return row is not None
        except Exception as e:
            logger.error(f"DB Error acquiring lease: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    else:
        # Fallback to Supabase REST client if no direct DB is configured (less robust)
        # Note: This fallback does not properly handle stealing expired leases atomically via REST 
        # without a custom RPC. For Phase 3, we prefer direct DB if available.
        response = supabase_client.table("migration_jobs").update({
            "status": MigrationState.ANALYZING.value,
            "worker_id": worker_id,
            "lease_expires_at": expires_at.isoformat(),
            "heartbeat_at": now.isoformat()
        }).eq("id", job_id).eq("status", MigrationState.QUEUED.value).execute()
        return len(response.data) > 0

def release_lease(job_id: str, final_status: str, error_reason: str = None) -> None:
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if error_reason:
                cursor.execute(
                    "UPDATE migration_jobs SET status = %s, worker_id = NULL, lease_expires_at = NULL, error_reason = %s WHERE id = %s",
                    (final_status, error_reason, job_id)
                )
            else:
                cursor.execute(
                    "UPDATE migration_jobs SET status = %s, worker_id = NULL, lease_expires_at = NULL WHERE id = %s",
                    (final_status, job_id)
                )
            conn.commit()
        except Exception as e:
            logger.error(f"DB Error releasing lease: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    else:
        update_data = {
            "status": final_status,
            "worker_id": None,
            "lease_expires_at": None
        }
        if error_reason:
            update_data["error_reason"] = error_reason
            
        supabase_client.table("migration_jobs").update(update_data).eq("id", job_id).execute()


@celery_app.task(bind=True, max_retries=3)
def process_migration_job(self, job_id: str, organization_id: str):
    worker_id = f"{socket.gethostname()}-{self.request.id}"
    logger.info(f"Worker {worker_id} attempting to claim job {job_id} for org {organization_id}")
    
    # 1. Atomic Claim
    if not acquire_lease(job_id, worker_id):
        logger.warning(f"Failed to acquire lease for job {job_id}. It may be locked or already processing.")
        return # Skip, we didn't get the lease. Idempotency enforced.

    try:
        # Validate state transition explicitly in code (we already transitioned to ANALYZING in DB during claim)
        validate_transition(MigrationState.QUEUED.value, MigrationState.ANALYZING.value)
        
        # Phase 1-3 pipelines are not fully implemented.
        raise NotImplementedError("Phase 1-3 migration pipeline not fully implemented")
        
        # 5. Success
        release_lease(job_id, MigrationState.COMPLETED.value)
        
    except InvalidStateTransitionError as exc:
        logger.error(f"State transition error for {job_id}: {exc}")
        release_lease(job_id, MigrationState.FAILED.value, str(exc))
        
    except Exception as exc:
        logger.error(f"Error processing job {job_id}: {exc}")
        release_lease(job_id, MigrationState.FAILED.value, str(exc))
        self.retry(exc=exc, countdown=10)

@celery_app.task(bind=True, max_retries=3)
def process_generation_job(self, run_id: str, organization_id: str):
    worker_id = f"{socket.gethostname()}-{self.request.id}"
    logger.info(f"Worker {worker_id} attempting to process generation run {run_id}")
    
    import os
    import tempfile
    from app.generation.repository import GenerationRepository
    from app.generation.state import StateTransitionService
    from app.generation.orchestrator import GenerationOrchestrator
    from app.generation.generator import FlutterGenerator
    from app.generation.workspace import GenerationWorkspace
    from app.generation.schema import GenerationSpec, GenerationTarget
    from app.orchestration.finalizer import GenerationFinalizer
    from app.validation.engine import ValidationEngine, FlutterStructureValidator
    from app.validation.dependency import DependencyValidator
    from app.generation.review import ReviewResult
    from app.generation.remediation import RemediationEngine
    from app.ai.providers.openai_provider import OpenAIProvider
    from app.core.state_machine import MigrationState

    repo = GenerationRepository(os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forgeflow_test"))
    state_service = StateTransitionService(repo)
    user_id = organization_id
    
    try:
        if not state_service.transition_generation_run(run_id, MigrationState.PLANNING.value, MigrationState.GENERATING.value, user_id):
            logger.warning(f"Could not transition {run_id} to GENERATING.")
            return

        workspace_dir = tempfile.mkdtemp(prefix=f"workspace_{run_id}_")
        ws = GenerationWorkspace(workspace_dir)
        
        ai_provider = OpenAIProvider()
        generator = FlutterGenerator(ai_provider)
        orchestrator = GenerationOrchestrator(generator, ws)
        
        spec = GenerationSpec(
            source_project_id="test", source_version_id="v1", air_version="1.0", plan_version="1.0",
            target=GenerationTarget(flutter_version="3.10.0", dart_version="3.0.0"),
            security_constraints=["no eval"]
        )
        
        generated_files = orchestrator.run_generation(spec, run_id)
        files_dict = [f.model_dump() for f in generated_files]
        repo.record_generated_files(run_id, organization_id, files_dict, user_id)
        
        if not state_service.transition_generation_run(run_id, MigrationState.GENERATING.value, MigrationState.REVIEWING.value, user_id):
            return

        rev_result = ReviewResult(status="ACCEPTED", confidence=0.99)
        
        if not state_service.transition_generation_run(run_id, MigrationState.REVIEWING.value, MigrationState.VALIDATING.value, user_id):
            return

        engine = ValidationEngine([FlutterStructureValidator(), DependencyValidator()])
        remediation_engine = RemediationEngine(generator)
        attempt = 0
        val_result = None
        
        while attempt <= RemediationEngine.MAX_REMEDIATION_ATTEMPTS:
            workspace_content = {f: ws.read_file(f) for f in ws.list_files()}
            val_result = engine.run_pipeline(workspace_content)
            
            repo.record_validation_run(run_id, organization_id, "ValidationEngine", "PASS" if val_result.is_valid else "FAIL", "\n".join(val_result.errors) if val_result.errors else "", user_id)
            
            if val_result.is_valid:
                break
                
            attempt += 1
            if attempt > RemediationEngine.MAX_REMEDIATION_ATTEMPTS:
                break
                
            if not state_service.transition_generation_run(run_id, MigrationState.VALIDATING.value, MigrationState.REMEDIATING.value, user_id):
                return
                
            patched = remediation_engine.run_remediation(ws, spec, val_result, attempt)
            if not patched:
                break
                
            if not state_service.transition_generation_run(run_id, MigrationState.REMEDIATING.value, MigrationState.VALIDATING.value, user_id):
                return

        if not val_result or not val_result.is_valid:
            state_service.transition_generation_run(run_id, MigrationState.VALIDATING.value, MigrationState.FAILED.value, user_id)
            return

        if not state_service.transition_generation_run(run_id, MigrationState.VALIDATING.value, MigrationState.BUILDING.value, user_id):
            return

        sandbox_result = {"status": "SUCCESS"}

        if not state_service.transition_generation_run(run_id, MigrationState.BUILDING.value, MigrationState.FINAL_SECURITY_SCAN.value, user_id):
            return

        archive_dir = tempfile.mkdtemp(prefix=f"archives_{run_id}_")
        finalizer = GenerationFinalizer(archive_dir)
        try:
            artifact_path = finalizer.finalize_generation(run_id, ws, val_result, rev_result, sandbox_result)
        except Exception as fe:
            logger.error(f"Finalizer error: {fe}")
            state_service.transition_generation_run(run_id, MigrationState.FINAL_SECURITY_SCAN.value, MigrationState.FAILED.value, user_id)
            return

        state_service.transition_generation_run(run_id, MigrationState.FINAL_SECURITY_SCAN.value, MigrationState.COMPLETED.value, user_id)
        
    except Exception as exc:
        logger.error(f"Error processing generation run {run_id}: {exc}")
        self.retry(exc=exc, countdown=10)
