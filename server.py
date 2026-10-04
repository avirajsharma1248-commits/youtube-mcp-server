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


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI()

oauth_sessions = {}


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    "YouTube MCP Server"
)


# ============================================================
# MCP TOOL 1 — GET CHANNEL INFO
# ============================================================

@mcp.tool()
def get_channel_info() -> dict:
    """
    Get information and statistics about the authenticated YouTube channel.
    """

    return youtube_get_channel_info()


# ============================================================
# MCP TOOL 2 — GET MY VIDEOS
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
# MCP TOOL 3 — SEARCH YOUTUBE
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
# MCP TOOL 4 — GET VIDEO STATS
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
# BASIC HTTP ROUTES
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


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# GOOGLE OAUTH LOGIN
# ============================================================

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
        url=authorization_url
    )


# ============================================================
# GOOGLE OAUTH CALLBACK
# ============================================================

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
                "message": "OAuth session expired. Please start login again."
            },
            status_code=400
        )

    try:

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        # Store tokens temporarily in process environment.
        # IMPORTANT: these disappear after a Render restart.
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
# MCP STREAMABLE HTTP
# ============================================================

mcp_app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True
)


# ============================================================
# MOUNT MCP INTO FASTAPI
# ============================================================

app.mount(
    "/",
    mcp_app
)
