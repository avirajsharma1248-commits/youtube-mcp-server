from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = MCPServer(
    "YouTube MCP Server",
    instructions="Tools for accessing and managing the authorized YouTube channel."
)

@mcp.tool()
def get_server_status() -> str:
    """Check whether the YouTube MCP server is running."""
    return "YouTube MCP Server is online."

@mcp.tool()
def get_channel_info() -> str:
    """Return information about the authorized YouTube channel."""
    return "YouTube OAuth connection will be added in the next step."

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request):
    return JSONResponse({"status": "healthy"})

app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    host="0.0.0.0"
)
