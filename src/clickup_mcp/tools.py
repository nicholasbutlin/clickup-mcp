"""MCP tool implementations for ClickUp."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from mcp.types import Tool

from .client import ClickUpAPIError, ClickUpClient
from .models import (
    CreateDocRequest,
    CreateTaskRequest,
    Task,
    UpdateDocRequest,
    UpdateTaskRequest,
)
from .utils import format_task_url, parse_duration, parse_task_id

logger = logging.getLogger(__name__)


class ClickUpTools:
    """MCP tools for ClickUp operations."""

    def __init__(self, client: ClickUpClient) -> None:
        """Initialize tools with ClickUp client."""
        self.client = client
        self._tools: Dict[str, Callable] = {
            "create_task": self.create_task,
            "get_task": self.get_task,
            "update_task": self.update_task,
            "delete_task": self.delete_task,
            "list_tasks": self.list_tasks,
            "search_tasks": self.search_tasks,
            "get_subtasks": self.get_subtasks,
            "get_task_comments": self.get_task_comments,
            "create_task_comment": self.create_task_comment,
            "get_task_status": self.get_task_status,
            "update_task_status": self.update_task_status,
            "get_assignees": self.get_assignees,
            "assign_task": self.assign_task,
            "list_spaces": self.list_spaces,
            "list_folders": self.list_folders,
            "list_lists": self.list_lists,
            "find_list_by_name": self.find_list_by_name,
            # Docs management
            "create_doc": self.create_doc,
            "get_doc": self.get_doc,
            "update_doc": self.update_doc,
            "list_docs": self.list_docs,
            "search_docs": self.search_docs,
            # Bulk operations
            "bulk_update_tasks": self.bulk_update_tasks,
            "bulk_move_tasks": self.bulk_move_tasks,
            # Time tracking
            "get_time_tracked": self.get_time_tracked,
            "log_time": self.log_time,
            # Templates
            "create_task_from_template": self.create_task_from_template,
            "create_task_chain": self.create_task_chain,
            # Analytics
            "get_team_workload": self.get_team_workload,
            "get_task_analytics": self.get_task_analytics,
            # User management
            "list_users": self.list_users,
            "get_current_user": self.get_current_user,
            "find_user_by_name": self.find_user_by_name,
        }

    def get_tool_definitions(self) -> List[Tool]:
        """Get all tool definitions for MCP."""
        return [
            Tool(
                name="create_task",
                description="Create a new task in a specific list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "list_name": {
                            "type": "string",
                            "description": "Name of the list to create task in",
                        },
                        "list_id": {
                            "type": "string",
                            "description": "ID of the list (alternative to list_name)",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "User IDs to assign",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority (1=urgent, 2=high, 3=normal, 4=low)",
                        },
                        "due_date": {"type": "string", "description": "Due date (ISO 8601 format)"},
                        "time_estimate": {
                            "type": "string",
                            "description": "Time estimate (e.g., '2h 30m')",
                        },
                    },
                    "required": ["title"],
                },
            ),
            Tool(
                name="get_task",
                description="Get task details by ID (supports various ID formats including project codes)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID, custom ID (e.g., gh-123), or URL",
                        },
                        "include_subtasks": {
                            "type": "boolean",
                            "description": "Include subtasks in response",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="update_task",
                description="Update task properties",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "title": {"type": "string", "description": "New title"},
                        "description": {"type": "string", "description": "New description"},
                        "status": {"type": "string", "description": "New status"},
                        "priority": {"type": "integer", "description": "New priority"},
                        "due_date": {"type": "string", "description": "New due date"},
                        "assignees_add": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "User IDs to add as assignees",
                        },
                        "assignees_remove": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "User IDs to remove as assignees",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="delete_task",
                description="Delete a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to delete"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="list_tasks",
                description="List tasks in a list, folder, or space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "list_id": {"type": "string", "description": "List ID"},
                        "folder_id": {"type": "string", "description": "Folder ID"},
                        "space_id": {"type": "string", "description": "Space ID"},
                        "statuses": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by statuses",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Filter by assignee IDs",
                        },
                        "include_closed": {
                            "type": "boolean",
                            "description": "Include closed tasks",
                        },
                    },
                },
            ),
            Tool(
                name="search_tasks",
                description="Search tasks across workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "statuses": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by statuses",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Filter by assignee IDs",
                        },
                    },
                },
            ),
            Tool(
                name="get_subtasks",
                description="Get all subtasks of a parent task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_task_id": {"type": "string", "description": "Parent task ID"},
                    },
                    "required": ["parent_task_id"],
                },
            ),
            Tool(
                name="get_task_comments",
                description="Get comments on a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="create_task_comment",
                description="Create a comment on a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "comment_text": {"type": "string", "description": "Comment text"},
                        "assignee": {
                            "type": "integer",
                            "description": "User ID to assign (optional)",
                        },
                        "notify_all": {
                            "type": "boolean",
                            "description": "Notify all assignees (default: true)",
                        },
                    },
                    "required": ["task_id", "comment_text"],
                },
            ),
            Tool(
                name="get_task_status",
                description="Get current status of a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="update_task_status",
                description="Update task status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "status": {"type": "string", "description": "New status"},
                    },
                    "required": ["task_id", "status"],
                },
            ),
            Tool(
                name="get_assignees",
                description="Get assignees of a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="assign_task",
                description="Assign users to a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "User IDs to assign",
                        },
                    },
                    "required": ["task_id", "user_ids"],
                },
            ),
            Tool(
                name="list_spaces",
                description="List all spaces in workspace",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_folders",
                description="List folders in a space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_id": {"type": "string", "description": "Space ID"},
                    },
                    "required": ["space_id"],
                },
            ),
            Tool(
                name="list_lists",
                description="List all lists in a folder or space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Folder ID"},
                        "space_id": {"type": "string", "description": "Space ID"},
                    },
                },
            ),
            Tool(
                name="find_list_by_name",
                description="Find a list by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "List name to search for"},
                        "space_id": {"type": "string", "description": "Space ID to search in"},
                    },
                    "required": ["name"],
                },
            ),
            # Bulk operations
            Tool(
                name="bulk_update_tasks",
                description="Update multiple tasks at once",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs to update",
                        },
                        "updates": {
                            "type": "object",
                            "description": "Updates to apply (status, priority, assignees, etc.)",
                        },
                    },
                    "required": ["task_ids", "updates"],
                },
            ),
            Tool(
                name="bulk_move_tasks",
                description="Move multiple tasks to a different list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs to move",
                        },
                        "target_list_id": {"type": "string", "description": "Target list ID"},
                    },
                    "required": ["task_ids", "target_list_id"],
                },
            ),
            # Time tracking
            Tool(
                name="get_time_tracked",
                description="Get time tracked for tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID"},
                        "start_date": {"type": "string", "description": "Start date (ISO 8601)"},
                        "end_date": {"type": "string", "description": "End date (ISO 8601)"},
                    },
                },
            ),
            Tool(
                name="log_time",
                description="Log time spent on a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "duration": {"type": "string", "description": "Duration (e.g., '2h 30m')"},
                        "description": {"type": "string", "description": "Optional description"},
                    },
                    "required": ["task_id", "duration"],
                },
            ),
            # Templates
            Tool(
                name="create_task_from_template",
                description="Create a task from a template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_name": {"type": "string", "description": "Template name"},
                        "customizations": {
                            "type": "object",
                            "description": "Customizations to apply to template",
                        },
                        "list_id": {"type": "string", "description": "List ID for the new task"},
                    },
                    "required": ["template_name", "list_id"],
                },
            ),
            Tool(
                name="create_task_chain",
                description="Create a chain of dependent tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "time_estimate": {"type": "string"},
                                },
                            },
                            "description": "List of tasks to create in sequence",
                        },
                        "list_id": {"type": "string", "description": "List ID for the tasks"},
                        "auto_link": {
                            "type": "boolean",
                            "description": "Automatically link tasks as dependencies",
                        },
                    },
                    "required": ["tasks", "list_id"],
                },
            ),
            # Docs management
            Tool(
                name="create_doc",
                description="Create a new document in a folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Folder ID"},
                        "title": {"type": "string", "description": "Document title"},
                        "content": {"type": "string", "description": "Document content"},
                    },
                    "required": ["folder_id", "title", "content"],
                },
            ),
            Tool(
                name="get_doc",
                description="Get a document by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string", "description": "Document ID"},
                    },
                    "required": ["doc_id"],
                },
            ),
            Tool(
                name="update_doc",
                description="Update an existing document",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string", "description": "Document ID"},
                        "title": {"type": "string", "description": "New title"},
                        "content": {"type": "string", "description": "New content"},
                    },
                    "required": ["doc_id"],
                },
            ),
            Tool(
                name="list_docs",
                description="List documents in a folder or space",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Folder ID"},
                        "space_id": {"type": "string", "description": "Space ID"},
                    },
                },
            ),
            Tool(
                name="search_docs",
                description="Search documents across workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "workspace_id": {"type": "string", "description": "Workspace ID"},
                    },
                },
            ),
            # Analytics
            Tool(
                name="get_team_workload",
                description="Get workload distribution across team members",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_id": {"type": "string", "description": "Space ID"},
                        "include_completed": {
                            "type": "boolean",
                            "description": "Include completed tasks in analysis",
                        },
                    },
                    "required": ["space_id"],
                },
            ),
            Tool(
                name="get_task_analytics",
                description="Get analytics for tasks (velocity, completion rate, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_id": {"type": "string", "description": "Space ID"},
                        "period_days": {
                            "type": "integer",
                            "description": "Period in days to analyze",
                        },
                    },
                    "required": ["space_id"],
                },
            ),
            # User management tools
            Tool(
                name="list_users",
                description="List all users in the workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "Workspace ID (optional, uses default if not provided)",
                        },
                    },
                },
            ),
            Tool(
                name="get_current_user",
                description="Get details of the currently authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="find_user_by_name",
                description="Find a user by name or email",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name or email to search for",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "Workspace ID (optional, uses default if not provided)",
                        },
                    },
                    "required": ["name"],
                },
            ),
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool by name with arguments."""
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        try:
            result = await self._tools[name](**arguments)
            return json.dumps(result, indent=2, default=str)
        except ClickUpAPIError as e:
            logger.error(f"ClickUp API error in {name}: {e}")
            return json.dumps({"error": str(e), "type": "api_error"})
        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)
            return json.dumps({"error": str(e), "type": "internal_error"})

    # Tool implementations

    async def _resolve_task_id(self, task_id: str, include_subtasks: bool = False) -> Task:
        """Smart task ID resolution that handles both internal and custom IDs."""
        # Parse task ID to determine if it might be a custom ID
        parsed_id, custom_type = parse_task_id(task_id, self.client.config.id_patterns)

        # Try direct lookup first (works for both internal and custom IDs)
        try:
            return await self.client.get_task(parsed_id, include_subtasks=include_subtasks)
        except ClickUpAPIError as direct_error:
            # If it might be a custom ID, try with custom_task_ids=true
            if custom_type or "-" in parsed_id:
                try:
                    team_id = (
                        self.client.config.default_team_id
                        or self.client.config.default_workspace_id
                    )
                    return await self.client.get_task(
                        parsed_id,
                        include_subtasks=include_subtasks,
                        custom_task_ids=True,
                        team_id=team_id,
                    )
                except ClickUpAPIError as custom_error:
                    # If both fail, try search as final fallback
                    try:
                        tasks = await self.client.search_tasks(query=task_id)
                        if not tasks:
                            raise ClickUpAPIError(f"Task '{task_id}' not found")

                        # Find exact match by custom_id or use first result
                        for task in tasks:
                            if hasattr(task, "custom_id") and task.custom_id == task_id:
                                return task
                        return tasks[0]
                    except ClickUpAPIError:
                        # Re-raise the most relevant error
                        raise (custom_error if custom_type else direct_error) from None
            else:
                # Not a custom ID pattern, re-raise the original error
                raise direct_error

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        list_name: Optional[str] = None,
        list_id: Optional[str] = None,
        assignees: Optional[List[int]] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None,
        time_estimate: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new task."""
        # Find list ID if name provided
        if not list_id and not list_name:
            raise ValueError("Either list_id or list_name must be provided")

        if not list_id:
            lst = await self.client.find_list_by_name(list_name)
            if not lst:
                return {"error": f"List '{list_name}' not found"}
            list_id = lst.id

        # Build task request
        task_request = CreateTaskRequest(name=title)

        if description:
            task_request.description = description
        if assignees:
            task_request.assignees = assignees
        if priority:
            task_request.priority = priority
        if due_date:
            # Parse ISO date to unix timestamp
            dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            task_request.due_date = int(dt.timestamp() * 1000)
            task_request.due_date_time = True
        if time_estimate:
            task_request.time_estimate = parse_duration(time_estimate)

        # Create task
        task = await self.client.create_task(list_id, task_request)

        result = {
            "id": task.id,
            "name": task.name,
            "status": task.status.status,
            "url": format_task_url(task.id),
            "list": task.list.get("name", "Unknown"),
            "created": True,
        }

        if task.custom_id:
            result["custom_id"] = task.custom_id

        return result

    async def get_task(
        self,
        task_id: str,
        include_subtasks: bool = False,
    ) -> Dict[str, Any]:
        """Get task details."""
        try:
            task = await self._resolve_task_id(task_id, include_subtasks)
        except ClickUpAPIError as e:
            return {"error": f"Failed to get task '{task_id}': {e!s}"}

        result = {
            "id": task.id,
            "name": task.name,
            "description": task.description or "",
            "status": task.status.status,
            "priority": task.priority.value if task.priority else None,
            "assignees": [{"id": u.id, "username": u.username} for u in task.assignees],
            "creator": {"id": task.creator.id, "username": task.creator.username},
            "list": task.list.get("name", "Unknown"),
            "space": task.space.get("name", "Unknown"),
            "url": format_task_url(task.id),
            "tags": task.tags,
        }

        if task.custom_id:
            result["custom_id"] = task.custom_id

        if task.due_date:
            result["due_date"] = task.due_date.isoformat()

        if task.time_estimate:
            result["time_estimate"] = task.time_estimate // 1000 // 60  # Convert to minutes

        if task.time_spent:
            result["time_spent"] = task.time_spent // 1000 // 60  # Convert to minutes

        if include_subtasks and task.parent:
            # Fetch subtasks
            subtasks = await self.get_subtasks(task.parent)
            result["subtasks"] = subtasks

        return result

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None,
        assignees_add: Optional[List[int]] = None,
        assignees_remove: Optional[List[int]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update task properties."""
        try:
            # First resolve the task to get the internal ID
            resolved_task = await self._resolve_task_id(task_id)
            parsed_id = resolved_task.id
        except ClickUpAPIError as e:
            return {"error": f"Failed to resolve task '{task_id}': {e!s}"}

        update_request = UpdateTaskRequest()

        if title:
            update_request.name = title
        if description is not None:
            update_request.description = description
        if status:
            update_request.status = status
        if priority:
            update_request.priority = priority
        if due_date:
            dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            update_request.due_date = int(dt.timestamp() * 1000)
            update_request.due_date_time = True

        if assignees_add or assignees_remove:
            update_request.assignees = {}
            if assignees_add:
                update_request.assignees["add"] = assignees_add
            if assignees_remove:
                update_request.assignees["rem"] = assignees_remove

        task = await self.client.update_task(parsed_id, update_request)

        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.status,
            "updated": True,
        }

    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task."""
        try:
            # First resolve the task to get the internal ID
            task = await self._resolve_task_id(task_id)
            await self.client.delete_task(task.id)
            return {"id": task.id, "deleted": True}
        except ClickUpAPIError as e:
            return {"error": f"Failed to delete task '{task_id}': {e!s}"}

    async def list_tasks(
        self,
        list_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        assignees: Optional[List[int]] = None,
        include_closed: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List tasks with filters."""
        tasks = await self.client.get_tasks(
            list_id=list_id,
            folder_id=folder_id,
            space_id=space_id,
            statuses=statuses,
            assignees=assignees,
            include_closed=include_closed,
        )

        return {
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.status,
                    "assignees": [u.username for u in task.assignees],
                    "url": format_task_url(task.id),
                }
                for task in tasks
            ],
            "count": len(tasks),
        }

    async def search_tasks(
        self,
        query: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        assignees: Optional[List[int]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Search tasks."""
        tasks = await self.client.search_tasks(
            query=query,
            statuses=statuses,
            assignees=assignees,
        )

        return {
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.status,
                    "list": task.list.get("name", "Unknown"),
                    "space": task.space.get("name", "Unknown"),
                    "url": format_task_url(task.id),
                }
                for task in tasks
            ],
            "count": len(tasks),
        }

    async def get_subtasks(self, parent_task_id: str) -> Dict[str, Any]:
        """Get subtasks of a parent task."""
        try:
            # First resolve the task to get the internal ID
            task = await self._resolve_task_id(parent_task_id)
            # Use the client's proper subtasks method
            subtasks = await self.client.get_subtasks(task.id)

            return {
                "parent_id": task.id,
                "subtasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "status": task.status.status,
                        "assignees": [u.username for u in task.assignees],
                        "url": format_task_url(task.id),
                        "custom_id": task.custom_id if task.custom_id else None,
                    }
                    for task in subtasks
                ],
                "count": len(subtasks),
            }
        except Exception as e:
            return {"error": f"Failed to get subtasks for '{parent_task_id}': {e!s}"}

    async def get_task_comments(self, task_id: str) -> Dict[str, Any]:
        """Get task comments."""
        try:
            # First resolve the task to get the internal ID
            task = await self._resolve_task_id(task_id)
            comments = await self.client.get_task_comments(task.id)
        except ClickUpAPIError as e:
            return {"error": f"Failed to get comments for task '{task_id}': {e!s}"}

        return {
            "task_id": task.id,
            "comments": [
                {
                    "id": comment["id"],
                    "text": comment["comment_text"],
                    "user": comment["user"]["username"],
                    "date": comment["date"],
                }
                for comment in comments
            ],
            "count": len(comments),
        }

    async def create_task_comment(
        self,
        task_id: str,
        comment_text: str,
        assignee: Optional[int] = None,
        notify_all: bool = True,
    ) -> Dict[str, Any]:
        """Create a comment on a task."""
        try:
            # First resolve the task to get the internal ID
            task = await self._resolve_task_id(task_id)
            comment_data = await self.client.create_task_comment(
                task.id, comment_text, assignee, notify_all
            )
        except ClickUpAPIError as e:
            return {"error": f"Failed to create comment on task '{task_id}': {e!s}"}

        return {
            "task_id": task.id,
            "comment_id": comment_data.get("id"),
            "comment_text": comment_text,
            "created": True,
            "notify_all": notify_all,
        }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status."""
        try:
            task = await self._resolve_task_id(task_id)
        except ClickUpAPIError as e:
            return {"error": f"Failed to get task status for '{task_id}': {e!s}"}

        return {
            "task_id": task.id,
            "status": task.status.status,
            "status_color": task.status.color,
            "status_type": task.status.type,
        }

    async def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """Update task status."""
        try:
            # First resolve the task to get the internal ID
            resolved_task = await self._resolve_task_id(task_id)
            update_request = UpdateTaskRequest(status=status)
            task = await self.client.update_task(resolved_task.id, update_request)
        except ClickUpAPIError as e:
            return {"error": f"Failed to update task status for '{task_id}': {e!s}"}

        return {
            "task_id": task.id,
            "status": task.status.status,
            "updated": True,
        }

    async def get_assignees(self, task_id: str) -> Dict[str, Any]:
        """Get task assignees."""
        try:
            task = await self._resolve_task_id(task_id)
        except ClickUpAPIError as e:
            return {"error": f"Failed to get assignees for task '{task_id}': {e!s}"}

        return {
            "task_id": task.id,
            "assignees": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "initials": user.initials,
                }
                for user in task.assignees
            ],
            "count": len(task.assignees),
        }

    async def assign_task(self, task_id: str, user_ids: List[int]) -> Dict[str, Any]:
        """Assign users to task."""
        try:
            # First resolve the task to get the internal ID
            resolved_task = await self._resolve_task_id(task_id)
            update_request = UpdateTaskRequest(assignees={"add": user_ids})
            task = await self.client.update_task(resolved_task.id, update_request)
        except ClickUpAPIError as e:
            return {"error": f"Failed to assign users to task '{task_id}': {e!s}"}

        return {
            "task_id": task.id,
            "assignees": [u.username for u in task.assignees],
            "updated": True,
        }

    async def list_spaces(self) -> Dict[str, Any]:
        """List all spaces."""
        spaces = await self.client.get_spaces()

        return {
            "spaces": [
                {
                    "id": space.id,
                    "name": space.name,
                    "private": space.private,
                    "color": space.color,
                }
                for space in spaces
            ],
            "count": len(spaces),
        }

    async def list_folders(self, space_id: str) -> Dict[str, Any]:
        """List folders in space."""
        folders = await self.client.get_folders(space_id)

        return {
            "space_id": space_id,
            "folders": [
                {
                    "id": folder.id,
                    "name": folder.name,
                    "task_count": folder.task_count,
                    "lists": [
                        {
                            "id": lst.id,
                            "name": lst.name,
                            "task_count": lst.task_count,
                        }
                        for lst in folder.lists
                    ],
                }
                for folder in folders
            ],
            "count": len(folders),
        }

    async def list_lists(
        self,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all lists."""
        if not folder_id and not space_id:
            # List all lists from all spaces
            spaces = await self.client.get_spaces()
            all_lists = []
            for space in spaces:
                lists = await self.client.get_lists(space_id=space.id)
                all_lists.extend(lists)
        else:
            all_lists = await self.client.get_lists(folder_id=folder_id, space_id=space_id)

        return {
            "lists": [
                {
                    "id": lst.id,
                    "name": lst.name,
                    "space": lst.space.get("name", "Unknown"),
                    "folder": lst.folder.get("name") if lst.folder else None,
                }
                for lst in all_lists
            ],
            "count": len(all_lists),
        }

    async def find_list_by_name(self, name: str, space_id: Optional[str] = None) -> Dict[str, Any]:
        """Find list by name."""
        lst = await self.client.find_list_by_name(name, space_id)

        if not lst:
            return {"error": f"List '{name}' not found"}

        return {
            "id": lst.id,
            "name": lst.name,
            "space": lst.space.get("name", "Unknown"),
            "folder": lst.folder.get("name") if lst.folder else None,
            "found": True,
        }

    # Bulk operations

    async def bulk_update_tasks(
        self, task_ids: List[str], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update multiple tasks at once."""
        results = {"updated": [], "failed": []}

        # Convert updates dict to UpdateTaskRequest format
        update_request = UpdateTaskRequest()
        if "status" in updates:
            update_request.status = updates["status"]
        if "priority" in updates:
            update_request.priority = updates["priority"]
        if "assignees_add" in updates:
            update_request.assignees = {"add": updates["assignees_add"]}
        if "assignees_remove" in updates:
            if update_request.assignees is None:
                update_request.assignees = {}
            update_request.assignees["rem"] = updates["assignees_remove"]

        for task_id in task_ids:
            try:
                # Resolve each task ID to get the internal ID
                resolved_task = await self._resolve_task_id(task_id)
                await self.client.update_task(resolved_task.id, update_request)
                results["updated"].append(task_id)
            except Exception as e:
                results["failed"].append({"task_id": task_id, "error": str(e)})

        return results

    async def bulk_move_tasks(self, task_ids: List[str], target_list_id: str) -> Dict[str, Any]:
        """Move multiple tasks to a different list."""
        results = {"moved": [], "failed": []}

        for task_id in task_ids:
            try:
                # Resolve each task ID to get the internal ID
                resolved_task = await self._resolve_task_id(task_id)
                # Moving tasks requires updating the list property
                await self.client._request(
                    "PUT", f"/task/{resolved_task.id}", json={"list": target_list_id}
                )
                results["moved"].append(task_id)
            except Exception as e:
                results["failed"].append({"task_id": task_id, "error": str(e)})

        return results

    # Time tracking

    async def get_time_tracked(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get time tracked for tasks."""
        # If no dates provided, default to last 7 days
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()

        start_ts = int(datetime.fromisoformat(start_date.replace("Z", "+00:00")).timestamp() * 1000)
        end_ts = int(datetime.fromisoformat(end_date.replace("Z", "+00:00")).timestamp() * 1000)

        # Get time entries
        params = {
            "start_date": str(start_ts),
            "end_date": str(end_ts),
        }
        if user_id:
            params["assignee"] = str(user_id)

        workspace_id = self.client.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.client.get_workspaces()
            workspace_id = workspaces[0].id

        data = await self.client._request(
            "GET", f"/team/{workspace_id}/time_entries", params=params
        )

        total_ms = sum(entry.get("duration", 0) for entry in data.get("data", []))
        total_hours = total_ms / (1000 * 60 * 60)

        return {
            "total_milliseconds": total_ms,
            "total_hours": round(total_hours, 2),
            "entries": len(data.get("data", [])),
            "period": {
                "start": start_date,
                "end": end_date,
            },
        }

    async def log_time(
        self,
        task_id: str,
        duration: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log time spent on a task."""
        try:
            # First resolve the task to get the internal ID
            resolved_task = await self._resolve_task_id(task_id)
            duration_ms = parse_duration(duration)
        except ClickUpAPIError as e:
            return {"error": f"Failed to resolve task '{task_id}': {e!s}"}

        # Create time entry
        payload = {
            "duration": duration_ms,
            "task_id": resolved_task.id,
        }
        if description:
            payload["description"] = description

        workspace_id = self.client.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.client.get_workspaces()
            workspace_id = workspaces[0].id

        await self.client._request("POST", f"/team/{workspace_id}/time_entries", json=payload)

        return {
            "logged": True,
            "duration": duration,
            "duration_ms": duration_ms,
            "task_id": resolved_task.id,
        }

    # Templates and chains

    async def create_task_from_template(
        self,
        template_name: str,
        list_id: str,
        customizations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a task from a template."""
        # Define common templates
        templates = {
            "bug_report": {
                "name": "Bug Report: {title}",
                "description": "## Description\n\n## Steps to Reproduce\n1. \n2. \n3. \n\n## Expected Behavior\n\n## Actual Behavior\n\n## Environment\n",
                "priority": 2,
                "tags": ["bug"],
            },
            "feature_request": {
                "name": "Feature: {title}",
                "description": "## Feature Description\n\n## User Story\nAs a [user type], I want [goal] so that [benefit].\n\n## Acceptance Criteria\n- [ ] \n- [ ] \n\n## Technical Notes\n",
                "priority": 3,
                "tags": ["feature"],
            },
            "code_review": {
                "name": "Code Review: {title}",
                "description": "## PR Link\n\n## Changes Summary\n\n## Checklist\n- [ ] Code follows style guidelines\n- [ ] Tests added/updated\n- [ ] Documentation updated\n- [ ] No console errors\n",
                "priority": 2,
                "tags": ["review"],
            },
        }

        template = templates.get(template_name)
        if not template:
            return {"error": f"Template '{template_name}' not found"}

        # Apply customizations
        task_data = template.copy()
        if customizations:
            task_data["name"] = task_data["name"].format(**customizations)
            task_data.update(customizations)

        # Create task
        task_request = CreateTaskRequest(
            name=task_data["name"],
            description=task_data.get("description"),
            priority=task_data.get("priority"),
            tags=task_data.get("tags"),
        )

        task = await self.client.create_task(list_id, task_request)

        return {
            "id": task.id,
            "name": task.name,
            "template": template_name,
            "url": format_task_url(task.id),
        }

    async def create_task_chain(
        self,
        tasks: List[Dict[str, Any]],
        list_id: str,
        auto_link: bool = True,
    ) -> Dict[str, Any]:
        """Create a chain of dependent tasks."""
        created_tasks = []

        for i, task_data in enumerate(tasks):
            # Create task
            task_request = CreateTaskRequest(
                name=task_data["title"],
                description=task_data.get("description"),
            )

            # Parse time estimate if provided
            if "time_estimate" in task_data:
                task_request.time_estimate = parse_duration(task_data["time_estimate"])

            # Link to previous task if auto_link is enabled
            if auto_link and i > 0 and created_tasks:
                task_request.links_to = created_tasks[-1]["id"]

            task = await self.client.create_task(list_id, task_request)
            created_tasks.append(
                {
                    "id": task.id,
                    "name": task.name,
                    "url": format_task_url(task.id),
                }
            )

        return {
            "created": len(created_tasks),
            "tasks": created_tasks,
            "linked": auto_link,
        }

    # Docs management

    async def create_doc(self, folder_id: str, title: str, content: str) -> Dict[str, Any]:
        """Create a document."""
        doc_req = CreateDocRequest(name=title, content=content)
        doc = await self.client.create_doc(folder_id, doc_req)
        return {"id": doc.id, "name": doc.name}

    async def get_doc(self, doc_id: str) -> Dict[str, Any]:
        """Get a document."""
        doc = await self.client.get_doc(doc_id)
        return {"id": doc.id, "name": doc.name, "content": doc.content}

    async def update_doc(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a document."""
        req = UpdateDocRequest(name=title, content=content)
        doc = await self.client.update_doc(doc_id, req)
        return {"id": doc.id, "name": doc.name, "updated": True}

    async def list_docs(
        self, folder_id: Optional[str] = None, space_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List documents."""
        docs = await self.client.list_docs(folder_id=folder_id, space_id=space_id)
        return {
            "docs": [{"id": d.id, "name": d.name} for d in docs],
            "count": len(docs),
        }

    async def search_docs(
        self, query: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search documents."""
        docs = await self.client.search_docs(workspace_id=workspace_id, query=query)
        return {
            "docs": [{"id": d.id, "name": d.name} for d in docs],
            "count": len(docs),
        }

    # Analytics

    async def get_team_workload(
        self, space_id: str, include_completed: bool = False
    ) -> Dict[str, Any]:
        """Get workload distribution across team members."""
        # Get all tasks in the space
        tasks = await self.client.get_tasks(
            space_id=space_id,
            include_closed=include_completed,
        )

        # Group by assignee
        workload = {}
        unassigned_count = 0

        for task in tasks:
            if not task.assignees:
                unassigned_count += 1
            else:
                for assignee in task.assignees:
                    username = assignee.username
                    if username not in workload:
                        workload[username] = {
                            "user_id": assignee.id,
                            "username": username,
                            "task_count": 0,
                            "total_time_estimate": 0,
                            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
                        }

                    workload[username]["task_count"] += 1
                    if task.time_estimate:
                        workload[username]["total_time_estimate"] += task.time_estimate
                    if task.priority:
                        workload[username]["by_priority"][task.priority.value] += 1

        # Convert time estimates to hours
        for user_data in workload.values():
            user_data["total_hours_estimate"] = round(
                user_data["total_time_estimate"] / (1000 * 60 * 60), 2
            )

        return {
            "space_id": space_id,
            "team_workload": list(workload.values()),
            "unassigned_tasks": unassigned_count,
            "total_tasks": len(tasks),
        }

    async def get_task_analytics(self, space_id: str, period_days: int = 30) -> Dict[str, Any]:
        """Get analytics for tasks."""
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Get tasks created in period
        tasks = await self.client.search_tasks(
            query="",
            date_created_gt=int(start_date.timestamp() * 1000),
            date_created_lt=int(end_date.timestamp() * 1000),
        )

        # Calculate metrics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status.type == "closed")

        # Calculate average completion time
        completion_times = []
        for task in tasks:
            if task.date_closed and task.date_created:
                time_to_complete = (task.date_closed - task.date_created).total_seconds() / 3600
                completion_times.append(time_to_complete)

        avg_completion_time = (
            sum(completion_times) / len(completion_times) if completion_times else 0
        )

        # Tasks by priority
        by_priority = {1: 0, 2: 0, 3: 0, 4: 0}
        for task in tasks:
            if task.priority:
                by_priority[task.priority.value] += 1

        return {
            "space_id": space_id,
            "period_days": period_days,
            "metrics": {
                "total_tasks_created": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": round(
                    completed_tasks / total_tasks * 100 if total_tasks > 0 else 0, 2
                ),
                "avg_completion_hours": round(avg_completion_time, 2),
                "tasks_per_day": round(total_tasks / period_days, 2),
            },
            "by_priority": by_priority,
        }

    # User management

    async def list_users(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """List all users in the workspace."""
        members = await self.client.get_workspace_members(workspace_id)

        return {
            "users": [
                {
                    "id": member.get("id"),
                    "username": member.get("username"),
                    "email": member.get("email"),
                    "initials": member.get("initials"),
                    "color": member.get("color"),
                    "profilePicture": member.get("profilePicture"),
                }
                for member in members
            ],
            "count": len(members),
        }

    async def get_current_user(self) -> Dict[str, Any]:
        """Get details of the currently authenticated user."""
        user = await self.client.get_current_user()

        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "initials": user.get("initials"),
            "color": user.get("color"),
            "profilePicture": user.get("profilePicture"),
            "role": user.get("role"),
        }

    async def find_user_by_name(
        self, name: str, workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find a user by name or email."""
        members = await self.client.get_workspace_members(workspace_id)

        # Search by username or email (case-insensitive)
        name_lower = name.lower()
        matches = []

        for member in members:
            username = member.get("username", "").lower()
            email = member.get("email", "").lower()

            if name_lower in username or name_lower in email:
                matches.append(
                    {
                        "id": member.get("id"),
                        "username": member.get("username"),
                        "email": member.get("email"),
                        "initials": member.get("initials"),
                        "color": member.get("color"),
                        "profilePicture": member.get("profilePicture"),
                    }
                )

        if not matches:
            return {"error": f"No user found matching '{name}'", "matches": []}

        return {
            "matches": matches,
            "count": len(matches),
            "found": True,
        }
