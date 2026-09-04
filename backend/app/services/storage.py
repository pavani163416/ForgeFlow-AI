from app.core.interfaces import StorageProvider
from app.core.security import supabase_client
from app.core.logger import get_logger
from fastapi import HTTPException, status
from typing import Optional

logger = get_logger(__name__)

class SupabaseStorageProvider(StorageProvider):
    
    def _verify_tenant_isolation(self, path: str, organization_id: str) -> bool:
        """
        Enforce tenant isolation on storage paths.
        Artifacts must be stored under /{organization_id}/...
        """
        if not path.startswith(f"{organization_id}/"):
            logger.error(f"Storage path isolation violation. Path: {path}, Org: {organization_id}")
            return False
        return True

    async def upload(self, bucket: str, path: str, file_content: bytes, organization_id: str) -> str:
        if not self._verify_tenant_isolation(path, organization_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage path does not match organization")
            
        try:
            res = supabase_client.storage.from_(bucket).upload(path, file_content)
            return path
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage upload failed")

    async def download(self, bucket: str, path: str, organization_id: str) -> bytes:
        if not self._verify_tenant_isolation(path, organization_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage path does not match organization")
            
        try:
            res = supabase_client.storage.from_(bucket).download(path)
            return res
        except Exception as e:
            logger.error(f"Error downloading from Supabase: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found or access denied")

    async def delete(self, bucket: str, path: str, organization_id: str) -> bool:
        if not self._verify_tenant_isolation(path, organization_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage path does not match organization")
            
        try:
            res = supabase_client.storage.from_(bucket).remove([path])
            return True
        except Exception as e:
            logger.error(f"Error deleting from Supabase: {e}")
            return False

    async def generate_access_url(self, bucket: str, path: str, organization_id: str, expires_in: int = 3600) -> str:
        if not self._verify_tenant_isolation(path, organization_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage path does not match organization")
            
        try:
            res = supabase_client.storage.from_(bucket).create_signed_url(path, expires_in)
            return res['signedURL']
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate access URL")
