"""Tests for user management tools."""

from unittest.mock import AsyncMock

import pytest
from clickup_mcp.tools import ClickUpTools


class TestUserTools:
    """Test user management tools functionality."""

    @pytest.fixture
    async def tools(self, mock_client):
        """Create tools instance with mocked client."""
        return ClickUpTools(mock_client)

    @pytest.mark.asyncio
    async def test_list_users(self, tools):
        """Test list_users tool."""
        members_data = [
            {"id": 1, "username": "user1", "email": "user1@example.com", "color": "#FF0000", "initials": "U1"},
            {"id": 2, "username": "user2", "email": "user2@example.com", "color": "#00FF00", "initials": "U2"},
        ]
        tools.client.get_workspace_members = AsyncMock(return_value=members_data)

        result = await tools.list_users()

        assert result["count"] == 2
        assert len(result["users"]) == 2
        assert result["users"][0]["id"] == 1
        assert result["users"][0]["username"] == "user1"
        tools.client.get_workspace_members.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user(self, tools):
        """Test get_current_user tool."""
        user_data = {
            "id": 123,
            "username": "currentuser",
            "email": "current@example.com",
            "role": 2,
            "color": "#0000FF",
            "initials": "CU",
        }
        tools.client.get_current_user = AsyncMock(return_value=user_data)

        result = await tools.get_current_user()

        assert result["id"] == 123
        assert result["username"] == "currentuser"
        assert result["email"] == "current@example.com"
        assert result["role"] == 2
        tools.client.get_current_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_user_by_name(self, tools):
        """Test find_user_by_name tool."""
        members_data = [
            {"id": 1, "username": "john.doe", "email": "john@example.com"},
            {"id": 2, "username": "jane.smith", "email": "jane@example.com"},
            {"id": 3, "username": "bob.jones", "email": "bob@example.com"},
        ]
        tools.client.get_workspace_members = AsyncMock(return_value=members_data)

        # Test finding by partial username
        result = await tools.find_user_by_name("john")

        assert result["found"] == True
        assert result["count"] == 1
        assert result["matches"][0]["username"] == "john.doe"

        # Test finding by email
        result = await tools.find_user_by_name("jane@")

        assert result["found"] == True
        assert result["count"] == 1
        assert result["matches"][0]["email"] == "jane@example.com"

        # Test no matches
        result = await tools.find_user_by_name("nonexistent")

        assert "error" in result
        assert result["matches"] == []