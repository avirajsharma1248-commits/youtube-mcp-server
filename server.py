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
# MCP TOOL 1: GET CHANNEL INFO
# =========================================================

@mcp.tool()
def get_channel_info() -> dict:
    """
    Get authenticated YouTube channel information
    and statistics.
    """

    return youtube_get_channel_info()


# =========================================================
# MCP TOOL 2: GET MY VIDEOS
# =========================================================

@mcp.tool()
def get_my_videos(max_results: int = 10) -> dict:
    """
    Get videos uploaded by the authenticated
    YouTube channel.
    """

    return youtube_get_my_videos(
        max_results=max_results
    )


# =========================================================
# MCP TOOL 3: SEARCH YOUTUBE
# =========================================================

@mcp.tool()
def search_youtube(
    query: str,
    max_results: int = 10
) -> dict:
    """
    Search YouTube videos using a keyword.
    """

    return youtube_search_youtube(
        query=query,
        max_results=max_results
    )


# =========================================================
# MCP TOOL 4: GET VIDEO STATS
# =========================================================

@mcp.tool()
def get_video_stats(
    video_id: str
) -> dict:
    """
    Get YouTube video information,
    statistics and duration.
    """

    return youtube_get_video_stats(
        video_id=video_id
    )


# =========================================================
# OAUTH SESSION STORAGE
# =========================================================

oauth_sessions = {}


# =========================================================
# MCP LIFESPAN
# =========================================================

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    async with mcp.session_manager.run():
        yield


# =========================================================
# FASTAPI APPLICATION
# =========================================================

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

    # Generate secure OAuth state
    state = secrets.token_urlsafe(32)

    # Create Google OAuth flow
    flow = create_google_flow(
        state=state
    )

    # Generate Google authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )

    # Store flow object.
    #
    # IMPORTANT:
    # The same Flow object must be used in callback
    # because it contains the PKCE code verifier.
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

    # Retrieve the original OAuth flow
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

        # Exchange authorization code
        # for access and refresh tokens.
        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        # =================================================
        # TEMPORARY TOKEN STORAGE
        # =================================================
        #
        # Tokens are stored only in this running process.
        # They are NOT stored in GitHub.
        #
        # Persistent token storage can be added later.
        # =================================================

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
# MCP TRANSPORT SECURITY
# =========================================================
#
# Render deploys this server behind:
#
# youtube-mcp-server-fiuu.onrender.com
#
# MCP's DNS-rebinding protection otherwise accepts only
# localhost hosts and returns:
#
# 421 Misdirected Request
# Invalid Host header
#
# Therefore the real Render hostname is explicitly allowed.
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
# MCP STREAMABLE HTTP
# =========================================================
#
# Because this application is mounted at /mcp,
# the internal MCP path is "/".
#
# Public endpoint:
#
# https://youtube-mcp-server-fiuu.onrender.com/mcp
#
# =========================================================

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True,
    transport_security=transport_security
)


# =========================================================
# MOUNT MCP
# =========================================================

app.mount(
    "/mcp",
    mcp_http_app
)
