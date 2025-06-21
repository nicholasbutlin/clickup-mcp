"""Pytest configuration and shared fixtures."""

from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import AsyncClient, Response

from clickup_mcp.client import ClickUpClient
from clickup_mcp.config import Config


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=Config)
    config.api_key = "test_api_key_123"
    config.default_workspace_id = "test_workspace"
    config.id_patterns = {"gh": "github", "bug": "bugfix"}
    config.headers = {
        "Authorization": "test_api_key_123",
        "Content-Type": "application/json",
    }
    return config


@pytest.fixture
def mock_response():
    """Factory for creating mock HTTP responses."""

    def _make_response(
        status_code: int = 200,
        json_data: Dict[str, Any] | None = None,
        text: str = "",
    ) -> Response:
        response = Mock(spec=Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = text
        return response

    return _make_response


@pytest.fixture
async def mock_client(mock_config):
    """Mock ClickUp client for testing."""
    client = ClickUpClient(mock_config)
    # Replace the httpx client with a mock
    client.client = AsyncMock(spec=AsyncClient)
    return client


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        "id": "abc123",
        "custom_id": "gh-123",
        "name": "Test Task",
        "description": "This is a test task",
        "status": {
            "id": "status123",
            "status": "todo",
            "color": "#ffffff",
            "orderindex": 0,
            "type": "open",
        },
        "orderindex": 1.0,
        "date_created": "1640995200000",
        "date_updated": "1640995200000",
        "date_closed": None,
        "archived": False,
        "creator": {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "color": "#000000",
            "initials": "TU",
            "profile_picture": None,
        },
        "assignees": [],
        "tags": ["test", "example"],
        "parent": None,
        "priority": None,
        "due_date": None,
        "start_date": None,
        "time_estimate": None,
        "time_spent": 0,
        "custom_fields": [],
        "list": {"id": "list123", "name": "Test List"},
        "folder": {"id": "folder123", "name": "Test Folder"},
        "space": {"id": "space123", "name": "Test Space"},
        "url": "https://app.clickup.com/t/abc123",
    }


@pytest.fixture
def sample_list():
    """Sample list data for testing."""
    return {
        "id": "list123",
        "name": "Test List",
        "orderindex": 0,
        "status": None,
        "priority": None,
        "assignee": None,
        "task_count": 5,
        "due_date": None,
        "start_date": None,
        "folder": {"id": "folder123", "name": "Test Folder"},
        "space": {"id": "space123", "name": "Test Space"},
        "archived": False,
    }


@pytest.fixture
def sample_space():
    """Sample space data for testing."""
    return {
        "id": "space123",
        "name": "Test Space",
        "private": False,
        "color": "#FF0000",
        "avatar": None,
        "admin_can_manage": True,
        "statuses": [
            {
                "id": "status1",
                "status": "todo",
                "color": "#ffffff",
                "orderindex": 0,
                "type": "open",
            },
            {
                "id": "status2",
                "status": "in_progress",
                "color": "#00ff00",
                "orderindex": 1,
                "type": "custom",
            },
            {
                "id": "status3",
                "status": "done",
                "color": "#0000ff",
                "orderindex": 2,
                "type": "closed",
            },
        ],
        "multiple_assignees": True,
        "features": {
            "due_dates": {"enabled": True},
            "time_tracking": {"enabled": True},
            "tags": {"enabled": True},
        },
        "archived": False,
    }


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "id": 123,
        "username": "testuser",
        "email": "test@example.com",
        "color": "#000000",
        "initials": "TU",
        "profile_picture": None,
    }


@pytest.fixture
def sample_comment():
    """Sample comment data for testing."""
    return {
        "id": "comment123",
        "comment_text": "This is a test comment",
        "user": {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "color": "#000000",
            "initials": "TU",
            "profile_picture": None,
        },
        "date": "1640995200000",
        "resolved": False,
        "assignee": None,
    }
