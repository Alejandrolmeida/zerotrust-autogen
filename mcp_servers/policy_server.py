#!/usr/bin/env python
"""
MCP‑Server – Herramientas 'Policy‑as‑Prompt'.
.env: TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID
"""
from __future__ import annotations
import asyncio, json, textwrap, sys, os
from typing import List

# Añadir el directorio raíz al path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ErrorData, INVALID_PARAMS, INTERNAL_ERROR
from mcp.shared.exceptions import McpError

from mcp_tools.policy_tools import get_policy_tools

TOOLS    = get_policy_tools()
TOOL_MAP = {t["name"]: t for t in TOOLS}

async def serve() -> None:
    s = Server("mcp-policy")

    @s.list_tools()
    async def _tools() -> List[Tool]:
        return [Tool(d["name"], d["description"], d["parameters"]) for d in TOOLS]

    @s.call_tool()
    async def _call(name: str, arguments: dict):
        try:
            if name not in TOOL_MAP:
                raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Tool desconocida: {name}"))
            result = TOOL_MAP[name]["handler"](arguments or {})
            text   = result if isinstance(result, str) \
                     else textwrap.indent(json.dumps(result, indent=2, ensure_ascii=False), "  ")
            return [TextContent(type="text", text=text)]
        except McpError:
            raise
        except Exception as exc:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(exc)))

    opts = s.create_initialization_options()
    async with stdio_server() as (r, w):
        await s.run(r, w, opts, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(serve())
