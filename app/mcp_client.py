"""
MCP Client Module - Direct tool calling
"""

import importlib.util
from typing import Any, Dict


def call_mcp_tool(
    server_module_path: str, server_name: str, tool_name: str, **kwargs
) -> Dict[str, Any]:
    """Call a tool directly from MCP server module"""
    try:
        # Load module
        spec = importlib.util.spec_from_file_location(server_name, server_module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get tool function (tools are decorated with @server.call_tool())
            # The decorator stores them as module-level functions
            tool_func = getattr(module, tool_name, None)
            if not tool_func:
                raise ValueError(f"Tool {tool_name} not found in {server_name}")

            # Call the tool
            result = tool_func(**kwargs)
            return result if result else {}

        raise ValueError(f"Could not load module {server_module_path}")

    except Exception as e:
        print(f"Error calling MCP tool {tool_name}: {e}")
        raise
