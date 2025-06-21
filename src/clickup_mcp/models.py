"""Pydantic models for ClickUp entities."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union
from typing import List as ListType

from pydantic import BaseModel


class TaskPriority(Enum):
    """Task priority levels."""

    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class TaskStatus(BaseModel):
    """Task status model."""

    id: str
    status: str
    color: str
    orderindex: int
    type: str


class User(BaseModel):
    """User model."""

    id: int
    username: str
    email: Optional[str] = None
    color: Optional[str] = None
    initials: Optional[str] = None
    profile_picture: Optional[str] = None


class CustomField(BaseModel):
    """Custom field model."""

    id: str
    name: str
    type: str
    type_config: Dict[str, Any] = {}
    value: Optional[Union[str, int, float, bool, ListType[Any], Dict[str, Any]]] = None


class Task(BaseModel):
    """Task model."""

    id: str
    custom_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: TaskStatus
    orderindex: Optional[float] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    date_closed: Optional[datetime] = None
    archived: bool = False
    creator: User
    assignees: ListType[User] = []
    tags: ListType[str] = []
    parent: Optional[str] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    time_estimate: Optional[int] = None
    time_spent: Optional[int] = None
    custom_fields: ListType[CustomField] = []
    list: Dict[str, Any]
    folder: Dict[str, Any]
    space: Dict[str, Any]
    url: str


class List(BaseModel):
    """List model."""

    id: str
    name: str
    orderindex: int
    status: Optional[Dict[str, Any]] = None
    priority: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None
    task_count: Optional[int] = None
    due_date: Optional[Dict[str, Any]] = None
    start_date: Optional[Dict[str, Any]] = None
    folder: Dict[str, Any]
    space: Dict[str, Any]
    archived: bool = False


class Folder(BaseModel):
    """Folder model."""

    id: str
    name: str
    orderindex: int
    override_statuses: bool = False
    hidden: bool = False
    space: Dict[str, Any]
    task_count: Optional[int] = None
    lists: ListType["List"] = []
    archived: bool = False


class Space(BaseModel):
    """Space model."""

    id: str
    name: str
    private: bool = False
    color: Optional[str] = None
    avatar: Optional[str] = None
    admin_can_manage: bool = False
    statuses: ListType[TaskStatus] = []
    multiple_assignees: bool = True
    features: Dict[str, Any] = {}
    archived: bool = False


class Comment(BaseModel):
    """Comment model."""

    id: str
    comment_text: str
    user: User
    date: datetime
    resolved: bool = False
    assignee: Optional[User] = None


class Workspace(BaseModel):
    """Workspace/Team model."""

    id: str
    name: str
    color: str
    avatar: Optional[str] = None
    members: ListType[User] = []


class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""

    name: str
    description: Optional[str] = None
    assignees: Optional[ListType[int]] = None
    tags: Optional[ListType[str]] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[int] = None  # Unix timestamp in milliseconds
    due_date_time: Optional[bool] = False
    time_estimate: Optional[int] = None  # Time in milliseconds
    start_date: Optional[int] = None  # Unix timestamp in milliseconds
    start_date_time: Optional[bool] = False
    notify_all: Optional[bool] = True
    parent: Optional[str] = None
    links_to: Optional[str] = None
    custom_fields: Optional[ListType[Dict[str, Any]]] = None


class UpdateTaskRequest(BaseModel):
    """Request model for updating a task."""

    name: Optional[str] = None
    description: Optional[str] = None
    assignees: Optional[Dict[str, ListType[int]]] = None  # {"add": [123], "rem": [456]}
    status: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[int] = None
    due_date_time: Optional[bool] = None
    time_estimate: Optional[int] = None
    start_date: Optional[int] = None
    start_date_time: Optional[bool] = None
    archived: Optional[bool] = None
    parent: Optional[str] = None
