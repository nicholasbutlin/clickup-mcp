"""ClickUp API client implementation."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import Config
from .models import CreateTaskRequest, Folder, Space, Task, UpdateTaskRequest, Workspace
from .models import List as ClickUpList

logger = logging.getLogger(__name__)


class ClickUpAPIError(Exception):
    """ClickUp API error."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ClickUpClient:
    """Client for interacting with ClickUp API."""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, config: Config) -> None:
        """Initialize the client with configuration."""
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=config.headers,
            timeout=30.0,
        )

    async def __aenter__(self) -> "ClickUpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make an API request and handle errors."""
        try:
            response = await self.client.request(method, path, **kwargs)

            if response.status_code >= 400:
                error_msg = f"API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "err" in error_data:
                        error_msg = f"{error_msg} - {error_data['err']}"
                except Exception:
                    error_msg = f"{error_msg} - {response.text}"

                raise ClickUpAPIError(error_msg, response.status_code)

            return response.json()

        except httpx.TimeoutException as e:
            raise ClickUpAPIError("Request timed out") from e
        except httpx.RequestError as e:
            raise ClickUpAPIError(f"Request failed: {e!s}") from e

    # User endpoints

    async def get_current_user(self) -> Dict[str, Any]:
        """Get the current authenticated user."""
        data = await self._request("GET", "/user")
        return data.get("user", {})

    async def get_workspace_members(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all members of a workspace.

        Note: This endpoint requires the workspace to be on an Enterprise plan
        for full functionality. For non-Enterprise plans, it may return limited data.
        """
        workspace_id = workspace_id or self.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                raise ClickUpAPIError("No workspaces found")
            workspace_id = workspaces[0].id

        # First try the groups endpoint which is more widely available
        try:
            data = await self._request("GET", "/group")
            groups = data.get("groups", [])

            # Extract unique members from all groups
            members_dict = {}
            for group in groups:
                for member in group.get("members", []):
                    user_id = member.get("id")
                    if user_id and user_id not in members_dict:
                        members_dict[user_id] = member

            return list(members_dict.values())
        except ClickUpAPIError:
            # Fallback: Try to get members from tasks/lists if groups endpoint fails
            # This is a workaround for non-Enterprise workspaces
            logger.warning("Groups endpoint failed, falling back to workspace team endpoint")

            # Try the team endpoint which might have member information
            try:
                data = await self._request("GET", f"/team/{workspace_id}")
                team = data.get("team", {})
                members = team.get("members", [])
                return members
            except ClickUpAPIError:
                logger.warning("Unable to fetch workspace members directly")
                return []

    # Workspace/Team endpoints

    async def get_workspaces(self) -> List[Workspace]:
        """Get all workspaces/teams."""
        data = await self._request("GET", "/team")
        teams = data.get("teams", [])
        return [Workspace(**team) for team in teams]

    # Space endpoints

    async def get_spaces(self, workspace_id: Optional[str] = None) -> List[Space]:
        """Get all spaces in a workspace."""
        workspace_id = workspace_id or self.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                raise ClickUpAPIError("No workspaces found")
            workspace_id = workspaces[0].id

        data = await self._request("GET", f"/team/{workspace_id}/space")
        spaces = data.get("spaces", [])
        return [Space(**space) for space in spaces]

    async def get_space(self, space_id: str) -> Space:
        """Get a specific space."""
        data = await self._request("GET", f"/space/{space_id}")
        return Space(**data)

    # Folder endpoints

    async def get_folders(self, space_id: str) -> List[Folder]:
        """Get all folders in a space."""
        data = await self._request("GET", f"/space/{space_id}/folder")
        folders = data.get("folders", [])
        return [Folder(**folder) for folder in folders]

    async def get_folder(self, folder_id: str) -> Folder:
        """Get a specific folder."""
        data = await self._request("GET", f"/folder/{folder_id}")
        return Folder(**data)

    # List endpoints

    async def get_lists(
        self,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
    ) -> List[ClickUpList]:
        """Get lists from a folder or space."""
        if folder_id:
            data = await self._request("GET", f"/folder/{folder_id}/list")
        elif space_id:
            data = await self._request("GET", f"/space/{space_id}/list")
        else:
            raise ValueError("Either folder_id or space_id must be provided")

        lists = data.get("lists", [])
        return [ClickUpList(**lst) for lst in lists]

    async def get_list(self, list_id: str) -> ClickUpList:
        """Get a specific list."""
        data = await self._request("GET", f"/list/{list_id}")
        return ClickUpList(**data)

    async def find_list_by_name(
        self,
        name: str,
        space_id: Optional[str] = None,
    ) -> Optional[ClickUpList]:
        """Find a list by name in a space."""
        if not space_id:
            # Search in all spaces if not specified
            spaces = await self.get_spaces()
            for space in spaces:
                result = await self.find_list_by_name(name, space.id)
                if result:
                    return result
            return None

        # Get all lists in the space
        lists = await self.get_lists(space_id=space_id)

        # Also check folders
        folders = await self.get_folders(space_id)
        for folder in folders:
            folder_lists = await self.get_lists(folder_id=folder.id)
            lists.extend(folder_lists)

        # Find by name (case-insensitive)
        name_lower = name.lower()
        for lst in lists:
            if lst.name.lower() == name_lower:
                return lst

        return None

    # Task endpoints

    async def create_task(
        self,
        list_id: str,
        task: CreateTaskRequest,
    ) -> Task:
        """Create a new task."""
        data = await self._request(
            "POST",
            f"/list/{list_id}/task",
            json=task.model_dump(exclude_none=True),
        )
        return Task(**data)

    async def get_task(
        self,
        task_id: str,
        include_subtasks: bool = False,
    ) -> Task:
        """Get a task by ID."""
        params = {}
        if include_subtasks:
            params["include_subtasks"] = "true"

        data = await self._request("GET", f"/task/{task_id}", params=params)
        return Task(**data)

    async def update_task(
        self,
        task_id: str,
        updates: UpdateTaskRequest,
    ) -> Task:
        """Update a task."""
        data = await self._request(
            "PUT",
            f"/task/{task_id}",
            json=updates.model_dump(exclude_none=True),
        )
        return Task(**data)

    async def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        await self._request("DELETE", f"/task/{task_id}")

    async def get_tasks(
        self,
        list_id: Optional[str] = None,
        space_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        archived: bool = False,
        page: int = 0,
        order_by: str = "created",
        statuses: Optional[List[str]] = None,
        assignees: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        include_closed: bool = False,
    ) -> List[Task]:
        """Get tasks with various filters."""
        params: Dict[str, Any] = {
            "archived": str(archived).lower(),
            "page": str(page),
            "order_by": order_by,
            "include_closed": str(include_closed).lower(),
        }

        if statuses:
            params["statuses[]"] = statuses
        if assignees:
            params["assignees[]"] = assignees
        if tags:
            params["tags[]"] = tags

        if list_id:
            path = f"/list/{list_id}/task"
        elif folder_id:
            path = f"/folder/{folder_id}/task"
        elif space_id:
            path = f"/space/{space_id}/task"
        else:
            raise ValueError("One of list_id, folder_id, or space_id must be provided")

        data = await self._request("GET", path, params=params)
        tasks = data.get("tasks", [])
        return [Task(**task) for task in tasks]

    async def search_tasks(
        self,
        workspace_id: Optional[str] = None,
        query: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        assignees: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        date_created_gt: Optional[int] = None,
        date_created_lt: Optional[int] = None,
        date_updated_gt: Optional[int] = None,
        date_updated_lt: Optional[int] = None,
    ) -> List[Task]:
        """Search tasks across the workspace."""
        workspace_id = workspace_id or self.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                raise ClickUpAPIError("No workspaces found")
            workspace_id = workspaces[0].id

        params: Dict[str, Any] = {}

        if query:
            params["query"] = query
        if statuses:
            params["statuses[]"] = statuses
        if assignees:
            params["assignees[]"] = assignees
        if tags:
            params["tags[]"] = tags
        if date_created_gt:
            params["date_created_gt"] = str(date_created_gt)
        if date_created_lt:
            params["date_created_lt"] = str(date_created_lt)
        if date_updated_gt:
            params["date_updated_gt"] = str(date_updated_gt)
        if date_updated_lt:
            params["date_updated_lt"] = str(date_updated_lt)

        data = await self._request(
            "GET",
            f"/team/{workspace_id}/task",
            params=params,
        )
        tasks = data.get("tasks", [])
        return [Task(**task) for task in tasks]

    async def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """Get comments for a task."""
        data = await self._request("GET", f"/task/{task_id}/comment")
        return data.get("comments", [])

    async def create_task_comment(
        self,
        task_id: str,
        comment_text: str,
        assignee: Optional[int] = None,
        notify_all: bool = True,
    ) -> Dict[str, Any]:
        """Create a comment on a task."""
        payload: Dict[str, Any] = {
            "comment_text": comment_text,
            "notify_all": notify_all,
        }
        if assignee:
            payload["assignee"] = assignee

        data = await self._request(
            "POST",
            f"/task/{task_id}/comment",
            json=payload,
        )
        return data
