import os

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

from youtube_auth import create_google_flow

app = FastAPI()


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

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return RedirectResponse(authorization_url)


@app.get("/oauth/callback")
def oauth_callback(code: str):

    flow = create_google_flow()

    flow.fetch_token(code=code)

    credentials = flow.credentials

    return JSONResponse({
        "status": "success",
        "message": "YouTube authorization successful",
        "access_token_received": credentials.token is not None,
        "refresh_token_received": credentials.refresh_token is not None
    })
