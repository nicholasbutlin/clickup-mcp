"""MCP server implementation for ClickUp integration."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmbeddedResource,
    ImageContent,
    LoggingLevel,
    TextContent,
    Tool,
)

from .client import ClickUpClient
from .config import Config
from .tools import ClickUpTools

logger = logging.getLogger(__name__)


class ClickUpMCPServer:
    """MCP Server for ClickUp integration."""

    def __init__(self, config: Config) -> None:
        """Initialize the server with configuration."""
        self.config = config
        self.client = ClickUpClient(config)
        self.tools = ClickUpTools(self.client)
        self.server = Server("clickup-mcp")

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all MCP handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            return self.tools.get_tool_definitions()

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Optional[Dict[str, Any]] = None
        ) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Call a specific tool."""
            logger.debug(f"Calling tool: {name} with arguments: {arguments}")

            try:
                result = await self.tools.call_tool(name, arguments or {})
                return [TextContent(type="text", text=result)]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {e!s}")]

        @self.server.set_logging_level()
        async def set_logging_level(level: LoggingLevel) -> None:
            """Set the logging level."""
            logger.info(f"Setting logging level to: {level}")
            # Map MCP logging levels to Python logging
            level_map = {
                LoggingLevel.DEBUG: logging.DEBUG,
                LoggingLevel.INFO: logging.INFO,
                LoggingLevel.WARNING: logging.WARNING,
                LoggingLevel.ERROR: logging.ERROR,
            }
            logging.getLogger().setLevel(level_map.get(level, logging.INFO))

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting ClickUp MCP Server")

        # Test API connection on startup
        try:
            user = await self.client.get_current_user()
            logger.info(f"Connected as: {user.get('username', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickUp API: {e}")
            # Continue anyway - connection might work later

        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name="clickup-mcp",
                server_version="0.1.0",
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )

            await self.server.run(
                read_stream,
                write_stream,
                init_options,
            )
