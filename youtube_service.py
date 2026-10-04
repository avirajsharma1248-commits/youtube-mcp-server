import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def get_youtube_service():
    access_token = os.environ.get("YOUTUBE_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError("YOUTUBE_ACCESS_TOKEN is not configured")

    credentials = Credentials(token=access_token)

    return build(
        "youtube",
        "v3",
        credentials=credentials
    )


def get_my_channel():
    youtube = get_youtube_service()

    response = youtube.channels().list(
        part="snippet,statistics",
        mine=True
    ).execute()

    return response
