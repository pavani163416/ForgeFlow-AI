import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
from app.core.security import require_organization_member, User

@pytest.mark.asyncio
async def test_require_organization_member_success():
    # Mock user and Supabase client
    user = User(id="user-123", email="test@example.com", role="authenticated")
    org_id = "org-456"
    
    mock_supabase = MagicMock()
    # Mocking supabase_client.table().select().eq().eq().execute() chain
    mock_execute = MagicMock()
    mock_execute.data = [{"role": "OWNER"}]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute = MagicMock(return_value=mock_execute)
    
    with patch("app.core.security.supabase_client", mock_supabase):
        role = await require_organization_member(org_id, user)
        assert role == "OWNER"

@pytest.mark.asyncio
async def test_require_organization_member_forbidden():
    user = User(id="user-123", email="test@example.com", role="authenticated")
    org_id = "org-456"
    
    mock_supabase = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [] # Empty list implies no membership
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute = MagicMock(return_value=mock_execute)
    
    with patch("app.core.security.supabase_client", mock_supabase):
        with pytest.raises(HTTPException) as exc:
            await require_organization_member(org_id, user)
        assert exc.value.status_code == 403
        assert exc.value.detail == "Not a member of this organization"
