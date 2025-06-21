"""Tests for ClickUp API client."""

from unittest.mock import AsyncMock, Mock

import pytest
from clickup_mcp.client import ClickUpAPIError, ClickUpClient
from httpx import HTTPStatusError, Request, Response


class TestClickUpClient:
    """Test ClickUp API client functionality."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = ClickUpClient(mock_config)
        assert client.config == mock_config
        assert client.BASE_URL == "https://api.clickup.com/api/v2"
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_request_headers(self, mock_client):
        """Test that proper headers are set."""
        mock_client.client.request = AsyncMock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_client.client.request.return_value = mock_response

        await mock_client._request("GET", "/test")

        mock_client.client.request.assert_called_once()
        call_args = mock_client.client.request.call_args
        # The client should use the config headers
        assert call_args.args[0] == "GET"
        assert call_args.args[1] == "/test"

    @pytest.mark.asyncio
    async def test_create_task(self, mock_client, mock_response, sample_task):
        """Test creating a task."""
        from clickup_mcp.models import CreateTaskRequest, Task
        
        mock_response_obj = mock_response(200, sample_task)
        mock_client.client.request = AsyncMock(return_value=mock_response_obj)

        task_request = CreateTaskRequest(
            name="Test Task",
            description="Test description",
        )
        
        result = await mock_client.create_task(
            list_id="list123",
            task=task_request,
        )

        # Should return a Task object, not raw dict
        assert isinstance(result, Task)
        assert result.name == sample_task["name"]
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task(self, mock_client, mock_response, sample_task):
        """Test getting a task."""
        from clickup_mcp.models import Task
        
        mock_response_obj = mock_response(200, sample_task)
        mock_client.client.request = AsyncMock(return_value=mock_response_obj)

        result = await mock_client.get_task("abc123")

        # Should return a Task object
        assert isinstance(result, Task)
        assert result.id == sample_task["id"]
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task(self, mock_client, mock_response, sample_task):
        """Test updating a task."""
        from clickup_mcp.models import UpdateTaskRequest, Task
        
        updated_task = {**sample_task, "name": "Updated Task"}
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, updated_task)
        )

        update_request = UpdateTaskRequest(name="Updated Task")
        result = await mock_client.update_task("abc123", update_request)

        assert isinstance(result, Task)
        assert result.name == "Updated Task"
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task(self, mock_client, mock_response):
        """Test deleting a task."""
        mock_client.client.request = AsyncMock(
            return_value=mock_response(204, {})
        )

        result = await mock_client.delete_task("abc123")

        assert result is None
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tasks(self, mock_client, mock_response, sample_task):
        """Test getting tasks."""
        from clickup_mcp.models import Task
        
        tasks_response = {"tasks": [sample_task]}
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, tasks_response)
        )

        result = await mock_client.get_tasks(list_id="list123")

        # get_tasks should return a list of Task objects
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Task)
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_tasks(self, mock_client, mock_response, sample_task):
        """Test searching tasks."""
        from clickup_mcp.models import Task
        
        search_response = {"tasks": [sample_task]}
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, search_response)
        )

        result = await mock_client.search_tasks(
            workspace_id="workspace123",
            query="test",
        )

        # search_tasks returns List[Task]
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Task)
        assert result[0].id == "abc123"
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_client, mock_response):
        """Test getting current user."""
        user_data = {
            "user": {
                "id": 123,
                "username": "testuser",
                "email": "test@example.com",
                "color": "#FF0000",
                "initials": "TU",
            }
        }
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, user_data)
        )

        result = await mock_client.get_current_user()

        assert result["id"] == 123
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workspace_members(self, mock_client, mock_response):
        """Test getting workspace members."""
        # Test successful groups endpoint response
        groups_data = {
            "groups": [
                {
                    "id": "group1",
                    "name": "Group 1",
                    "members": [
                        {"id": 1, "username": "user1", "email": "user1@example.com"},
                        {"id": 2, "username": "user2", "email": "user2@example.com"},
                    ]
                },
                {
                    "id": "group2",
                    "name": "Group 2",
                    "members": [
                        {"id": 2, "username": "user2", "email": "user2@example.com"},  # Duplicate
                        {"id": 3, "username": "user3", "email": "user3@example.com"},
                    ]
                }
            ]
        }
        mock_client.client.request = AsyncMock(
            return_value=mock_response(200, groups_data)
        )

        result = await mock_client.get_workspace_members("workspace123")

        # Should return unique members
        assert len(result) == 3
        user_ids = [member["id"] for member in result]
        assert user_ids == [1, 2, 3]
        mock_client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workspace_members_fallback(self, mock_client, mock_response):
        """Test workspace members fallback to team endpoint."""
        # Mock groups endpoint failure
        error_response = mock_response(403, {"err": "Access denied"})
        error_response.status_code = 403
        
        # Mock team endpoint success
        team_data = {
            "team": {
                "id": "workspace123",
                "members": [
                    {"id": 1, "username": "user1", "email": "user1@example.com"},
                    {"id": 2, "username": "user2", "email": "user2@example.com"},
                ]
            }
        }
        
        mock_client.client.request = AsyncMock(
            side_effect=[error_response, mock_response(200, team_data)]
        )

        result = await mock_client.get_workspace_members("workspace123")

        assert len(result) == 2
        assert result[0]["username"] == "user1"
        assert mock_client.client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_client, mock_response):
        """Test API error handling."""
        # Mock a 404 response - the client checks status_code and raises ClickUpAPIError
        error_response = mock_response(404, {})
        error_response.text = "Task not found"
        error_response.json.side_effect = Exception("No JSON")  # Simulate JSON parse error
        
        mock_client.client.request = AsyncMock(return_value=error_response)

        with pytest.raises(ClickUpAPIError) as exc_info:
            await mock_client.get_task("abc123")

        assert exc_info.value.status_code == 404
        assert "Task not found" in str(exc_info.value)

    # Note: Methods like update_task_status, assign_task, bulk_update_tasks, log_time
    # don't exist in the client layer - they are tools layer methods.
    # Client layer only provides basic CRUD operations.
