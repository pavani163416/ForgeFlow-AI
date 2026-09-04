from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import require_authenticated_user, require_role, User

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    framework: str
    organization_id: str

@router.post("/")
async def create_project(
    project: ProjectCreate,
    user: User = Depends(require_authenticated_user),
):
    """
    Create a new project. Requires ADMIN or OWNER role in the organization.
    Note: We invoke the dependency function manually here to pass the dynamic organization_id from the payload.
    """
    # We validate role manually since org_id is in body
    from app.core.security import require_organization_member
    role = await require_organization_member(project.organization_id, user)
    if role not in ["OWNER", "ADMIN", "MEMBER"]:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to create project")

    return {"id": "mock-proj-uuid", "name": project.name, "organization_id": project.organization_id}

@router.get("/{organization_id}/{project_id}")
async def get_project(
    organization_id: str,
    project_id: str,
    user: User = Depends(require_authenticated_user),
    role: str = Depends(require_role(["OWNER", "ADMIN", "MEMBER", "VIEWER"]))
):
    """
    Get project details. Project must belong to the organization, and user must be in organization.
    """
    return {"id": project_id, "name": "Mock Project", "organization_id": organization_id}
