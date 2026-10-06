import os
import secrets
import contextlib

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from youtube_auth import create_google_flow

from youtube_service import (
    get_channel_info,
    get_my_videos,
    search_youtube,
    get_video_stats,
    get_channel_analytics,
    get_video_details,
    youtube_keyword_research,
    get_trending_videos,
    analyze_video_comments,
    compare_videos,
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "youtube-mcp-server"
APP_VERSION = "1.3.0"

REDIRECT_URI = os.environ.get(
    "YOUTUBE_REDIRECT_URI",
    "https://youtube-mcp-server-fiuu.onrender.com/oauth/callback"
)


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    APP_NAME,
    version=APP_VERSION
)


# ============================================================
# MCP TOOLS
# ============================================================

@mcp.tool()
def get_channel_info_tool():
    """
    Get information about the authenticated YouTube channel.
    """
    try:
        return get_channel_info()
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_channel_info",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def get_my_videos_tool(
    max_results: int = 20,
):
    """
    Get videos from the authenticated YouTube channel.

    Args:
        max_results: Number of videos to return.
    """
    try:
        return get_my_videos(
            max_results=max_results
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_my_videos",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def search_youtube_tool(
    query: str,
    max_results: int = 10,
):
    """
    Search YouTube videos.

    Args:
        query: Search keyword or phrase.
        max_results: Number of results.
    """
    try:
        return search_youtube(
            query=query,
            max_results=max_results
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "search_youtube",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def get_video_stats_tool(
    video_id: str,
):
    """
    Get YouTube video statistics.

    Args:
        video_id: YouTube video ID.
    """
    try:
        return get_video_stats(
            video_id=video_id
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_video_stats",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def get_channel_analytics_tool(
    start_date: str,
    end_date: str,
):
    """
    Get YouTube channel analytics.

    Dates must use YYYY-MM-DD format.

    Args:
        start_date: Analytics start date.
        end_date: Analytics end date.
    """
    try:
        return get_channel_analytics(
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_channel_analytics",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def get_video_details_tool(
    video_id: str,
):
    """
    Get detailed information about a YouTube video.

    Args:
        video_id: YouTube video ID.
    """
    try:
        return get_video_details(
            video_id=video_id
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_video_details",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def youtube_keyword_research_tool(
    keyword: str,
    max_results: int = 20,
):
    """
    Research YouTube keywords and related videos.

    Args:
        keyword: Keyword to research.
        max_results: Number of results.
    """
    try:
        return youtube_keyword_research(
            keyword=keyword,
            max_results=max_results
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "youtube_keyword_research",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def get_trending_videos_tool(
    region_code: str = "IN",
    max_results: int = 20,
):
    """
    Get currently trending YouTube videos.

    Args:
        region_code: Two-letter country code, e.g. IN or US.
        max_results: Number of results.
    """
    try:
        return get_trending_videos(
            region_code=region_code,
            max_results=max_results
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_trending_videos",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def analyze_video_comments_tool(
    video_id: str,
    max_results: int = 100,
):
    """
    Analyze comments on a YouTube video.

    Args:
        video_id: YouTube video ID.
        max_results: Maximum comments to analyze.
    """
    try:
        return analyze_video_comments(
            video_id=video_id,
            max_results=max_results
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "analyze_video_comments",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@mcp.tool()
def compare_videos_tool(
    video_ids: str,
):
    """
    Compare multiple YouTube videos.

    Provide video IDs separated by commas.

    Example:
    2jIGinRBkLM,VIDEO_ID_2,VIDEO_ID_3
    """
    try:
        ids = [
            item.strip()
            for item in video_ids.split(",")
            if item.strip()
        ]

        return compare_videos(
            video_ids=ids
        )

    except Exception as e:
        return {
            "status": "error",
            "tool": "compare_videos",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


# ============================================================
# TRANSPORT SECURITY
# ============================================================

transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,

    allowed_hosts=[
        "youtube-mcp-server-fiuu.onrender.com",
        "youtube-mcp-server-fiuu.onrender.com:*",
    ],

    allowed_origins=[
        "https://youtube-mcp-server-fiuu.onrender.com",
    ],
)


# ============================================================
# MCP HTTP APP
# ============================================================

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True,
    transport_security=transport_security,
)


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    async with mcp.session_manager.run():
        yield


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
)


# ============================================================
# BASIC HOME PAGE
# ============================================================

@app.get("/")
async def home():

    return {
        "status": "online",
        "service": APP_NAME,
        "version": APP_VERSION,
        "mcp_endpoint": "/mcp",
        "oauth_login": "/oauth/login",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# ============================================================
# OAUTH LOGIN
# ============================================================

@app.get("/oauth/login")
async def oauth_login():

    try:

        state = secrets.token_urlsafe(32)

        flow = create_google_flow(
            state=state
        )

        authorization_url, generated_state = (
            flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )
        )

        return RedirectResponse(
            url=authorization_url
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "tool": "oauth_login",
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        )


# ============================================================
# OAUTH CALLBACK
# ============================================================

@app.get("/oauth/callback")
async def oauth_callback(
    code: str,
    state: str = None,
):

    try:

        # Create OAuth flow
        flow = create_google_flow(
            state=state
        )

        # Exchange authorization code
        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        access_token = credentials.token
        refresh_token = credentials.refresh_token

        # ----------------------------------------------------
        # CHECK REFRESH TOKEN
        # ----------------------------------------------------

        if not refresh_token:

            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": (
                        "Refresh token was not received. "
                        "Try OAuth authorization again."
                    ),
                },
            )

        # ----------------------------------------------------
        # TEMPORARY PROCESS STORAGE
        # ----------------------------------------------------

        os.environ[
            "YOUTUBE_ACCESS_TOKEN"
        ] = access_token

        os.environ[
            "YOUTUBE_REFRESH_TOKEN"
        ] = refresh_token

        # ----------------------------------------------------
        # TEMPORARY TOKEN DISPLAY PAGE
        #
        # IMPORTANT:
        # Remove this after copying the token to Render.
        # ----------------------------------------------------

        html = f"""
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                YouTube Authorization Successful
            </title>

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1"
            >

            <style>

                body {{
                    font-family:
                        Arial,
                        sans-serif;

                    max-width:
                        900px;

                    margin:
                        50px auto;

                    padding:
                        20px;

                    line-height:
                        1.6;

                    background:
                        #ffffff;
                }}

                h1 {{
                    color:
                        #16a34a;
                }}

                .warning {{
                    background:
                        #fff3cd;

                    border:
                        1px solid #ffe69c;

                    padding:
                        15px;

                    border-radius:
                        8px;

                    margin:
                        20px 0;
                }}

                .token {{
                    display:
                        block;

                    background:
                        #f4f4f4;

                    border:
                        1px solid #ddd;

                    padding:
                        15px;

                    border-radius:
                        8px;

                    word-break:
                        break-all;

                    margin:
                        10px 0;

                    font-family:
                        monospace;
                }}

                button {{
                    background:
                        #111827;

                    color:
                        white;

                    border:
                        none;

                    padding:
                        12px 20px;

                    border-radius:
                        6px;

                    cursor:
                        pointer;

                    font-size:
                        16px;
                }}

                button:hover {{
                    opacity:
                        0.9;
                }}

                .step {{
                    margin-top:
                        30px;
                }}

                .success {{
                    background:
                        #dcfce7;

                    border:
                        1px solid #86efac;

                    padding:
                        15px;

                    border-radius:
                        8px;
                }}

            </style>

        </head>

        <body>

            <h1>
                ✅ YouTube Authorization Successful
            </h1>

            <div class="success">

                Google OAuth authorization completed
                successfully.

            </div>

            <div class="warning">

                <strong>
                    ⚠️ IMPORTANT
                </strong>

                <br>

                This refresh token is private.

                Do NOT share it with anyone.

                Do NOT post it on GitHub.

            </div>


            <div class="step">

                <h2>
                    Step 1 — Copy Refresh Token
                </h2>

                <div
                    id="token"
                    class="token"
                >
                    {refresh_token}
                </div>

                <button
                    onclick="copyToken()"
                >
                    Copy Refresh Token
                </button>

            </div>


            <div class="step">

                <h2>
                    Step 2 — Add to Render
                </h2>

                <p>
                    Open your Render service.
                </p>

                <p>
                    Go to:
                </p>

                <p>
                    <strong>
                        Environment
                        →
                        Add Environment Variable
                    </strong>
                </p>

                <p>
                    Key:
                </p>

                <div class="token">

                    YOUTUBE_REFRESH_TOKEN

                </div>

                <p>
                    Value:
                    paste the refresh token copied above.
                </p>

            </div>


            <div class="step">

                <h2>
                    Step 3 — Save & Redeploy
                </h2>

                <p>
                    Save the Environment Variable
                    in Render.
                </p>

                <p>
                    Then redeploy your service.
                </p>

            </div>


            <div class="step">

                <h2>
                    Step 4 — Important
                </h2>

                <p>
                    After the token has been added
                    to Render, remove the temporary
                    token-display code from this
                    callback.
                </p>

            </div>


            <script>

                function copyToken() {{

                    const token =
                        document
                        .getElementById("token")
                        .innerText;

                    navigator
                        .clipboard
                        .writeText(token);

                    alert(
                        "Refresh token copied."
                    );
                }}

            </script>

        </body>

        </html>
        """

        return HTMLResponse(
            content=html
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,

            content={
                "status": "error",
                "tool": "oauth_callback",
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )


# ============================================================
# MOUNT MCP
# ============================================================

app.mount(
    "/mcp",
    mcp_http_app
)
