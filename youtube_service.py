import os
from typing import Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# ============================================================
# CONFIGURATION
# ============================================================

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_ANALYTICS_SERVICE_NAME = "youtubeAnalytics"
YOUTUBE_ANALYTICS_API_VERSION = "v2"


# ============================================================
# CREDENTIALS
# ============================================================

def get_credentials():
    """
    Get YouTube OAuth credentials.

    Priority:
    1. Existing access token + refresh token
    2. Refresh token alone -> automatically generate access token
    3. Access token alone

    YOUTUBE_REFRESH_TOKEN is the important persistent credential
    for Render deployments/restarts.
    """

    access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is missing from Render environment variables."
        )

    if not client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET is missing from Render environment variables."
        )

    # --------------------------------------------------------
    # Preferred method: refresh token
    # --------------------------------------------------------

    if refresh_token:

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[
                YOUTUBE_SCOPE,
                YOUTUBE_ANALYTICS_SCOPE,
            ],
        )

        # If access token is missing or expired,
        # automatically obtain a new one.
        if not credentials.valid:

            try:
                credentials.refresh(Request())

                # Keep the new access token available
                # during this Render process.
                if credentials.token:
                    os.environ["YOUTUBE_ACCESS_TOKEN"] = credentials.token

            except Exception as e:
                raise RuntimeError(
                    "Unable to refresh YouTube access token. "
                    "Your YOUTUBE_REFRESH_TOKEN may be invalid, revoked, "
                    "or may not contain YouTube write permission. "
                    f"Original error: {str(e)}"
                )

        return credentials

    # --------------------------------------------------------
    # Fallback: access token only
    # --------------------------------------------------------

    if access_token:

        return Credentials(
            token=access_token,
            scopes=[
                YOUTUBE_SCOPE,
                YOUTUBE_ANALYTICS_SCOPE,
            ],
        )

    # --------------------------------------------------------
    # Nothing available
    # --------------------------------------------------------

    raise RuntimeError(
        "YouTube access token unavailable. "
        "Please set YOUTUBE_REFRESH_TOKEN or visit /oauth/login."
    )


# ============================================================
# YOUTUBE SERVICE
# ============================================================

def get_youtube_service():

    credentials = get_credentials()

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# YOUTUBE ANALYTICS SERVICE
# ============================================================

def get_analytics_service():

    credentials = get_credentials()

    return build(
        YOUTUBE_ANALYTICS_SERVICE_NAME,
        YOUTUBE_ANALYTICS_API_VERSION,
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# GET CHANNEL INFO
# ============================================================

def get_channel_info():

    try:

        youtube = get_youtube_service()

        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True
        ).execute()

        if not response.get("items"):
            return {
                "status": "error",
                "message": "No YouTube channel found for this account."
            }

        channel = response["items"][0]

        snippet = channel.get("snippet", {})
        statistics = channel.get("statistics", {})
        content_details = channel.get("contentDetails", {})

        return {
            "status": "success",
            "channel_id": channel.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "custom_url": snippet.get("customUrl"),
            "published_at": snippet.get("publishedAt"),
            "country": snippet.get("country"),
            "thumbnail": snippet.get("thumbnails", {}).get(
                "high", {}
            ).get("url"),
            "subscribers": int(statistics.get("subscriberCount", 0)),
            "views": int(statistics.get("viewCount", 0)),
            "videos": int(statistics.get("videoCount", 0)),
            "uploads_playlist": content_details.get(
                "relatedPlaylists", {}
            ).get("uploads"),
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# GET MY VIDEOS
# ============================================================

def get_my_videos(max_results: int = 20):

    try:

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

        uploads_playlist = (
            channel_response["items"][0]
            ["contentDetails"]
            ["relatedPlaylists"]
            ["uploads"]
        )

        playlist_response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist,
            maxResults=min(max_results, 50)
        ).execute()

        videos = []

        for item in playlist_response.get("items", []):

            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})

            videos.append({
                "video_id": content.get("videoId"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "published_at": snippet.get("publishedAt"),
                "thumbnail": snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url"),
                "url": (
                    f"https://www.youtube.com/watch?v="
                    f"{content.get('videoId')}"
                ),
            })

        return {
            "status": "success",
            "count": len(videos),
            "videos": videos,
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# SEARCH YOUTUBE
# ============================================================

def search_youtube(
    query: str,
    max_results: int = 10
):

    try:

        youtube = get_youtube_service()

        response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=min(max_results, 50)
        ).execute()

        results = []

        for item in response.get("items", []):

            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId")

            results.append({
                "video_id": video_id,
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "thumbnail": snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url"),
                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                    if video_id else None
                ),
            })

        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results,
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# GET VIDEO STATS
# ============================================================

def get_video_stats(video_id: str):

    try:

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()

        if not response.get("items"):

            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id,
            }

        video = response["items"][0]

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        return {
            "status": "success",
            "video_id": video_id,
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "views": int(statistics.get("viewCount", 0)),
            "likes": int(statistics.get("likeCount", 0)),
            "comments": int(statistics.get("commentCount", 0)),
            "duration": content_details.get("duration"),
            "thumbnail": snippet.get("thumbnails", {})
                .get("high", {})
                .get("url"),
            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
            ),
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# GET VIDEO DETAILS
# ============================================================

def get_video_details(video_id: str):

    try:

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part="snippet,statistics,contentDetails,status",
            id=video_id
        ).execute()

        if not response.get("items"):

            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id,
            }

        video = response["items"][0]

        return {
            "status": "success",
            "video_id": video_id,
            "snippet": video.get("snippet", {}),
            "statistics": video.get("statistics", {}),
            "content_details": video.get("contentDetails", {}),
            "status_details": video.get("status", {}),
            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
            ),
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# UPDATE VIDEO TITLE
# ============================================================

def update_video_title(
    video_id: str,
    new_title: str
):

    try:

        # ----------------------------------------------------
        # Validate title
        # ----------------------------------------------------

        if not new_title or not new_title.strip():

            return {
                "status": "error",
                "message": "New title cannot be empty."
            }

        new_title = new_title.strip()

        if len(new_title) > 100:

            return {
                "status": "error",
                "message": (
                    "YouTube titles must be 100 characters "
                    "or fewer."
                ),
                "length": len(new_title),
            }

        # ----------------------------------------------------
        # Get YouTube service
        # ----------------------------------------------------

        youtube = get_youtube_service()

        # ----------------------------------------------------
        # Get existing video
        # ----------------------------------------------------

        existing_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        if not existing_response.get("items"):

            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id,
            }

        existing_video = existing_response["items"][0]

        existing_snippet = existing_video.get(
            "snippet",
            {}
        )

        old_title = existing_snippet.get(
            "title",
            ""
        )

        # ----------------------------------------------------
        # Preserve existing snippet information
        # ----------------------------------------------------

        update_snippet = {
            "title": new_title,
            "description": existing_snippet.get(
                "description",
                ""
            ),
            "categoryId": existing_snippet.get(
                "categoryId",
                "22"
            ),
        }

        # Preserve tags if they exist
        if "tags" in existing_snippet:
            update_snippet["tags"] = existing_snippet["tags"]

        # Preserve default language if available
        if existing_snippet.get("defaultLanguage"):
            update_snippet["defaultLanguage"] = (
                existing_snippet["defaultLanguage"]
            )

        # Preserve audio language if available
        if existing_snippet.get("defaultAudioLanguage"):
            update_snippet["defaultAudioLanguage"] = (
                existing_snippet["defaultAudioLanguage"]
            )

        # ----------------------------------------------------
        # Update YouTube video
        # ----------------------------------------------------

        response = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": update_snippet,
            }
        ).execute()

        updated_snippet = response.get(
            "snippet",
            {}
        )

        return {
            "status": "success",
            "message": "YouTube video title updated successfully.",
            "video_id": video_id,
            "old_title": old_title,
            "new_title": updated_snippet.get(
                "title",
                new_title
            ),
            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
            ),
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
            "video_id": video_id,
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
            "video_id": video_id,
        }


# ============================================================
# KEYWORD RESEARCH
# ============================================================

def youtube_keyword_research(
    query: str,
    max_results: int = 10
):

    try:

        youtube = get_youtube_service()

        search_response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=min(max_results, 50),
            order="viewCount"
        ).execute()

        results = []

        for item in search_response.get("items", []):

            video_id = item.get("id", {}).get(
                "videoId"
            )

            snippet = item.get(
                "snippet",
                {}
            )

            results.append({
                "video_id": video_id,
                "title": snippet.get("title"),
                "channel_title": snippet.get(
                    "channelTitle"
                ),
                "published_at": snippet.get(
                    "publishedAt"
                ),
                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                    if video_id else None
                ),
            })

        return {
            "status": "success",
            "keyword": query,
            "count": len(results),
            "results": results,
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# TRENDING VIDEOS
# ============================================================

def get_trending_videos(
    region_code: str = "IN",
    max_results: int = 10
):

    try:

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            chart="mostPopular",
            regionCode=region_code,
            maxResults=min(max_results, 50)
        ).execute()

        results = []

        for video in response.get("items", []):

            video_id = video.get("id")

            snippet = video.get(
                "snippet",
                {}
            )

            statistics = video.get(
                "statistics",
                {}
            )

            results.append({
                "video_id": video_id,
                "title": snippet.get("title"),
                "channel_title": snippet.get(
                    "channelTitle"
                ),
                "views": int(
                    statistics.get(
                        "viewCount",
                        0
                    )
                ),
                "likes": int(
                    statistics.get(
                        "likeCount",
                        0
                    )
                ),
                "comments": int(
                    statistics.get(
                        "commentCount",
                        0
                    )
                ),
                "published_at": snippet.get(
                    "publishedAt"
                ),
                "thumbnail": snippet.get(
                    "thumbnails",
                    {}
                ).get(
                    "high",
                    {}
                ).get("url"),
                "url": (
                    f"https://www.youtube.com/watch?v="
                    f"{video_id}"
                ),
            })

        return {
            "status": "success",
            "region_code": region_code,
            "count": len(results),
            "videos": results,
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# ANALYZE VIDEO COMMENTS
# ============================================================

def analyze_video_comments(
    video_id: str,
    max_results: int = 50
):

    try:

        youtube = get_youtube_service()

        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_results, 100),
            textFormat="plainText"
        ).execute()

        comments = []

        for item in response.get("items", []):

            top_comment = (
                item
                .get("snippet", {})
                .get("topLevelComment", {})
                .get("snippet", {})
            )

            comments.append({
                "author": top_comment.get(
                    "authorDisplayName"
                ),
                "text": top_comment.get(
                    "textDisplay"
                ),
                "likes": int(
                    top_comment.get(
                        "likeCount",
                        0
                    )
                ),
                "published_at": top_comment.get(
                    "publishedAt"
                ),
                "updated_at": top_comment.get(
                    "updatedAt"
                ),
            })

        positive_words = [
            "love",
            "good",
            "great",
            "nice",
            "awesome",
            "amazing",
            "best",
            "wow",
            "funny",
        ]

        negative_words = [
            "bad",
            "worst",
            "hate",
            "boring",
            "fake",
            "poor",
            "waste",
        ]

        positive_count = 0
        negative_count = 0

        for comment in comments:

            text = (
                comment.get("text") or ""
            ).lower()

            if any(
                word in text
                for word in positive_words
            ):
                positive_count += 1

            if any(
                word in text
                for word in negative_words
            ):
                negative_count += 1

        return {
            "status": "success",
            "video_id": video_id,
            "comment_count": len(comments),
            "positive_signals": positive_count,
            "negative_signals": negative_count,
            "comments": comments,
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# COMPARE VIDEOS
# ============================================================

def compare_videos(
    video_ids: List[str]
):

    try:

        youtube = get_youtube_service()

        if isinstance(video_ids, str):
            video_ids = [
                x.strip()
                for x in video_ids.split(",")
                if x.strip()
            ]

        if not video_ids:

            return {
                "status": "error",
                "message": "No video IDs provided."
            }

        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()

        results = []

        for video in response.get("items", []):

            video_id = video.get("id")

            snippet = video.get(
                "snippet",
                {}
            )

            statistics = video.get(
                "statistics",
                {}
            )

            results.append({
                "video_id": video_id,
                "title": snippet.get("title"),
                "views": int(
                    statistics.get(
                        "viewCount",
                        0
                    )
                ),
                "likes": int(
                    statistics.get(
                        "likeCount",
                        0
                    )
                ),
                "comments": int(
                    statistics.get(
                        "commentCount",
                        0
                    )
                ),
                "published_at": snippet.get(
                    "publishedAt"
                ),
                "url": (
                    f"https://www.youtube.com/watch?v="
                    f"{video_id}"
                ),
            })

        return {
            "status": "success",
            "count": len(results),
            "videos": results,
        }

    except HttpError as e:

        return {
            "status": "error",
            "error_type": "YouTubeAPIError",
            "error": str(e),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# END OF FILE
# ============================================================
