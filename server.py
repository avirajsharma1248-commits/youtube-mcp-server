from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "YouTube MCP Server",
    stateless_http=True,
    json_response=True
)

@mcp.tool()
def get_server_status() -> str:
    """Check whether the YouTube MCP server is online."""
    return "YouTube MCP Server is online."

@mcp.tool()
def get_channel_info() -> str:
    """Get information about the connected YouTube channel."""
    return "YouTube authorization will be connected next."

app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )
)
