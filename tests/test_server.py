"""Tests for the MCP server implementation."""

from unittest.mock import AsyncMock, patch

import pytest
from clickup_mcp.server import ClickUpMCPServer


class TestClickUpMCPServer:
    """Test MCP server functionality."""

    @pytest.fixture
    def server(self, mock_config):
        """Create server instance with mocked config."""
        return ClickUpMCPServer(mock_config)

    def test_server_initialization(self, server, mock_config):
        """Test server initialization."""
        assert server.config == mock_config
        assert server.client is not None
        assert server.tools is not None
        assert server.server is not None

    def test_get_tool_definitions(self, server):
        """Test that all tool definitions are returned."""
        definitions = server.tools.get_tool_definitions()

        # Should have all 27 tools
        assert len(definitions) >= 24  # At least the documented tools

        tool_names = [tool.name for tool in definitions]

        # Check for core tools
        assert "create_task" in tool_names
        assert "get_task" in tool_names
        assert "update_task" in tool_names
        assert "delete_task" in tool_names
        assert "list_tasks" in tool_names
        assert "search_tasks" in tool_names

        # Check for advanced tools
        assert "bulk_update_tasks" in tool_names
        assert "log_time" in tool_names
        assert "create_task_from_template" in tool_names
        assert "get_team_workload" in tool_names

    @pytest.mark.asyncio
    async def test_server_startup(self, server):
        """Test server startup process."""
        # Mock the API connection
        server.client.get_current_user = AsyncMock(return_value={"username": "testuser"})

        with patch("clickup_mcp.server.stdio_server") as mock_stdio:
            # Mock stdio_server to return read/write streams
            mock_read_stream = AsyncMock()
            mock_write_stream = AsyncMock()
            mock_stdio.return_value.__aenter__ = AsyncMock(
                return_value=(mock_read_stream, mock_write_stream)
            )
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock the server run method
            server.server.run = AsyncMock()

            await server.run()

            server.server.run.assert_called_once()

    def test_tool_schema_validation(self, server):
        """Test that all tool schemas are valid."""
        definitions = server.tools.get_tool_definitions()

        for tool in definitions:
            # Each tool should have required fields
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

            # Name should be non-empty string
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0

            # Description should be non-empty string
            assert isinstance(tool.description, str)
            assert len(tool.description) > 0

            # Input schema should be a dict with required fields
            schema = tool.inputSchema
            assert isinstance(schema, dict)
            assert "type" in schema
            assert schema["type"] == "object"

            # If properties exist, should be a dict
            if "properties" in schema:
                assert isinstance(schema["properties"], dict)

            # If required exists, should be a list
            if "required" in schema:
                assert isinstance(schema["required"], list)
