from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class User(BaseModel):
    id: str
    email: str
    role: str
    # other JWT claims

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    try:
        # Supabase uses HS256 by default for its JWTs
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            
        return User(id=user_id, email=email, role=role)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_authenticated_user(user: User = Depends(get_current_user)) -> User:
    return user

async def require_organization_member(organization_id: str, user: User = Depends(get_current_user)) -> str:
    """
    Validates that the current user is a member of the requested organization.
    Checks the database directly using the service role to ensure true server-side authorization.
    """
    try:
        # We query the DB to check membership. 
        # Note: Since the backend is a trusted environment, it might use service_role to check.
        response = supabase_client.table("organization_members").select("role").eq("organization_id", organization_id).eq("user_id", user.id).execute()
        
        if not response.data:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
            
        return response.data[0]['role']
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking organization membership: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authorization check failed")

def require_role(allowed_roles: List[str]):
    """
    Dependency factory to check if the user has one of the allowed roles in the organization.
    """
    async def role_checker(organization_id: str, user: User = Depends(get_current_user)):
        user_role = await require_organization_member(organization_id, user)
        if user_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient organization permissions")
        return user_role
    return role_checker
