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
    get_channel_analytics as youtube_get_channel_analytics,
    get_video_details as youtube_get_video_details,
    youtube_keyword_research as youtube_keyword_research_fn,
    get_trending_videos as youtube_get_trending_videos,
    analyze_video_comments as youtube_analyze_video_comments,
    compare_videos as youtube_compare_videos,
)


# =========================================================
# MCP SERVER
# =========================================================

mcp = MCPServer(
    "youtube-mcp-server",
    version="1.1.0"
)


# =========================================================
# BASIC TOOLS
# =========================================================

@mcp.tool()
def get_channel_info() -> dict:
    """
    Get YouTube channel information including
    subscribers, views and video count.
    """

    return youtube_get_channel_info()


@mcp.tool()
def get_my_videos(
    max_results: int = 10
) -> dict:
    """
    Get the latest videos from the authenticated
    YouTube channel.
    """

    return youtube_get_my_videos(
        max_results=max_results
    )


@mcp.tool()
def search_youtube(
    query: str,
    max_results: int = 10
) -> dict:
    """
    Search YouTube videos.
    """

    return youtube_search_youtube(
        query=query,
        max_results=max_results
    )


@mcp.tool()
def get_video_stats(
    video_id: str
) -> dict:
    """
    Get views, likes, comments and other statistics
    for a YouTube video.
    """

    return youtube_get_video_stats(
        video_id=video_id
    )


# =========================================================
# ADDITIONAL MCP TOOLS
# =========================================================

@mcp.tool()
def get_channel_analytics(
    start_date: str,
    end_date: str
) -> dict:
    """
    Get YouTube channel analytics for a date range.

    Date format:
    YYYY-MM-DD
    """

    return youtube_get_channel_analytics(
        start_date=start_date,
        end_date=end_date
    )


@mcp.tool()
def get_video_details(
    video_id: str
) -> dict:
    """
    Get complete details about a YouTube video.
    """

    return youtube_get_video_details(
        video_id=video_id
    )


@mcp.tool()
def youtube_keyword_research(
    query: str,
    max_results: int = 20
) -> dict:
    """
    Research YouTube search results for a keyword.
    """

    return youtube_keyword_research_fn(
        query=query,
        max_results=max_results
    )


@mcp.tool()
def get_trending_videos(
    region_code: str = "IN",
    category_id: str = None,
    max_results: int = 10
) -> dict:
    """
    Get popular/trending YouTube videos for a region.
    """

    return youtube_get_trending_videos(
        region_code=region_code,
        category_id=category_id,
        max_results=max_results
    )


@mcp.tool()
def analyze_video_comments(
    video_id: str,
    max_results: int = 100
) -> dict:
    """
    Retrieve and analyze comments from a YouTube video.
    """

    return youtube_analyze_video_comments(
        video_id=video_id,
        max_results=max_results
    )


@mcp.tool()
def compare_videos(
    video_ids: str
) -> dict:
    """
    Compare multiple YouTube videos.

    Example:
    abc123,xyz456,test789
    """

    return youtube_compare_videos(
        video_ids=video_ids
    )


# =========================================================
# OAUTH SESSION STORAGE
# =========================================================

oauth_sessions = {}


# =========================================================
# MCP TRANSPORT SECURITY
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
    streamable_http_path="/",
    stateless_http=True,
    transport_security=transport_security
)


# =========================================================
# APPLICATION LIFESPAN
# =========================================================

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    async with mcp.session_manager.run():
        yield


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="YouTube MCP Server",
    version="1.1.0",
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
        "version": "1.1.0",
        "mcp_endpoint": "/mcp",
        "oauth_login": "/oauth/login",
        "health": "/health",
        "tools": [
            "get_channel_info",
            "get_my_videos",
            "search_youtube",
            "get_video_stats",
            "get_channel_analytics",
            "get_video_details",
            "youtube_keyword_research",
            "get_trending_videos",
            "analyze_video_comments",
            "compare_videos"
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

        # -------------------------------------------------
        # Save current access token in process memory
        # -------------------------------------------------

        if credentials.token:

            os.environ[
                "YOUTUBE_ACCESS_TOKEN"
            ] = credentials.token

        # -------------------------------------------------
        # Save refresh token in process memory
        #
        # IMPORTANT:
        # For permanent Render storage, the refresh token
        # must also be added manually to Render Environment.
        # -------------------------------------------------

        if credentials.refresh_token:

            os.environ[
                "YOUTUBE_REFRESH_TOKEN"
            ] = credentials.refresh_token

        return JSONResponse(
            {
                "status": "success",
                "message": (
                    "YouTube authorization successful"
                ),
                "access_token_received": bool(
                    credentials.token
                ),
                "refresh_token_received": bool(
                    credentials.refresh_token
                ),
                "next_step": (
                    "Add YOUTUBE_REFRESH_TOKEN to "
                    "Render Environment Variables "
                    "for persistent authorization."
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
# MOUNT MCP
# =========================================================

app.mount(
    "/mcp",
    mcp_http_app
)
