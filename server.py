import secrets

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

from youtube_auth import create_google_flow


app = FastAPI()

oauth_states = {}


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

    flow = create_google_flow()

    state = secrets.token_urlsafe(32)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )

    oauth_states[state] = flow

    return RedirectResponse(authorization_url)


@app.get("/oauth/callback")
def oauth_callback(code: str, state: str):

    flow = oauth_states.pop(state, None)

    if flow is None:
        return JSONResponse(
            {
                "status": "error",
                "message": "OAuth session expired or invalid."
            },
            status_code=400
        )

    try:

        flow.fetch_token(code=code)

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
