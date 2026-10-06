import os
import secrets

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

from mcp.server import MCPServer

from youtube_auth import create_google_flow

from youtube_service import (
    get_channel_info as youtube_get_channel_info,
    get_my_videos as youtube_get_my_videos,
    search_youtube as youtube_search_youtube,
    get_video_stats as youtube_get_video_stats,
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="YouTube MCP Server",
    version="1.0.0"
)


# =========================================================
# TEMPORARY OAUTH SESSION STORAGE
# =========================================================

oauth_sessions = {}


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
# HEALTH CHECK
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

    # Generate OAuth state
    state = secrets.token_urlsafe(32)

    # Create Google OAuth flow
    flow = create_google_flow(
        state=state
    )

    # Generate authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )

    # Save flow object.
    # Important for PKCE/code_verifier.
    oauth_sessions[state] = flow

    # Redirect user to Google
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

    # Get original OAuth flow
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
        # for access + refresh tokens
        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        # -------------------------------------------------
        # TEMPORARY TOKEN STORAGE
        # -------------------------------------------------
        #
        # These are stored only in the current Render
        # process. They are NOT written to GitHub.
        #
        # For production, persistent token storage should
        # be added later.
        # -------------------------------------------------

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
# MCP STREAMABLE HTTP
# =========================================================
#
# IMPORTANT:
#
# Because the MCP application is mounted at /mcp,
# its internal path must be "/".
#
# Otherwise /mcp + /mcp can result in:
#
#     /mcp/mcp
#
# The desired public endpoint is:
#
#     /mcp
#
# =========================================================

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True
)


# =========================================================
# MOUNT MCP AT /mcp
# =========================================================

app.mount(
    "/mcp",
    mcp_http_app
)
