"""MCP Server setup and management."""

import logging
from typing import Callable
from uuid import uuid4

from mcp.server import Server
from mcp.types import Tool, TextContent

from gl_mcp import __version__

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages MCP server instances and tool registration."""

    def __init__(self, name: str = "gl-mcp", version: str = __version__):
        self.name = name
        self.version = version
        self._tool_handlers: dict[str, Callable] = {}
        self._tools: list[Tool] = []

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
    ) -> None:
        """Register a tool with the MCP server.

        Args:
            name: Unique tool name (e.g., "news_list_articles")
            description: Human-readable description
            input_schema: JSON Schema for tool parameters
            handler: Async function to handle tool calls
        """
        tool = Tool(
            name=name,
            description=description,
            inputSchema=input_schema,
        )
        self._tools.append(tool)
        self._tool_handlers[name] = handler
        logger.debug(f"Registered tool: {name}")

    def create_server(self, user_roles: list[str] | None = None) -> Server:
        """Create a new MCP Server instance.

        Args:
            user_roles: Optional list of user roles for filtering tools

        Returns:
            Configured MCP Server instance
        """
        server = Server(self.name)

        # Register list_tools handler
        @server.list_tools()
        async def list_tools():
            return self._tools

        # Register call_tool handler
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name not in self._tool_handlers:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            try:
                handler = self._tool_handlers[name]
                result = await handler(**arguments)

                # Normalize result to list of content
                if isinstance(result, str):
                    return [TextContent(type="text", text=result)]
                elif isinstance(result, list):
                    return result
                else:
                    return [TextContent(type="text", text=str(result))]

            except Exception as e:
                logger.exception(f"Error executing tool {name}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        logger.info(f"Created MCP server with {len(self._tools)} tools")
        return server

    @property
    def tool_count(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    @property
    def tool_names(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tool_handlers.keys())


# Global server manager instance
_server_manager: MCPServerManager | None = None


def get_server_manager() -> MCPServerManager:
    """Get or create the global server manager."""
    global _server_manager
    if _server_manager is None:
        _server_manager = MCPServerManager()
    return _server_manager


def create_mcp_server(user_roles: list[str] | None = None) -> Server:
    """Create a new MCP server instance.

    Args:
        user_roles: Optional list of user roles for filtering tools

    Returns:
        Configured MCP Server instance
    """
    return get_server_manager().create_server(user_roles)
