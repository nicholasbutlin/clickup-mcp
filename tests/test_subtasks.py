"""Tests for subtasks functionality."""

import pytest
from unittest.mock import AsyncMock

from clickup_mcp.client import ClickUpClient
from clickup_mcp.config import Config
from clickup_mcp.models import Task, TaskStatus, User, Workspace


class TestSubtasks:
    """Test subtasks functionality."""

    @pytest.fixture
    def client(self):
        """Create a mock client for testing."""
        config = Config(api_key="test_key")
        client = ClickUpClient(config)
        # Mock the HTTP client
        client.client = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_subtasks_with_workspace_id_in_config(self, client):
        """Test get_subtasks when workspace_id is configured."""
        # Set up workspace_id in config
        client.config.default_workspace_id = "workspace123"
        
        # Mock the API response for subtasks
        subtask_data = {
            "tasks": [
                {
                    "id": "subtask1",
                    "name": "Subtask 1",
                    "status": {"id": "status1", "status": "open", "color": "#ffffff", "orderindex": 0, "type": "open"},
                    "creator": {"id": 123, "username": "testuser"},
                    "list": {"id": "list123", "name": "Test List"},
                    "folder": {"id": "folder123", "name": "Test Folder"},
                    "space": {"id": "space123", "name": "Test Space"},
                    "url": "https://app.clickup.com/t/subtask1",
                    "assignees": [],
                    "tags": [],
                    "custom_fields": [],
                    "parent": "parent123",
                }
            ]
        }
        
        client._request = AsyncMock(return_value=subtask_data)
        
        # Call get_subtasks
        result = await client.get_subtasks("parent123")
        
        # Verify the correct API call was made
        client._request.assert_called_once_with(
            "GET",
            "/team/workspace123/task",
            params={
                "parent": "parent123",
                "include_closed": "true",
            }
        )
        
        # Verify result
        assert len(result) == 1
        assert result[0].id == "subtask1"
        assert result[0].name == "Subtask 1"
        assert result[0].parent == "parent123"

    @pytest.mark.asyncio
    async def test_get_subtasks_without_workspace_id_in_config(self, client):
        """Test get_subtasks when workspace_id needs to be fetched."""
        # Don't set workspace_id in config
        client.config.default_workspace_id = None
        
        # Mock workspace response
        workspace_data = {
            "teams": [
                {"id": "workspace123", "name": "Test Workspace", "color": "#ffffff", "avatar": None, "members": []}
            ]
        }
        
        # Mock subtasks response
        subtask_data = {
            "tasks": [
                {
                    "id": "subtask1",
                    "name": "Subtask 1",
                    "status": {"id": "status1", "status": "open", "color": "#ffffff", "orderindex": 0, "type": "open"},
                    "creator": {"id": 123, "username": "testuser"},
                    "list": {"id": "list123", "name": "Test List"},
                    "folder": {"id": "folder123", "name": "Test Folder"},
                    "space": {"id": "space123", "name": "Test Space"},
                    "url": "https://app.clickup.com/t/subtask1",
                    "assignees": [],
                    "tags": [],
                    "custom_fields": [],
                    "parent": "parent123",
                }
            ]
        }
        
        # Set up mock to return different responses for different endpoints
        def mock_request(method, path, **kwargs):
            if path == "/team":
                return workspace_data
            elif path == "/team/workspace123/task":
                return subtask_data
            return {}
        
        client._request = AsyncMock(side_effect=mock_request)
        
        # Call get_subtasks
        result = await client.get_subtasks("parent123")
        
        # Verify two API calls were made
        assert client._request.call_count == 2
        
        # Check the calls
        calls = client._request.call_args_list
        assert calls[0][0] == ("GET", "/team")  # First call to get workspaces
        assert calls[1][0] == ("GET", "/team/workspace123/task")  # Second call to get subtasks
        assert calls[1][1]["params"] == {
            "parent": "parent123",
            "include_closed": "true",
        }
        
        # Verify result
        assert len(result) == 1
        assert result[0].id == "subtask1"
        assert result[0].name == "Subtask 1"
        assert result[0].parent == "parent123"

    @pytest.mark.asyncio
    async def test_get_subtasks_no_workspaces(self, client):
        """Test get_subtasks when no workspaces are found."""
        client.config.default_workspace_id = None
        
        # Mock empty workspace response
        workspace_data = {"teams": []}
        client._request = AsyncMock(return_value=workspace_data)
        
        # Call get_subtasks
        result = await client.get_subtasks("parent123")
        
        # Should return empty list when no workspaces found
        assert result == []
        
        # Should only call workspace endpoint
        client._request.assert_called_once_with("GET", "/team")

    @pytest.mark.asyncio
    async def test_get_subtasks_empty_result(self, client):
        """Test get_subtasks when no subtasks are found."""
        client.config.default_workspace_id = "workspace123"
        
        # Mock empty subtasks response
        subtask_data = {"tasks": []}
        client._request = AsyncMock(return_value=subtask_data)
        
        # Call get_subtasks
        result = await client.get_subtasks("parent123")
        
        # Verify empty result
        assert result == []
        
        # Verify the correct API call was made
        client._request.assert_called_once_with(
            "GET",
            "/team/workspace123/task",
            params={
                "parent": "parent123",
                "include_closed": "true",
            }
        )

    @pytest.mark.asyncio
    async def test_get_subtasks_api_error_fallback(self, client):
        """Test get_subtasks error handling and fallback."""
        from clickup_mcp.client import ClickUpAPIError
        
        client.config.default_workspace_id = "workspace123"
        
        # Mock API error
        client._request = AsyncMock(side_effect=ClickUpAPIError("API Error", 500))
        
        # Call get_subtasks - should handle error gracefully
        result = await client.get_subtasks("parent123")
        
        # Should return empty list on error
        assert result == []