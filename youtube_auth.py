import os

from google_auth_oauthlib.flow import Flow


SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def create_google_flow(state=None):

    client_id = os.environ.get(
        "GOOGLE_CLIENT_ID"
    )

    client_secret = os.environ.get(
        "GOOGLE_CLIENT_SECRET"
    )

    redirect_uri = os.environ.get(
        "YOUTUBE_REDIRECT_URI"
    )

    if not client_id:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID environment variable is missing."
        )

    if not client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET environment variable is missing."
        )

    if not redirect_uri:
        raise RuntimeError(
            "YOUTUBE_REDIRECT_URI environment variable is missing."
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
                redirect_uri
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
    )

    return flow
