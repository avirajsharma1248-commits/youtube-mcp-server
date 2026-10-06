import os

from google_auth_oauthlib.flow import Flow


# =========================================================
# YOUTUBE OAUTH SCOPES
# =========================================================

SCOPES = [
    # Read YouTube channel/video data
    "https://www.googleapis.com/auth/youtube.readonly",

    # Manage YouTube channel
    "https://www.googleapis.com/auth/youtube",

    # YouTube Analytics
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


# =========================================================
# CREATE GOOGLE OAUTH FLOW
# =========================================================

def create_google_flow(state=None):

    client_config = {
        "web": {
            "client_id": os.environ[
                "GOOGLE_CLIENT_ID"
            ],

            "client_secret": os.environ[
                "GOOGLE_CLIENT_SECRET"
            ],

            "auth_uri":
                "https://accounts.google.com/o/oauth2/auth",

            "token_uri":
                "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=os.environ[
            "YOUTUBE_REDIRECT_URI"
        ],
    )

    return flow
