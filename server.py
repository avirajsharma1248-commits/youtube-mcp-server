import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

from mcp.server import MCPServer

from youtube_auth import create_google_flow
from youtube_service import get_my_channel


# -----------------------------
# MCP SERVER
# -----------------------------

mcp = MCPServer(
    "YouTube MCP Server",
    instructions="MCP server for the user's authorized YouTube channel."
)


@mcp.tool()
def get_server_status() -> str:
    """Check whether the YouTube MCP server is online."""
    return "YouTube MCP Server is online."


@mcp.tool()
def get_channel_info() -> dict:
    """Get information about the authorized YouTube channel."""
    try:
        return get_my_channel()
    except Exception as e:
        return {
            "error": str(e),
            "message": "YouTube account is not authorized yet."
        }


# -----------------------------
# FASTAPI APP
# -----------------------------

app = FastAPI()


@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "YouTube MCP Server"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# -----------------------------
# GOOGLE OAUTH LOGIN
# -----------------------------

@app.get("/oauth/login")
async def oauth_login():

    flow = create_google_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return RedirectResponse(authorization_url)


# -----------------------------
# GOOGLE OAUTH CALLBACK
# -----------------------------

@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str = None):

    flow = create_google_flow()

    flow.fetch_token(code=code)

    credentials = flow.credentials

    return JSONResponse({
        "status": "success",
        "message": "YouTube authorization successful.",
        "has_access_token": credentials.token is not None,
        "has_refresh_token": credentials.refresh_token is not None
    })


# -----------------------------
# MCP ENDPOINT
# -----------------------------

mcp_app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True
)

app.mount("/", mcp_app)
