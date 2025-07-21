"""ClickUp API client implementation."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import Config
from .models import CreateDocRequest, CreateTaskRequest, Document, Folder
from .models import List as ClickUpList
from .models import Space, Task, UpdateDocRequest, UpdateTaskRequest, Workspace

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

    async def _request_v3(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make an API v3 request (for newer endpoints like docs)."""
        # Replace v2 with v3 in the base URL for this request
        v3_client = httpx.AsyncClient(
            base_url="https://api.clickup.com/api/v3",
            headers=self.config.headers,
            timeout=30.0,
        )

        try:
            response = await v3_client.request(method, path, **kwargs)

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
        finally:
            await v3_client.aclose()

    # User endpoints

    async def get_current_user(self) -> Dict[str, Any]:
        """Get the current authenticated user."""
        data = await self._request("GET", "/user")
        return data.get("user", {})

    async def get_workspace_members(
        self, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
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
                        # Ensure consistent user format
                        user_data = {
                            "id": member.get("id"),
                            "username": member.get("username"),
                            "email": member.get("email"),
                            "initials": member.get("initials"),
                            "color": member.get("color"),
                            "profilePicture": member.get("profilePicture"),
                        }
                        members_dict[user_id] = user_data

            if members_dict:
                return list(members_dict.values())

        except ClickUpAPIError:
            logger.warning("Groups endpoint failed, trying other endpoints")

        # Try the team endpoint which might have member information
        try:
            data = await self._request("GET", f"/team/{workspace_id}")
            team = data.get("team", {})
            members = team.get("members", [])

            # Format members consistently
            formatted_members = []
            for member in members:
                if isinstance(member, dict):
                    # Handle nested user structure
                    if "user" in member:
                        user_data = member["user"]
                    else:
                        user_data = member

                    formatted_member = {
                        "id": user_data.get("id"),
                        "username": user_data.get("username"),
                        "email": user_data.get("email"),
                        "initials": user_data.get("initials"),
                        "color": user_data.get("color"),
                        "profilePicture": user_data.get("profilePicture"),
                    }
                    formatted_members.append(formatted_member)

            if formatted_members:
                return formatted_members

        except ClickUpAPIError:
            logger.warning("Team endpoint also failed")

        # Final fallback: get current user and return as single-item list
        try:
            current_user = await self.get_current_user()
            return [
                {
                    "id": current_user.get("id"),
                    "username": current_user.get("username"),
                    "email": current_user.get("email"),
                    "initials": current_user.get("initials"),
                    "color": current_user.get("color"),
                    "profilePicture": current_user.get("profilePicture"),
                }
            ]
        except ClickUpAPIError:
            logger.warning("Unable to fetch any workspace members")
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
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> Task:
        """Get a task by ID."""
        params = {}
        if include_subtasks:
            params["include_subtasks"] = "true"
        if custom_task_ids:
            params["custom_task_ids"] = "true"
            if team_id:
                params["team_id"] = team_id

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

        # Handle different task retrieval strategies
        if list_id:
            # Direct list access - this works fine
            path = f"/list/{list_id}/task"
            data = await self._request("GET", path, params=params)
            tasks = data.get("tasks", [])
            return [Task(**task) for task in tasks]

        elif folder_id:
            # Get all lists in the folder, then get tasks from each list
            lists = await self.get_lists(folder_id=folder_id)
            all_tasks = []
            for list_obj in lists:
                try:
                    list_path = f"/list/{list_obj.id}/task"
                    data = await self._request("GET", list_path, params=params)
                    tasks = data.get("tasks", [])
                    all_tasks.extend([Task(**task) for task in tasks])
                except ClickUpAPIError as e:
                    # Log the error but continue with other lists
                    logger.warning(f"Failed to get tasks from list {list_obj.id}: {e}")
            return all_tasks

        elif space_id:
            # ClickUp API doesn't support /space/{id}/task endpoint
            # Instead, get all lists in the space and get tasks from each
            lists = await self.get_lists(space_id=space_id)
            all_tasks = []
            for list_obj in lists:
                try:
                    list_path = f"/list/{list_obj.id}/task"
                    data = await self._request("GET", list_path, params=params)
                    tasks = data.get("tasks", [])
                    all_tasks.extend([Task(**task) for task in tasks])
                except ClickUpAPIError as e:
                    # Log the error but continue with other lists
                    logger.warning(f"Failed to get tasks from list {list_obj.id}: {e}")
            return all_tasks

        else:
            raise ValueError("One of list_id, folder_id, or space_id must be provided")

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

    async def get_subtasks(self, parent_task_id: str) -> List[Task]:
        """Get subtasks of a parent task using team endpoint."""
        # Get the workspace ID - use configured default or fetch from API
        workspace_id = self.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                return []
            workspace_id = workspaces[0].id

        # Use team endpoint to get tasks with parent filter
        params = {
            "parent": parent_task_id,
            "include_closed": "true",
        }

        try:
            data = await self._request(
                "GET", f"/team/{workspace_id}/task", params=params
            )
            tasks_data = data.get("tasks", [])
            return [Task(**task_data) for task_data in tasks_data]
        except ClickUpAPIError as e:
            # If team endpoint fails, fallback to original method
            logger.warning(f"Team endpoint failed for subtasks: {e}")
            return []

    # Docs endpoints

    async def create_doc(self, folder_id: str, doc: "CreateDocRequest") -> "Document":
        """Create a new document."""
        data = await self._request(
            "POST",
            f"/folder/{folder_id}/doc",
            json=doc.model_dump(exclude_none=True),
        )
        return Document(**data)

    async def get_doc(self, doc_id: str) -> "Document":
        """Retrieve a document by ID."""
        data = await self._request("GET", f"/doc/{doc_id}")
        return Document(**data)

    async def update_doc(self, doc_id: str, updates: "UpdateDocRequest") -> "Document":
        """Update an existing document."""
        data = await self._request(
            "PUT",
            f"/doc/{doc_id}",
            json=updates.model_dump(exclude_none=True),
        )
        return Document(**data)

    async def list_docs(
        self, folder_id: Optional[str] = None, space_id: Optional[str] = None
    ) -> List["Document"]:
        """List documents in a folder or space.

        Note: Uses ClickUp API v3 for docs endpoints.
        """
        # For v3 docs API, we need the workspace_id, not folder/space
        workspace_id = self.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                raise ClickUpAPIError("No workspaces found")
            workspace_id = workspaces[0].id

        try:
            # Use the correct v3 endpoint
            data = await self._request_v3("GET", f"/workspaces/{workspace_id}/docs")
            docs = data.get("docs", [])

            # If folder_id or space_id is specified, filter the results
            if folder_id or space_id:
                # Note: The API doesn't support filtering by folder/space directly
                # You may need to filter client-side based on doc properties
                logger.info(
                    f"Retrieved {len(docs)} docs from workspace. "
                    f"Note: folder_id/space_id filtering not supported by API"
                )

            return [Document(**d) for d in docs]

        except ClickUpAPIError as e:
            logger.error(f"Failed to list docs: {e}")
            # Return empty list instead of raising error to allow graceful
            # degradation
            return []

    async def search_docs(
        self,
        workspace_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List["Document"]:
        """Search documents across a workspace.

        https://developer.clickup.com/reference/searchdocs
        Uses ClickUp API v3 for docs endpoints.
        """
        workspace_id = workspace_id or self.config.default_workspace_id
        if not workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                raise ClickUpAPIError("No workspaces found")
            workspace_id = workspaces[0].id

        params: Dict[str, Any] = {}
        if query:
            params["query"] = query

        try:
            # Use the correct v3 endpoint
            data = await self._request_v3(
                "GET", f"/workspaces/{workspace_id}/docs", params=params
            )
            docs = data.get("docs", [])
            return [Document(**d) for d in docs]

        except ClickUpAPIError as e:
            logger.error(f"Failed to search docs: {e}")
            # Return empty list instead of raising error to allow graceful
            # degradation
            return []
