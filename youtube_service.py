import os
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def get_credentials():
    """
    Create Google credentials from environment variables.
    """

    access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not access_token:
        raise RuntimeError(
            "YOUTUBE_ACCESS_TOKEN is not configured."
        )

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=[
            "https://www.googleapis.com/auth/youtube.readonly"
        ],
    )

    return credentials


def get_youtube_service():
    """
    Create authenticated YouTube Data API client.
    """

    credentials = get_credentials()

    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        credentials=credentials,
        cache_discovery=False
    )

    return youtube


def get_channel_info():
    """
    Get authenticated user's YouTube channel information.
    """

    youtube = get_youtube_service()

    response = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        mine=True
    ).execute()

    if not response.get("items"):
        return {
            "status": "error",
            "message": "No YouTube channel found."
        }

    channel = response["items"][0]

    return {
        "status": "success",
        "channel_id": channel["id"],
        "title": channel["snippet"]["title"],
        "description": channel["snippet"].get("description", ""),
        "published_at": channel["snippet"].get("publishedAt"),
        "statistics": channel.get("statistics", {}),
        "uploads_playlist_id": (
            channel.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
    }


def get_my_videos(max_results=10):
    """
    Get videos uploaded to the authenticated user's channel.
    """

    youtube = get_youtube_service()

    channel_response = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    if not channel_response.get("items"):
        return {
            "status": "error",
            "message": "No YouTube channel found."
        }

    uploads_playlist_id = (
        channel_response["items"][0]
        ["contentDetails"]
        ["relatedPlaylists"]
        ["uploads"]
    )

    playlist_response = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=max_results
    ).execute()

    videos = []

    for item in playlist_response.get("items", []):

        videos.append({
            "video_id": item["contentDetails"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "published_at": item["snippet"].get("publishedAt"),
            "thumbnail": (
                item["snippet"]
                .get("thumbnails", {})
                .get("high", {})
                .get("url")
            )
        })

    return {
        "status": "success",
        "count": len(videos),
        "videos": videos
    }


def search_youtube(query, max_results=10):
    """
    Search YouTube videos.
    """

    youtube = get_youtube_service()

    response = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    ).execute()

    results = []

    for item in response.get("items", []):

        results.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "channel_id": item["snippet"]["channelId"],
            "channel_title": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"],
            "thumbnail": (
                item["snippet"]
                .get("thumbnails", {})
                .get("high", {})
                .get("url")
            )
        })

    return {
        "status": "success",
        "query": query,
        "count": len(results),
        "results": results
    }


def get_video_stats(video_id):
    """
    Get statistics and details for a YouTube video.
    """

    youtube = get_youtube_service()

    response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()

    if not response.get("items"):
        return {
            "status": "error",
            "message": "Video not found."
        }

    video = response["items"][0]

    return {
        "status": "success",
        "video_id": video["id"],
        "title": video["snippet"]["title"],
        "description": video["snippet"].get("description", ""),
        "channel_id": video["snippet"]["channelId"],
        "published_at": video["snippet"]["publishedAt"],
        "statistics": video.get("statistics", {}),
        "duration": video.get("contentDetails", {}).get("duration")
    }
