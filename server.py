import os
import secrets
import contextlib

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from youtube_auth import create_google_flow

from youtube_service import (
    get_channel_info as youtube_get_channel_info,
    get_my_videos as youtube_get_my_videos,
    search_youtube as youtube_search_youtube,
    get_video_stats as youtube_get_video_stats,
)


# =========================================================
# MCP SERVER
# =========================================================

mcp = MCPServer(
    "youtube-mcp-server"
)


# =========================================================
# MCP TOOLS
# =========================================================

@mcp.tool()
def get_channel_info() -> dict:
    """Get authenticated YouTube channel information and statistics."""
    return youtube_get_channel_info()


@mcp.tool()
def get_my_videos(max_results: int = 10) -> dict:
    """Get videos uploaded by the authenticated YouTube channel."""
    return youtube_get_my_videos(
        max_results=max_results
    )


@mcp.tool()
def search_youtube(
    query: str,
    max_results: int = 10
) -> dict:
    """Search YouTube videos using a keyword."""
    return youtube_search_youtube(
        query=query,
        max_results=max_results
    )


@mcp.tool()
def get_video_stats(
    video_id: str
) -> dict:
    """Get YouTube video information and statistics."""
    return youtube_get_video_stats(
        video_id=video_id
    )


# =========================================================
# OAUTH STORAGE
# =========================================================

oauth_sessions = {}


# =========================================================
# TRANSPORT SECURITY
# =========================================================

transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[
        "youtube-mcp-server-fiuu.onrender.com",
        "youtube-mcp-server-fiuu.onrender.com:*"
    ],
    allowed_origins=[
        "https://youtube-mcp-server-fiuu.onrender.com"
    ]
)


# =========================================================
# MCP HTTP APP
# =========================================================

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    transport_security=transport_security
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="YouTube MCP Server",
    version="1.0.0",
    lifespan=lifespan
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "service": "YouTube MCP Server",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "oauth_login": "/oauth/login",
        "health": "/health",
        "tools": [
            "get_channel_info",
            "get_my_videos",
            "search_youtube",
            "get_video_stats"
        ]
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "youtube-mcp-server"
    }


# =========================================================
# OAUTH LOGIN
# =========================================================

@app.get("/oauth/login")
def oauth_login():

    state = secrets.token_urlsafe(32)

    flow = create_google_flow(
        state=state
    )

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )

    oauth_sessions[state] = flow

    return RedirectResponse(
        authorization_url
    )


# =========================================================
# OAUTH CALLBACK
# =========================================================

@app.get("/oauth/callback")
def oauth_callback(
    code: str,
    state: str
):

    flow = oauth_sessions.pop(
        state,
        None
    )

    if flow is None:

        return JSONResponse(
            {
                "status": "error",
                "message": (
                    "OAuth session expired. "
                    "Please start login again."
                )
            },
            status_code=400
        )

    try:

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        if credentials.token:

            os.environ[
                "YOUTUBE_ACCESS_TOKEN"
            ] = credentials.token

        if credentials.refresh_token:

            os.environ[
                "YOUTUBE_REFRESH_TOKEN"
            ] = credentials.refresh_token

        return JSONResponse(
            {
                "status": "success",
                "message": "YouTube authorization successful",
                "access_token_received": bool(
                    credentials.token
                ),
                "refresh_token_received": bool(
                    credentials.refresh_token
                )
            }
        )

    except Exception as e:

        return JSONResponse(
            {
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )


# =========================================================
# MOUNT MCP AT ROOT
# =========================================================
#
# IMPORTANT:
#
# The MCP app itself contains /mcp.
# Therefore we mount it at "/".
#
# Final endpoint:
#
# https://youtube-mcp-server-fiuu.onrender.com/mcp
#
# =========================================================

app.mount(
    "/",
    mcp_http_app
)
