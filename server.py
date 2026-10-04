import secrets

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

from youtube_auth import create_google_flow


app = FastAPI()

# Temporary OAuth session storage
oauth_sessions = {}


# -------------------------
# Home
# -------------------------

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "YouTube MCP Server"
    }


# -------------------------
# Health
# -------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# -------------------------
# Start Google OAuth
# -------------------------

@app.get("/oauth/login")
def oauth_login():

    # Create unique OAuth state
    state = secrets.token_urlsafe(32)

    # Create Google OAuth flow
    flow = create_google_flow(state=state)

    # Generate Google authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
        code_challenge_method="S256"
    )

    # Save flow so we can use the same
    # PKCE verifier during callback
    oauth_sessions[state] = flow

    # Send user to Google
    return RedirectResponse(authorization_url)


# -------------------------
# Google OAuth Callback
# -------------------------

@app.get("/oauth/callback")
def oauth_callback(code: str, state: str):

    # Get the original OAuth flow
    flow = oauth_sessions.pop(state, None)

    # If flow doesn't exist
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
        # for Google access/refresh tokens
        flow.fetch_token(code=code)

        credentials = flow.credentials

        return JSONResponse(
            {
                "status": "success",
                "message": "YouTube authorization successful",
                "access_token_received": bool(credentials.token),
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
