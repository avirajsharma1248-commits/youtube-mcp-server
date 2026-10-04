from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

mcp = MCPServer(
    "YouTube MCP Server",
    instructions="MCP server for the user's authorized YouTube channel."
)

@mcp.tool()
def get_server_status() -> str:
    """Check whether the MCP server is online."""
    return "YouTube MCP Server is online."

@mcp.tool()
def get_channel_info() -> str:
    """Get information about the authorized YouTube channel."""
    return "YouTube authorization will be connected next."

security = TransportSecuritySettings(
    allowed_hosts=[
        "youtube-mcp-server-fiuu.onrender.com",
        "youtube-mcp-server-fiuu.onrender.com:*"
    ],
    allowed_origins=[
        "https://youtube-mcp-server-fiuu.onrender.com"
    ]
)

app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    transport_security=security
)
