"""MCP Transport implementations for FastAPI integration."""

import asyncio
import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.types import JSONRPCMessage

from gl_mcp.mcp.server import create_mcp_server

logger = logging.getLogger(__name__)

# Session storage for active MCP sessions
_sessions: dict[str, dict[str, Any]] = {}


def get_mcp_router(user_roles_extractor=None) -> APIRouter:
    """Create FastAPI router for MCP endpoints.

    Args:
        user_roles_extractor: Optional callable to extract user roles from request

    Returns:
        FastAPI APIRouter with MCP endpoints
    """
    router = APIRouter(prefix="/mcp", tags=["MCP"])

    @router.post("")
    async def mcp_post(request: Request) -> Response:
        """Handle MCP POST requests (messages)."""
        try:
            body = await request.json()
        except Exception:
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }),
                status_code=400,
                media_type="application/json",
            )

        # Get or create session
        session_id = request.headers.get("mcp-session-id")

        if session_id and session_id in _sessions:
            session = _sessions[session_id]
        elif _is_initialize_request(body):
            # Create new session
            session_id = str(uuid4())
            user_roles = []
            if user_roles_extractor:
                user_roles = await user_roles_extractor(request)

            server = create_mcp_server(user_roles)
            session = {
                "server": server,
                "user_roles": user_roles,
                "message_queue": asyncio.Queue(),
            }
            _sessions[session_id] = session
            logger.info(f"Created new MCP session: {session_id}")
        else:
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid session"},
                    "id": body.get("id") if isinstance(body, dict) else None,
                }),
                status_code=400,
                media_type="application/json",
            )

        # Process the message
        try:
            response = await _handle_message(session["server"], body)

            headers = {"mcp-session-id": session_id}

            if response is None:
                # Notification - no response needed
                return Response(status_code=202, headers=headers)

            return Response(
                content=json.dumps(response),
                status_code=200,
                media_type="application/json",
                headers=headers,
            )

        except Exception as e:
            logger.exception("Error processing MCP message")
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": body.get("id") if isinstance(body, dict) else None,
                }),
                status_code=500,
                media_type="application/json",
            )

    @router.get("")
    async def mcp_get(request: Request) -> Response:
        """Handle MCP GET requests (SSE stream)."""
        session_id = request.headers.get("mcp-session-id")

        if not session_id or session_id not in _sessions:
            return Response(
                content="Invalid or missing session ID",
                status_code=400,
            )

        accept = request.headers.get("accept", "")
        if "text/event-stream" not in accept:
            return Response(
                content="SSE not accepted",
                status_code=405,
            )

        async def event_generator():
            """Generate SSE events."""
            session = _sessions.get(session_id)
            if not session:
                return

            queue = session["message_queue"]
            try:
                while True:
                    try:
                        # Wait for messages with timeout for keep-alive
                        message = await asyncio.wait_for(queue.get(), timeout=30)
                        yield f"data: {json.dumps(message)}\n\n"
                    except asyncio.TimeoutError:
                        # Send keep-alive
                        yield ": keep-alive\n\n"
            except asyncio.CancelledError:
                logger.debug(f"SSE stream cancelled for session {session_id}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "mcp-session-id": session_id,
            },
        )

    @router.delete("")
    async def mcp_delete(request: Request) -> Response:
        """Handle MCP DELETE requests (session termination)."""
        session_id = request.headers.get("mcp-session-id")

        if session_id and session_id in _sessions:
            del _sessions[session_id]
            logger.info(f"Terminated MCP session: {session_id}")
            return Response(status_code=200)

        return Response(status_code=400)

    return router


def _is_initialize_request(body: Any) -> bool:
    """Check if the request is an initialization request."""
    if isinstance(body, dict):
        return body.get("method") == "initialize"
    return False


async def _handle_message(server: Server, message: dict) -> dict | None:
    """Handle an incoming MCP message.

    Args:
        server: MCP Server instance
        message: JSON-RPC message

    Returns:
        Response dict or None for notifications
    """
    method = message.get("method", "")
    params = message.get("params", {})
    msg_id = message.get("id")

    # Handle different MCP methods
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "gl-mcp-python",
                    "version": "0.1.0",
                },
                "capabilities": {
                    "tools": {"listChanged": False},
                },
            },
        }

    elif method == "initialized":
        # Notification - no response
        return None

    elif method == "tools/list":
        tools = await server.list_tools()
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema,
                    }
                    for t in tools
                ],
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        result = await server.call_tool(tool_name, tool_args)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {"type": c.type, "text": c.text}
                    for c in result
                ],
            },
        }

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {},
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }


def get_session_count() -> int:
    """Get the number of active MCP sessions."""
    return len(_sessions)


def get_session_ids() -> list[str]:
    """Get list of active session IDs."""
    return list(_sessions.keys())
