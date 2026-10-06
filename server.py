import os
import secrets
import contextlib
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import (
    RedirectResponse,
    JSONResponse,
    HTMLResponse,
)

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
    update_video_title,
)


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "youtube-mcp-server"
APP_VERSION = "1.6.0"

REDIRECT_URI = os.environ.get(
    "YOUTUBE_REDIRECT_URI",
    "https://youtube-mcp-server-fiuu.onrender.com/oauth/callback",
)


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    APP_NAME,
    version=APP_VERSION,
)


# ============================================================
# OAUTH PKCE STORAGE
# ============================================================

oauth_flows: Dict[str, object] = {}


# ============================================================
# COMMON ERROR HANDLER
# ============================================================

def tool_error(
    tool_name: str,
    error: Exception,
):
    return {
        "status": "error",
        "tool": tool_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }


# ============================================================
# TOOL 1
# get_channel_info
# ============================================================

@mcp.tool(name="get_channel_info")
def get_channel_info_tool():

    try:

        return get_channel_info()

    except Exception as e:

        return tool_error(
            "get_channel_info",
            e,
        )


# ============================================================
# TOOL 2
# get_my_videos
# ============================================================

@mcp.tool(name="get_my_videos")
def get_my_videos_tool(
    max_results: int = 20,
):

    try:

        return get_my_videos(
            max_results=max_results,
        )

    except Exception as e:

        return tool_error(
            "get_my_videos",
            e,
        )


# ============================================================
# TOOL 3
# search_youtube
# ============================================================

@mcp.tool(name="search_youtube")
def search_youtube_tool(
    query: str,
    max_results: int = 10,
):

    try:

        return search_youtube(
            query=query,
            max_results=max_results,
        )

    except Exception as e:

        return tool_error(
            "search_youtube",
            e,
        )


# ============================================================
# TOOL 4
# get_video_stats
# ============================================================

@mcp.tool(name="get_video_stats")
def get_video_stats_tool(
    video_id: str,
):

    try:

        return get_video_stats(
            video_id=video_id,
        )

    except Exception as e:

        return tool_error(
            "get_video_stats",
            e,
        )


# ============================================================
# TOOL 5
# get_channel_analytics
# ============================================================

@mcp.tool(name="get_channel_analytics")
def get_channel_analytics_tool(
    start_date: str,
    end_date: str,
):

    try:

        return get_channel_analytics(
            start_date=start_date,
            end_date=end_date,
        )

    except Exception as e:

        return tool_error(
            "get_channel_analytics",
            e,
        )


# ============================================================
# TOOL 6
# get_video_details
# ============================================================

@mcp.tool(name="get_video_details")
def get_video_details_tool(
    video_id: str,
):

    try:

        return get_video_details(
            video_id=video_id,
        )

    except Exception as e:

        return tool_error(
            "get_video_details",
            e,
        )


# ============================================================
# TOOL 7
# youtube_keyword_research
# ============================================================

@mcp.tool(name="youtube_keyword_research")
def youtube_keyword_research_tool(
    keyword: str,
    max_results: int = 20,
):

    try:

        return youtube_keyword_research(
            query=keyword,
            max_results=max_results,
        )

    except Exception as e:

        return tool_error(
            "youtube_keyword_research",
            e,
        )


# ============================================================
# TOOL 8
# get_trending_videos
# ============================================================

@mcp.tool(name="get_trending_videos")
def get_trending_videos_tool(
    region_code: str = "IN",
    max_results: int = 20,
):

    try:

        return get_trending_videos(
            region_code=region_code,
            max_results=max_results,
        )

    except Exception as e:

        return tool_error(
            "get_trending_videos",
            e,
        )


# ============================================================
# TOOL 9
# analyze_video_comments
# ============================================================

@mcp.tool(name="analyze_video_comments")
def analyze_video_comments_tool(
    video_id: str,
    max_results: int = 100,
):

    try:

        return analyze_video_comments(
            video_id=video_id,
            max_results=max_results,
        )

    except Exception as e:

        return tool_error(
            "analyze_video_comments",
            e,
        )


# ============================================================
# TOOL 10
# compare_videos
# ============================================================

@mcp.tool(name="compare_videos")
def compare_videos_tool(
    video_ids: str,
):

    try:

        ids = [
            video_id.strip()
            for video_id in video_ids.split(",")
            if video_id.strip()
        ]

        if not ids:

            return {
                "status": "error",
                "tool": "compare_videos",
                "message": "No video IDs provided.",
            }

        return compare_videos(
            video_ids=ids,
        )

    except Exception as e:

        return tool_error(
            "compare_videos",
            e,
        )


# ============================================================
# TOOL 11
# update_video_title
# ============================================================

@mcp.tool(name="update_video_title")
def update_video_title_tool(
    video_id: str,
    new_title: str,
):

    try:

        return update_video_title(
            video_id=video_id,
            new_title=new_title,
        )

    except Exception as e:

        return tool_error(
            "update_video_title",
            e,
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
# HOME
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
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# ============================================================
# VERSION
# ============================================================

@app.get("/version")
async def version():

    return {
        "version": APP_VERSION,

        "oauth": "PKCE_FLOW_STORAGE",

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
# OAUTH LOGIN
# ============================================================

@app.get("/oauth/login")
async def oauth_login():

    try:

        # ----------------------------------------------------
        # Generate OAuth state
        # ----------------------------------------------------

        state = secrets.token_urlsafe(32)

        # ----------------------------------------------------
        # Create Google OAuth flow
        # ----------------------------------------------------

        flow = create_google_flow(
            state=state,
        )

        # ----------------------------------------------------
        # Generate authorization URL
        #
        # This also creates PKCE information.
        # The SAME flow object is stored for callback.
        # ----------------------------------------------------

        authorization_url, generated_state = (
            flow.authorization_url(

                access_type="offline",

                include_granted_scopes="true",

                prompt="consent",
            )
        )

        # ----------------------------------------------------
        # Save flow for callback
        # ----------------------------------------------------

        oauth_flows[
            generated_state
        ] = flow

        return RedirectResponse(
            url=authorization_url,
        )

    except Exception as e:

        return JSONResponse(

            status_code=500,

            content={
                "status": "error",
                "tool": "oauth_login",
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
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

        # ----------------------------------------------------
        # State validation
        # ----------------------------------------------------

        if not state:

            return JSONResponse(

                status_code=400,

                content={
                    "status": "error",
                    "message": "Missing OAuth state.",
                },
            )

        # ----------------------------------------------------
        # Retrieve SAME OAuth flow
        #
        # This fixes:
        # invalid_grant / Missing code verifier
        # ----------------------------------------------------

        flow = oauth_flows.pop(
            state,
            None,
        )

        if flow is None:

            return JSONResponse(

                status_code=400,

                content={
                    "status": "error",
                    "message": (
                        "OAuth session expired or was not found. "
                        "Please start again from /oauth/login."
                    ),
                },
            )

        # ----------------------------------------------------
        # Exchange authorization code
        # ----------------------------------------------------

        flow.fetch_token(
            code=code,
        )

        credentials = flow.credentials

        access_token = credentials.token

        refresh_token = credentials.refresh_token

        # ----------------------------------------------------
        # Validate tokens
        # ----------------------------------------------------

        if not access_token:

            return JSONResponse(

                status_code=400,

                content={
                    "status": "error",
                    "message": (
                        "Access token was not received."
                    ),
                },
            )

        if not refresh_token:

            return JSONResponse(

                status_code=400,

                content={
                    "status": "error",
                    "message": (
                        "Refresh token was not received. "
                        "Try authorization again."
                    ),
                },
            )

        # ----------------------------------------------------
        # Temporary process storage
        #
        # Persistent value should be stored in Render:
        #
        # YOUTUBE_REFRESH_TOKEN
        # ----------------------------------------------------

        os.environ[
            "YOUTUBE_ACCESS_TOKEN"
        ] = access_token

        os.environ[
            "YOUTUBE_REFRESH_TOKEN"
        ] = refresh_token

        # ----------------------------------------------------
        # Success HTML page
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
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
        }}

        h1 {{
            color: #16a34a;
        }}

        .success {{
            background: #dcfce7;
            border: 1px solid #86efac;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .warning {{
            background: #fff3cd;
            border: 1px solid #ffe69c;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .token {{
            display: block;
            background: #f4f4f4;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 8px;
            word-break: break-all;
            margin: 10px 0;
            font-family: monospace;
        }}

        button {{
            background: #111827;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }}

        .step {{
            margin-top: 30px;
        }}

    </style>

</head>

<body>

    <h1>
        ✅ YouTube Authorization Successful
    </h1>

    <div class="success">

        Google OAuth authorization completed successfully.

        <br><br>

        Your YouTube account is now connected.

    </div>

    <div class="warning">

        <strong>
            ⚠️ IMPORTANT
        </strong>

        <br><br>

        The refresh token is private.

        <br>

        Do NOT share it with anyone.

        <br>

        Do NOT upload it to GitHub.

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

        <button onclick="copyToken()">
            Copy Refresh Token
        </button>

    </div>

    <div class="step">

        <h2>
            Step 2 — Add to Render
        </h2>

        <p>
            Open your Render service and go to:
        </p>

        <p>
            <strong>
                Environment → Environment Variables
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
            paste your refresh token.
        </p>

    </div>

    <div class="step">

        <h2>
            Step 3 — Save and Deploy
        </h2>

        <p>
            Save the environment variable and redeploy
            the Render service.
        </p>

    </div>

    <div class="step">

        <h2>
            Step 4 — Test
        </h2>

        <p>
            After deployment, reconnect/refresh your
            Claude MCP connector.
        </p>

        <p>
            Then test:
        </p>

        <div class="token">
            Get the stats for YouTube video 2jIGinRBkLM
        </div>

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
            content=html,
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
    mcp_http_app,
)
