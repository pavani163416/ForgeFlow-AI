from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_authenticated_user, require_organization_member, require_role, User
from pydantic import BaseModel

router = APIRouter()

class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: str
    name: str

@router.post("/", response_model=OrganizationResponse)
async def create_organization(org: OrganizationCreate, user: User = Depends(require_authenticated_user)):
    """
    Create a new organization. The user becomes the OWNER.
    """
    # Logic to insert into DB would go here
    return {"id": "mock-uuid", "name": org.name}

@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str, 
    user: User = Depends(require_authenticated_user),
    role: str = Depends(require_role(["OWNER", "ADMIN", "MEMBER", "VIEWER"]))
):
    """
    Get organization details. Requires membership.
    """
    return {"id": organization_id, "name": "Mock Org"}
