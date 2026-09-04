import os
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.worker import process_generation_job

router = APIRouter(prefix="/projects/{project_id}/migrations/{migration_id}")

def get_current_user_id() -> str:
    # Stub: Extracts JWT sub
    return "user-id-stub"

def verify_ownership(project_id: str, migration_id: str, user_id: str):
    # Stub: query DB for ownership
    pass

@router.post("/generate")
def start_generation(project_id: str, migration_id: str, spec_version: str = "1.0", generation_stage: str = "initial", input_identity: str = "unknown"):
    """
    Triggers Phase 4 async generation via Celery.
    Checks idempotency first.
    """
    user_id = get_current_user_id()
    verify_ownership(project_id, migration_id, user_id)
    
    # 1. Idempotency Check
    from app.generation.repository import GenerationRepository
    repo = GenerationRepository(os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forgeflow_test"))
    
    existing_run = repo.check_idempotency(
        organization_id="org_id_stub",
        migration_job_id=migration_id,
        generation_stage=generation_stage,
        spec_version=spec_version,
        input_identity=input_identity,
        user_id=user_id
    )
    if existing_run:
        return {"status": "idempotent_hit", "run_id": existing_run, "message": "Generation already completed."}
        
    # 2. Update state -> GENERATING and persist run request
    run_id = repo.create_generation_run(
        migration_job_id=migration_id,
        organization_id="org_id_stub",
        spec_version=spec_version,
        user_id=user_id,
        generation_stage=generation_stage,
        input_identity=input_identity
    )
    
    # 3. Queue celery task
    process_generation_job.delay(run_id, "org_id_stub")
    
    return {"status": "accepted", "run_id": run_id, "message": "Generation queued."}
