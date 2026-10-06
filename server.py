import contextlib
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from google_auth_oauthlib.flow import Flow

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

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
    update_video_title,
)


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "youtube-mcp-server"
APP_VERSION = "1.6.1"

REDIRECT_URI = os.getenv(
    "YOUTUBE_REDIRECT_URI",
    "https://youtube-mcp-server-fiuu.onrender.com/oauth/callback",
)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP(
    APP_NAME,
    version=APP_VERSION,
)


# ============================================================
# OAUTH PKCE STORAGE
# ============================================================

oauth_flows = {}


# ============================================================
# MCP TOOLS
# ============================================================

@mcp.tool()
def get_channel_info_tool():
    """Get information and statistics for the authenticated YouTube channel."""
    return get_channel_info()


@mcp.tool()
def get_my_videos_tool(max_results: int = 10):
    """List videos from the authenticated YouTube channel."""
    return get_my_videos(max_results=max_results)


@mcp.tool()
def search_youtube_tool(
    query: str,
    max_results: int = 10,
):
    """Search YouTube videos."""
    return search_youtube(
        query=query,
        max_results=max_results,
    )


@mcp.tool()
def get_video_stats_tool(video_id: str):
    """Get views, likes, comments and other statistics for a YouTube video."""
    return get_video_stats(video_id)


@mcp.tool()
def get_channel_analytics_tool(
    start_date: str,
    end_date: str,
    metrics: str = (
        "views,"
        "estimatedMinutesWatched,"
        "averageViewDuration,"
        "subscribersGained,"
        "subscribersLost"
    ),
):
    """Get YouTube Analytics data for a date range."""
    return get_channel_analytics(
        start_date=start_date,
        end_date=end_date,
        metrics=metrics,
    )


@mcp.tool()
def get_video_details_tool(video_id: str):
    """Get detailed information about a YouTube video."""
    return get_video_details(video_id)


@mcp.tool()
def youtube_keyword_research_tool(
    keyword: str,
    max_results: int = 20,
):
    """Research YouTube search results for a keyword."""
    return youtube_keyword_research(
        query=keyword,
        max_results=max_results,
    )


@mcp.tool()
def get_trending_videos_tool(
    region_code: str = "IN",
    category_id: str = "",
    max_results: int = 10,
):
    """Get currently trending YouTube videos."""
    return get_trending_videos(
        region_code=region_code,
        category_id=category_id or None,
        max_results=max_results,
    )


@mcp.tool()
def analyze_video_comments_tool(
    video_id: str,
    max_results: int = 100,
):
    """Analyze comments on a YouTube video."""
    return analyze_video_comments(
        video_id=video_id,
        max_results=max_results,
    )


@mcp.tool()
def compare_videos_tool(
    video_ids: str,
):
    """
    Compare multiple YouTube videos.

    video_ids should be comma-separated.
    Example:
    abc123,def456,ghi789
    """
    return compare_videos(video_ids)


@mcp.tool()
def update_video_title_tool(
    video_id: str,
    new_title: str,
):
    """
    Update the title of a YouTube video.

    Requires YouTube OAuth write permission.
    """
    return update_video_title(
        video_id=video_id,
        new_title=new_title,
    )


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
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://youtube-mcp-server-fiuu.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "mcp_endpoint": "/mcp/",
        "oauth_login": "/oauth/login",
        "oauth_status": "/oauth/status",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "version": APP_VERSION,
    }


# ============================================================
# VERSION
# ============================================================

@app.get("/version")
async def version():

    return {
        "version": APP_VERSION,
        "oauth": "PKCE_FLOW_STORAGE_REFRESH_TOKEN",
        "callback": "HTML_TOKEN_VERSION",
        "tool_names": [
            "get_channel_info",
            "get_my_videos",
            "search_youtube",
            "get_video_stats",
            "get_channel_analytics",
            "get_video_details",
            "youtube_keyword_research",
            "get_trending_videos",
            "analyze_video_comments",
            "compare_videos",
            "update_video_title",
        ],
    }


# ============================================================
# OAUTH STATUS
# ============================================================

@app.get("/oauth/status")
async def oauth_status():

    refresh_token = os.getenv(
        "YOUTUBE_REFRESH_TOKEN"
    )

    access_token = os.getenv(
        "YOUTUBE_ACCESS_TOKEN"
    )

    return {
        "status": "ok",
        "refresh_token_present": bool(
            refresh_token
        ),
        "access_token_present": bool(
            access_token
        ),
        "client_id_present": bool(
            os.getenv("GOOGLE_CLIENT_ID")
        ),
        "client_secret_present": bool(
            os.getenv("GOOGLE_CLIENT_SECRET")
        ),
        "redirect_uri": REDIRECT_URI,
        "message": (
            "Persistent refresh token is available."
            if refresh_token
            else
            "YOUTUBE_REFRESH_TOKEN is missing."
        ),
    }


# ============================================================
# OAUTH LOGIN
# ============================================================

@app.get(
    "/oauth/login",
    response_class=HTMLResponse,
)
async def oauth_login():

    client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    if not client_id:
        return HTMLResponse(
            """
            <h2>OAuth Configuration Error</h2>
            <p>GOOGLE_CLIENT_ID is missing.</p>
            """,
            status_code=500,
        )

    if not client_secret:
        return HTMLResponse(
            """
            <h2>OAuth Configuration Error</h2>
            <p>GOOGLE_CLIENT_SECRET is missing.</p>
            """,
            status_code=500,
        )

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": (
                "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": (
                "https://oauth2.googleapis.com/token"
            ),
            "redirect_uris": [
                REDIRECT_URI
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
    )

    flow.redirect_uri = REDIRECT_URI

    state = secrets.token_urlsafe(32)

    authorization_url, generated_state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
    )

    # Store the EXACT flow object so PKCE verifier
    # remains available during callback.
    oauth_flows[generated_state] = flow

    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube OAuth</title>
        </head>

        <body style="
            font-family: Arial;
            max-width: 700px;
            margin: 60px auto;
            padding: 20px;
        ">

            <h1>YouTube Authorization</h1>

            <p>
                Click the button below to authorize
                your YouTube channel.
            </p>

            <p>
                Make sure you use the Google account
                that owns the <b>Sai Code Tech</b> channel.
            </p>

            <a href="{authorization_url}"
               style="
                    display:inline-block;
                    padding:14px 22px;
                    background:#ff0000;
                    color:white;
                    text-decoration:none;
                    border-radius:6px;
               ">
                Authorize YouTube
            </a>

        </body>
        </html>
        """
    )


# ============================================================
# OAUTH CALLBACK
# ============================================================

@app.get(
    "/oauth/callback",
    response_class=HTMLResponse,
)
async def oauth_callback(
    request: Request,
):

    params = request.query_params

    error = params.get("error")

    if error:

        error_description = params.get(
            "error_description",
            "Google OAuth authorization failed.",
        )

        return HTMLResponse(
            f"""
            <h2>YouTube OAuth Failed</h2>
            <p><b>Error:</b> {error}</p>
            <p>{error_description}</p>
            <p>
                <a href="/oauth/login">
                    Try again
                </a>
            </p>
            """,
            status_code=400,
        )

    code = params.get("code")
    state = params.get("state")

    if not code:
        return HTMLResponse(
            """
            <h2>OAuth Error</h2>
            <p>Authorization code is missing.</p>
            """,
            status_code=400,
        )

    if not state:
        return HTMLResponse(
            """
            <h2>OAuth Error</h2>
            <p>OAuth state is missing.</p>
            """,
            status_code=400,
        )

    flow = oauth_flows.pop(
        state,
        None,
    )

    if flow is None:
        return HTMLResponse(
            """
            <h2>OAuth Session Expired</h2>

            <p>
                The OAuth flow was not found.
                Please start authorization again.
            </p>

            <p>
                <a href="/oauth/login">
                    Start OAuth again
                </a>
            </p>
            """,
            status_code=400,
        )

    try:

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        access_token = credentials.token
        refresh_token = credentials.refresh_token

        if access_token:
            os.environ[
                "YOUTUBE_ACCESS_TOKEN"
            ] = access_token

        if refresh_token:
            os.environ[
                "YOUTUBE_REFRESH_TOKEN"
            ] = refresh_token

        if not refresh_token:

            return HTMLResponse(
                """
                <h2>Authorization completed</h2>

                <p>
                    Google did not return a new refresh token.
                </p>

                <p>
                    If you already have a valid refresh token
                    in Render, you can continue using it.
                </p>
                """,
                status_code=200,
            )

        # Escape token before inserting into HTML.
        # It is intentionally displayed only on the OAuth
        # callback page so the user can save it in Render.
        import html

        safe_refresh_token = html.escape(
            refresh_token
        )

        return HTMLResponse(
            f"""
            <!DOCTYPE html>

            <html>

            <head>
                <title>YouTube Authorization Successful</title>
            </head>

            <body style="
                font-family: Arial;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
            ">

                <h1>
                    YouTube Authorization Successful
                </h1>

                <p>
                    Your YouTube account has been authorized.
                </p>

                <h3>
                    IMPORTANT
                </h3>

                <p>
                    Copy the refresh token below into
                    Render Environment Variables as:
                </p>

                <pre style="
                    background:#f5f5f5;
                    padding:15px;
                    overflow:auto;
                ">YOUTUBE_REFRESH_TOKEN</pre>

                <textarea
                    id="token"
                    readonly
                    style="
                        width:100%;
                        height:120px;
                        padding:10px;
                    "
                >{safe_refresh_token}</textarea>

                <br><br>

                <button
                    onclick="copyToken()"
                    style="
                        padding:12px 20px;
                        cursor:pointer;
                    "
                >
                    Copy Refresh Token
                </button>

                <p style="
                    color:#b00020;
                    margin-top:25px;
                ">
                    Do not share this refresh token with anyone.
                    Do not paste it into ChatGPT or Claude.
                </p>

                <script>
                    function copyToken() {{
                        const token =
                            document.getElementById(
                                "token"
                            );

                        token.select();

                        document.execCommand(
                            "copy"
                        );

                        alert(
                            "Refresh token copied."
                        );
                    }}
                </script>

            </body>

            </html>
            """,
            status_code=200,
        )

    except Exception as e:

        return HTMLResponse(
            f"""
            <h2>YouTube OAuth Failed</h2>

            <p>
                <b>Error:</b>
                {str(e)}
            </p>

            <p>
                <a href="/oauth/login">
                    Try OAuth again
                </a>
            </p>
            """,
            status_code=500,
        )


# ============================================================
# MOUNT MCP
# ============================================================

app.mount(
    "/mcp",
    mcp_http_app,
)
