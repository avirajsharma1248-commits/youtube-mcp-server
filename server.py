import os
import secrets

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from youtube_auth import create_google_flow

from youtube_service import (
    get_channel_info as youtube_get_channel_info,
    get_my_videos as youtube_get_my_videos,
    search_youtube as youtube_search_youtube,
    get_video_stats as youtube_get_video_stats,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI()

# Temporary OAuth sessions
oauth_sessions = {}


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer("YouTube MCP Server")


# ============================================================
# TOOL 1: GET CHANNEL INFO
# ============================================================

@mcp.tool()
def get_channel_info() -> dict:
    """
    Get information and statistics about the authenticated YouTube channel.
    """

    return youtube_get_channel_info()


# ============================================================
# TOOL 2: GET MY VIDEOS
# ============================================================

@mcp.tool()
def get_my_videos(max_results: int = 10) -> dict:
    """
    Get videos uploaded to the authenticated YouTube channel.
    """

    return youtube_get_my_videos(
        max_results=max_results
    )


# ============================================================
# TOOL 3: SEARCH YOUTUBE
# ============================================================

@mcp.tool()
def search_youtube(
    query: str,
    max_results: int = 10
) -> dict:
    """
    Search YouTube videos using a keyword or phrase.
    """

    return youtube_search_youtube(
        query=query,
        max_results=max_results
    )


# ============================================================
# TOOL 4: GET VIDEO STATS
# ============================================================

@mcp.tool()
def get_video_stats(video_id: str) -> dict:
    """
    Get details and statistics for a YouTube video.
    """

    return youtube_get_video_stats(
        video_id=video_id
    )


# ============================================================
# BASIC HOME ROUTE
# ============================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "service": "YouTube MCP Server",
        "mcp_endpoint": "/mcp",
        "tools": [
            "get_channel_info",
            "get_my_videos",
            "search_youtube",
            "get_video_stats"
        ]
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# OAUTH LOGIN
# ============================================================

@app.get("/oauth/login")
def oauth_login():

    # Generate secure state
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

    # Save flow temporarily
    oauth_sessions[state] = flow

    # Redirect to Google
    return RedirectResponse(
        url=authorization_url
    )


# ============================================================
# OAUTH CALLBACK
# ============================================================

@app.get("/oauth/callback")
def oauth_callback(
    code: str,
    state: str
):

    # Get saved OAuth flow
    flow = oauth_sessions.pop(
        state,
        None
    )

    # Session not found
    if flow is None:

        return JSONResponse(
            {
                "status": "error",
                "message": "OAuth session expired. Please start login again."
            },
            status_code=400
        )

    try:

        # Exchange authorization code
        # for access and refresh tokens
        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        # Store tokens in current process.
        #
        # IMPORTANT:
        # These are temporary and disappear
        # when the Render instance restarts.
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


# ============================================================
# MCP HOST SECURITY
# ============================================================

security = TransportSecuritySettings(

    allowed_hosts=[
        "youtube-mcp-server-fiuu.onrender.com",
        "youtube-mcp-server-fiuu.onrender.com:*"
    ],

    allowed_origins=[
        "https://youtube-mcp-server-fiuu.onrender.com"
    ]
)


# ============================================================
# MCP STREAMABLE HTTP APP
# ============================================================

mcp_app = mcp.streamable_http_app(

    streamable_http_path="/mcp",

    stateless_http=True,

    transport_security=security
)


# ============================================================
# MOUNT MCP
# ============================================================

app.mount(
    "/",
    mcp_app
)
