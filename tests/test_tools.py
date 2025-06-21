"""Tests for MCP tools implementation."""

from unittest.mock import AsyncMock

import pytest
from clickup_mcp.client import ClickUpAPIError
from clickup_mcp.tools import ClickUpTools


class TestClickUpTools:
    """Test MCP tools functionality."""

    @pytest.fixture
    async def tools(self, mock_client):
        """Create tools instance with mocked client."""
        return ClickUpTools(mock_client)

    @pytest.mark.asyncio
    async def test_create_task(self, tools, sample_task):
        """Test create_task tool."""
        from clickup_mcp.models import Task
        
        # Mock create_task to return a Task object
        task_obj = Task(**sample_task)
        tools.client.create_task = AsyncMock(return_value=task_obj)

        result = await tools.create_task(
            title="Test Task",
            description="Test description", 
            list_id="list123",
        )

        # Check the expected return format from tools.create_task
        assert result["id"] == "abc123"
        assert result["name"] == "Test Task"
        assert result["url"] == "https://app.clickup.com/t/abc123"
        assert result["created"] == True
        tools.client.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_with_list_name(self, tools, sample_task, sample_list):
        """Test create_task with list name instead of ID."""
        from clickup_mcp.models import Task, List as ClickUpList
        
        # Mock the client methods that will be called
        list_obj = ClickUpList(**sample_list)
        task_obj = Task(**sample_task)
        
        tools.client.find_list_by_name = AsyncMock(return_value=list_obj)
        tools.client.create_task = AsyncMock(return_value=task_obj)

        result = await tools.create_task(
            title="Test Task",
            list_name="Test List",
        )

        # Check the expected tools.create_task return format
        assert result["id"] == "abc123"
        assert result["name"] == "Test Task"
        assert result["created"] == True
        tools.client.find_list_by_name.assert_called_once_with("Test List")
        tools.client.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_with_custom_id(self, tools, sample_task):
        """Test getting task with custom ID format."""
        from clickup_mcp.models import Task
        
        # Mock task object
        task_obj = Task(**sample_task)
        
        # For custom ID, it should call search_tasks, not get_task directly
        tools.client.search_tasks = AsyncMock(return_value=[task_obj])
        
        result = await tools.get_task("gh-123")

        # Check the expected return format
        assert result["id"] == "abc123"
        assert result["name"] == "Test Task"
        assert result["url"] == "https://app.clickup.com/t/abc123"
        tools.client.search_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task(self, tools, sample_task):
        """Test update_task tool."""
        from clickup_mcp.models import Task
        
        updated_task_data = {**sample_task, "name": "Updated Task"}
        updated_task_obj = Task(**updated_task_data)
        tools.client.update_task = AsyncMock(return_value=updated_task_obj)

        result = await tools.update_task(
            task_id="abc123",
            updates={"name": "Updated Task"},
        )

        # Check the tools.update_task return format
        assert result["id"] == "abc123"
        assert result["name"] == "Updated Task"
        tools.client.update_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, tools, sample_task):
        """Test listing tasks with various filters."""
        from clickup_mcp.models import Task
        
        # Mock the client method that will actually be called
        task_obj = Task(**sample_task)
        tools.client.get_tasks = AsyncMock(return_value=[task_obj])

        result = await tools.list_tasks(
            list_id="list123",
            status="todo",
            assignee=123,
        )

        # Check tools.list_tasks return format
        assert "tasks" in result
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["id"] == "abc123"
        tools.client.get_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_tasks(self, tools, sample_task):
        """Test searching tasks."""
        from clickup_mcp.models import Task
        
        # Mock client.search_tasks to return List[Task]
        task_obj = Task(**sample_task)
        tools.client.search_tasks = AsyncMock(return_value=[task_obj])

        result = await tools.search_tasks(
            query="bug fix",
            space_id="space123",
        )

        # Check tools.search_tasks return format
        assert "tasks" in result
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["id"] == "abc123"
        tools.client.search_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_tasks(self, tools):
        """Test bulk updating tasks."""
        from clickup_mcp.models import Task
        
        # Mock client.update_task to return Task objects
        task1_data = {"id": "task1", "name": "Task 1", "status": {"id": "status1", "status": "done", "color": "#ffffff", "orderindex": 0, "type": "closed"}, "creator": {"id": 123, "username": "testuser"}, "list": {"id": "list123", "name": "Test List"}, "folder": {"id": "folder123", "name": "Test Folder"}, "space": {"id": "space123", "name": "Test Space"}, "url": "https://app.clickup.com/t/task1", "assignees": [], "tags": [], "custom_fields": []}
        task2_data = {"id": "task2", "name": "Task 2", "status": {"id": "status1", "status": "done", "color": "#ffffff", "orderindex": 0, "type": "closed"}, "creator": {"id": 123, "username": "testuser"}, "list": {"id": "list123", "name": "Test List"}, "folder": {"id": "folder123", "name": "Test Folder"}, "space": {"id": "space123", "name": "Test Space"}, "url": "https://app.clickup.com/t/task2", "assignees": [], "tags": [], "custom_fields": []}
        
        task1_obj = Task(**task1_data)
        task2_obj = Task(**task2_data)
        
        tools.client.update_task = AsyncMock(
            side_effect=[task1_obj, task2_obj]
        )

        result = await tools.bulk_update_tasks(
            task_ids=["task1", "task2"],
            updates={"status": "done"},
        )

        # Check actual return format from implementation
        assert result["updated"] == ["task1", "task2"]
        assert result["failed"] == []

    @pytest.mark.asyncio
    async def test_create_task_from_template(self, tools, sample_task):
        """Test creating task from template."""
        from clickup_mcp.models import Task
        
        task_obj = Task(**sample_task)
        tools.client.create_task = AsyncMock(return_value=task_obj)

        result = await tools.create_task_from_template(
            template_name="bug_report",
            list_id="list123",
            customizations={"title": "Login button not working"}
        )

        # Check tools.create_task_from_template return format
        assert result["id"] == "abc123"
        assert result["name"] == "Test Task"
        assert result["template"] == "bug_report"
        assert result["url"] == "https://app.clickup.com/t/abc123"
        tools.client.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_chain(self, tools):
        """Test creating a chain of dependent tasks."""
        from clickup_mcp.models import Task
        
        # Create Task objects to mock client.create_task returns
        task1_data = {**self.get_base_task_data(), "id": "task1", "name": "Design"}
        task2_data = {**self.get_base_task_data(), "id": "task2", "name": "Implementation"}
        task3_data = {**self.get_base_task_data(), "id": "task3", "name": "Testing"}
        
        task1 = Task(**task1_data)
        task2 = Task(**task2_data)
        task3 = Task(**task3_data)
        
        # Mock task creation to return Task objects
        tools.client.create_task = AsyncMock(side_effect=[task1, task2, task3])

        chain_tasks = [
            {"title": "Design", "description": "Design phase"},
            {"title": "Implementation", "description": "Code it"},
            {"title": "Testing", "description": "Test it"},
        ]

        result = await tools.create_task_chain(
            list_id="list123",
            tasks=chain_tasks,
        )

        assert result["created"] == 3
        assert len(result["tasks"]) == 3
        assert result["linked"] == True
        assert result["tasks"][0]["id"] == "task1"
        assert result["tasks"][1]["id"] == "task2"
        assert result["tasks"][2]["id"] == "task3"

    @pytest.mark.asyncio
    async def test_get_team_workload(self, tools, sample_user):
        """Test getting team workload."""
        from clickup_mcp.models import Task, User
        
        # Create User objects for assignees
        user_obj = User(**sample_user)
        
        # Create sample tasks with assignees
        task1_data = {**self.get_base_task_data(), "id": "task1", "assignees": [user_obj]}
        task2_data = {**self.get_base_task_data(), "id": "task2", "assignees": [user_obj]}
        
        task1 = Task(**task1_data)
        task2 = Task(**task2_data)
        
        # Mock get_tasks which is what actually gets called
        tools.client.get_tasks = AsyncMock(return_value=[task1, task2])

        result = await tools.get_team_workload("space123")

        assert result["space_id"] == "space123"
        assert result["total_tasks"] == 2
        assert len(result["team_workload"]) == 1
        assert result["team_workload"][0]["user_id"] == 123
        assert result["team_workload"][0]["username"] == "testuser"  
        assert result["team_workload"][0]["task_count"] == 2

    def get_base_task_data(self):
        """Helper to get base task data for testing."""
        return {
            "name": "Test Task",
            "description": "Test description",
            "status": {"id": "status123", "status": "todo", "color": "#ffffff", "orderindex": 0, "type": "open"},
            "creator": {"id": 123, "username": "testuser", "email": "test@example.com", "color": "#000000", "initials": "TU", "profile_picture": None},
            "list": {"id": "list123", "name": "Test List"},
            "folder": {"id": "folder123", "name": "Test Folder"},
            "space": {"id": "space123", "name": "Test Space"},
            "url": "https://app.clickup.com/t/abc123",
            "assignees": [],
            "tags": [],
            "custom_fields": []
        }

    @pytest.mark.asyncio
    async def test_log_time(self, tools):
        """Test logging time on a task."""
        # Mock the _request method that is actually called
        tools.client._request = AsyncMock()

        result = await tools.log_time(
            task_id="abc123",
            duration="2h 30m",
            description="Working on feature",
        )

        assert result["logged"] == True
        assert result["task_id"] == "abc123"
        assert result["duration_ms"] == 9000000  # 2.5 hours in ms
        assert result["duration"] == "2h 30m"
        tools.client._request.assert_called_once_with(
            "POST", 
            "/team/test_workspace/time_entries",
            json={
                "duration": 9000000,
                "task_id": "abc123", 
                "description": "Working on feature"
            }
        )

    @pytest.mark.asyncio
    async def test_get_task_analytics(self, tools, sample_task):
        """Test getting task analytics."""
        from clickup_mcp.models import Task
        
        # Mock completed and in-progress tasks
        completed_task_data = {**sample_task, "status": {"id": "status1", "status": "done", "color": "#ffffff", "orderindex": 0, "type": "closed"}}
        in_progress_task_data = {**sample_task, "status": {"id": "status2", "status": "in_progress", "color": "#ffffff", "orderindex": 0, "type": "custom"}}

        # Create Task objects from the data
        completed_task = Task(**completed_task_data)
        in_progress_task = Task(**in_progress_task_data)  
        regular_task = Task(**sample_task)

        # Mock search_tasks which is what actually gets called
        tools.client.search_tasks = AsyncMock(
            return_value=[completed_task, in_progress_task, regular_task]
        )

        result = await tools.get_task_analytics("space123")

        assert result["space_id"] == "space123"
        assert result["period_days"] == 30
        assert result["metrics"]["total_tasks_created"] == 3
        assert result["metrics"]["completed_tasks"] == 1
        # The completion rate should be 1/3 = 33.33%
        assert result["metrics"]["completion_rate"] == pytest.approx(33.33, 0.01)

    @pytest.mark.asyncio
    async def test_error_handling(self, tools):
        """Test error handling in tools."""
        tools.client.get_task = AsyncMock(
            side_effect=ClickUpAPIError("Task not found", 404)
        )

        with pytest.raises(ClickUpAPIError) as exc_info:
            await tools.get_task("nonexistent")

        assert exc_info.value.status_code == 404
