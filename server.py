from mcp.server import MCPServer

mcp = MCPServer(
    "YouTube MCP Server",
    instructions="MCP server for the user's authorized YouTube channel."
)

@mcp.tool()
def get_server_status() -> str:
    """Check whether the YouTube MCP server is online."""
    return "YouTube MCP Server is online."

@mcp.tool()
def get_channel_info() -> str:
    """Get information about the user's authorized YouTube channel."""
    return "YouTube authorization is not connected yet."

app = mcp.streamable_http_app()
