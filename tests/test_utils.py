"""Tests for utility functions."""

import pytest
from clickup_mcp.utils import format_task_url, parse_duration, parse_task_id


class TestUtils:
    """Test utility functions."""

    def test_parse_task_id_standard(self):
        """Test parsing standard task IDs."""
        assert parse_task_id("abc123") == ("abc123", None)
        assert parse_task_id("123456") == ("123456", None)
        assert parse_task_id("task_789") == ("task_789", None)

    def test_parse_task_id_custom_format(self):
        """Test parsing custom task ID formats."""
        # Without patterns, these are treated as standard IDs
        assert parse_task_id("gh-123") == ("gh-123", None)
        assert parse_task_id("bug-456") == ("bug-456", None)
        assert parse_task_id("PROJ-789") == ("PROJ-789", None)
        assert parse_task_id("cs-1234") == ("cs-1234", None)

    def test_parse_task_id_custom_format_with_patterns(self):
        """Test parsing custom task ID formats with patterns."""
        patterns = {"gh": "github", "bug": "bugfix"}
        assert parse_task_id("gh-123", patterns) == ("gh-123", "gh")
        assert parse_task_id("bug-456", patterns) == ("bug-456", "bug")
        assert parse_task_id("cs-1234", patterns) == ("cs-1234", None)  # No pattern

    def test_parse_task_id_from_url(self):
        """Test extracting task ID from ClickUp URLs."""
        assert parse_task_id("https://app.clickup.com/t/abc123") == ("abc123", None)
        assert parse_task_id("https://app.clickup.com/t/gh123") == ("gh123", None)
        assert parse_task_id("https://app.clickup.com/12345/t/task123") == ("task123", None)
        assert parse_task_id("https://app.clickup.com/t/abc123?view=board") == ("abc123", None)

    def test_parse_task_id_hash_format(self):
        """Test parsing hash format task IDs."""
        assert parse_task_id("#123") == ("123", None)
        assert parse_task_id("#abc123") == ("abc123", None)

    def test_parse_task_id_edge_cases(self):
        """Test edge cases for task ID parsing."""
        assert parse_task_id("") == ("", None)
        assert parse_task_id("   abc123   ") == ("abc123", None)
        assert parse_task_id("https://app.clickup.com/t/") == ("https://app.clickup.com/t/", None)
        assert parse_task_id("not-a-url-or-id") == ("not-a-url-or-id", None)

    def test_format_task_url(self):
        """Test formatting task URLs."""
        assert format_task_url("abc123") == "https://app.clickup.com/t/abc123"
        assert format_task_url("gh-123") == "https://app.clickup.com/t/gh-123"
        assert format_task_url("") == "https://app.clickup.com/t/"

    def test_parse_duration_hours_minutes(self):
        """Test parsing duration with hours and minutes."""
        assert parse_duration("2h") == 2 * 60 * 60 * 1000  # 2 hours in ms
        assert parse_duration("30m") == 30 * 60 * 1000  # 30 minutes in ms
        assert parse_duration("1h 30m") == (1 * 60 * 60 + 30 * 60) * 1000  # 1.5 hours in ms
        assert parse_duration("2h30m") == (2 * 60 * 60 + 30 * 60) * 1000  # 2.5 hours in ms
        assert parse_duration("0h 45m") == 45 * 60 * 1000  # 45 minutes in ms

    def test_parse_duration_case_insensitive(self):
        """Test that duration parsing is case insensitive."""
        assert parse_duration("2H") == 2 * 60 * 60 * 1000  # 2 hours in ms
        assert parse_duration("30M") == 30 * 60 * 1000  # 30 minutes in ms
        assert parse_duration("1h 30M") == (1 * 60 * 60 + 30 * 60) * 1000  # 1.5 hours in ms

    def test_parse_duration_whitespace(self):
        """Test duration parsing with various whitespace."""
        assert parse_duration("  2h  ") == 2 * 60 * 60 * 1000  # 2 hours in ms
        assert parse_duration("1h  30m") == (1 * 60 * 60 + 30 * 60) * 1000  # 1.5 hours in ms
        assert parse_duration("2h\t30m") == (2 * 60 * 60 + 30 * 60) * 1000  # 2.5 hours in ms

    def test_parse_duration_invalid(self):
        """Test parsing invalid duration strings."""
        # Should raise ValueError for invalid formats
        with pytest.raises(ValueError):
            parse_duration("invalid")

        with pytest.raises(ValueError):
            parse_duration("2x")

    def test_parse_duration_mixed_formats(self):
        """Test parsing various mixed duration formats."""
        assert parse_duration("90m") == 90 * 60 * 1000  # 90 minutes in ms
        assert parse_duration("1h30m") == (1 * 60 * 60 + 30 * 60) * 1000  # 1.5 hours in ms

    def test_parse_duration_large_values(self):
        """Test parsing large duration values."""
        assert parse_duration("100h") == 100 * 60 * 60 * 1000  # 100 hours in ms
        assert parse_duration("1000m") == 1000 * 60 * 1000  # 1000 minutes in ms

    def test_parse_duration_minutes_only(self):
        """Test parsing duration with just numbers (assumed to be minutes)."""
        assert parse_duration("30") == 30 * 60 * 1000  # 30 minutes in ms
        assert parse_duration("120") == 120 * 60 * 1000  # 120 minutes in ms
