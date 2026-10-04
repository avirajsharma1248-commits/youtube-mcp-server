import secrets

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse

from youtube_auth import create_google_flow


app = FastAPI()

oauth_sessions = {}


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "YouTube MCP Server"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/oauth/login")
def oauth_login():

    state = secrets.token_urlsafe(32)

    flow = create_google_flow(state=state)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
        code_challenge_method="S256"
    )

    # IMPORTANT:
    # Flow's internal OAuth2Session contains the PKCE verifier.
    oauth_sessions[state] = flow

    return RedirectResponse(authorization_url)


@app.get("/oauth/callback")
def oauth_callback(code: str, state: str):

    flow = oauth_sessions.pop(state, None)

    if flow is None:
        return JSONResponse(
            {
                "status": "error",
                "message": "OAuth session not found. Start login again."
            },
            status_code=400
        )

    try:

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        return JSONResponse({
            "status": "success",
            "message": "YouTube authorization successful",
            "access_token_received": credentials.token is not None,
            "refresh_token_received": credentials.refresh_token is not None
        })

    except Exception as e:

        return JSONResponse(
            {
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )
