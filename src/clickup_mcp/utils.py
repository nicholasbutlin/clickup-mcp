"""Utility functions for ClickUp MCP server."""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def parse_task_id(
    task_ref: str, id_patterns: Optional[dict[str, str]] = None
) -> Tuple[str, Optional[str]]:
    """
    Parse various task reference formats.

    Args:
        task_ref: Task reference in various formats
        id_patterns: Custom ID patterns mapping

    Returns:
        Tuple of (task_id, custom_id_type)

    Examples:
        - "abc123def" -> ("abc123def", None)
        - "gh-123" -> ("gh-123", "gh")
        - "#123" -> ("123", None)
        - "https://app.clickup.com/t/abc123" -> ("abc123", None)
    """
    task_ref = task_ref.strip()

    # Handle ClickUp URLs
    if task_ref.startswith(("http://", "https://")):
        parsed = urlparse(task_ref)
        # Extract task ID from path like /t/abc123
        match = re.search(r"/t/([a-zA-Z0-9]+)", parsed.path)
        if match:
            return match.group(1), None

    # Handle #123 format
    if task_ref.startswith("#"):
        return task_ref[1:], None

    # Handle custom ID patterns (e.g., gh-123, cs-456)
    if id_patterns and "-" in task_ref:
        prefix = task_ref.split("-")[0]
        if prefix in id_patterns:
            return task_ref, prefix

    # Default: assume it's a direct task ID
    return task_ref, None


def format_task_url(task_id: str) -> str:
    """Generate ClickUp task URL."""
    return f"https://app.clickup.com/t/{task_id}"


def format_duration(milliseconds: Optional[int]) -> str:
    """Format duration from milliseconds to human-readable string."""
    if not milliseconds:
        return "0m"

    hours = milliseconds // (1000 * 60 * 60)
    minutes = (milliseconds % (1000 * 60 * 60)) // (1000 * 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to milliseconds.

    Examples:
        - "1h" -> 3600000
        - "30m" -> 1800000
        - "1h 30m" -> 5400000
        - "90m" -> 5400000
    """
    duration_str = duration_str.strip().lower()
    total_ms = 0

    # Match hours
    hours_match = re.search(r"(\d+)\s*h", duration_str)
    if hours_match:
        total_ms += int(hours_match.group(1)) * 60 * 60 * 1000

    # Match minutes
    minutes_match = re.search(r"(\d+)\s*m", duration_str)
    if minutes_match:
        total_ms += int(minutes_match.group(1)) * 60 * 1000

    # If no unit specified, assume minutes
    if not hours_match and not minutes_match:
        try:
            total_ms = int(duration_str) * 60 * 1000
        except ValueError as e:
            raise ValueError(f"Invalid duration format: {duration_str}") from e

    return total_ms


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    # Replace invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    # Remove leading/trailing dots and spaces
    name = name.strip(". ")

    # Limit length
    if len(name) > 255:
        name = name[:255]

    return name or "untitled"
