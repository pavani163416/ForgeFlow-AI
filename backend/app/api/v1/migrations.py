from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import require_authenticated_user, require_role, User

router = APIRouter()

class MigrationJobCreate(BaseModel):
    project_id: str
    organization_id: str

@router.post("/")
async def create_migration_job(
    job: MigrationJobCreate,
    user: User = Depends(require_authenticated_user),
):
    """
    Create a new migration job and return a signed upload URL for the ZIP.
    """
    from app.core.security import require_organization_member
    role = await require_organization_member(job.organization_id, user)
    if role not in ["OWNER", "ADMIN", "MEMBER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return {
        "job_id": "mock-job-uuid", 
        "status": "CREATED", 
        "upload_url": "https://storage.supabase.co/mock-signed-url-for-upload"
    }

@router.post("/{organization_id}/{job_id}/start")
async def start_migration_job(
    organization_id: str,
    job_id: str,
    user: User = Depends(require_authenticated_user),
    role: str = Depends(require_role(["OWNER", "ADMIN", "MEMBER"]))
):
    """
    Called after client successfully uploads the ZIP. Changes status to QUEUED and pushes to Redis.
    """
    # Logic to enqueue to Redis
    return {"status": "QUEUED"}

@router.get("/{organization_id}/{job_id}")
async def get_migration_status(
    organization_id: str,
    job_id: str,
    user: User = Depends(require_authenticated_user),
    role: str = Depends(require_role(["OWNER", "ADMIN", "MEMBER", "VIEWER"]))
):
    """
    Get current status of a migration job.
    """
    return {"id": job_id, "status": "QUEUED", "organization_id": organization_id}
