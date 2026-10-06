import os
from collections import Counter

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# ============================================================
# CONFIGURATION
# ============================================================

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_ANALYTICS_SCOPE = (
    "https://www.googleapis.com/auth/yt-analytics.readonly"
)


# ============================================================
# CREDENTIALS
# ============================================================

def get_credentials():
    """
    Get YouTube credentials.

    Render should permanently store YOUTUBE_REFRESH_TOKEN.
    The access token can expire/disappear; the refresh token
    is used to automatically obtain a new access token.
    """

    access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is missing from Render Environment."
        )

    if not client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET is missing from Render Environment."
        )

    # --------------------------------------------------------
    # PREFERRED: refresh-token authentication
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

        # Access token missing or expired
        if not credentials.valid:

            try:
                credentials.refresh(Request())

                if not credentials.token:
                    raise RuntimeError(
                        "Google returned no access token."
                    )

                # Keep the new access token available
                # for the current Render process.
                os.environ["YOUTUBE_ACCESS_TOKEN"] = (
                    credentials.token
                )

            except Exception as e:

                raise RuntimeError(
                    "YouTube OAuth refresh failed. "
                    "Check YOUTUBE_REFRESH_TOKEN and Google OAuth permissions. "
                    f"Details: {str(e)}"
                )

        return credentials

    # --------------------------------------------------------
    # FALLBACK: access token only
    # --------------------------------------------------------

    if access_token:

        return Credentials(
            token=access_token,
            scopes=[
                YOUTUBE_SCOPE,
                YOUTUBE_ANALYTICS_SCOPE,
            ],
        )

    raise RuntimeError(
        "YouTube access token unavailable. "
        "YOUTUBE_REFRESH_TOKEN is missing. "
        "Please visit /oauth/login."
    )


# ============================================================
# YOUTUBE DATA API
# ============================================================

def get_youtube_service():

    credentials = get_credentials()

    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# YOUTUBE ANALYTICS API
# ============================================================

def get_analytics_service():

    credentials = get_credentials()

    return build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# 1. CHANNEL ANALYTICS
# ============================================================

def get_channel_analytics(
    start_date,
    end_date,
    metrics=(
        "views,"
        "estimatedMinutesWatched,"
        "averageViewDuration,"
        "subscribersGained,"
        "subscribersLost"
    ),
):

    try:

        youtube = get_youtube_service()

        channel_response = youtube.channels().list(
            part="id,snippet,statistics",
            mine=True,
        ).execute()

        if not channel_response.get("items"):
            return {
                "status": "error",
                "message": "No YouTube channel found.",
            }

        channel = channel_response["items"][0]
        channel_id = channel["id"]

        analytics = get_analytics_service()

        response = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics=metrics,
            dimensions="day",
            sort="day",
        ).execute()

        return {
            "status": "success",
            "channel_id": channel_id,
            "channel_name": channel["snippet"]["title"],
            "start_date": start_date,
            "end_date": end_date,
            "headers": response.get(
                "columnHeaders",
                []
            ),
            "rows": response.get(
                "rows",
                []
            ),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 2. CHANNEL INFORMATION
# ============================================================

def get_channel_info():

    try:

        youtube = get_youtube_service()

        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True,
        ).execute()

        if not response.get("items"):
            return {
                "status": "error",
                "message": "No YouTube channel found.",
            }

        channel = response["items"][0]

        snippet = channel.get(
            "snippet",
            {}
        )

        statistics = channel.get(
            "statistics",
            {}
        )

        content_details = channel.get(
            "contentDetails",
            {}
        )

        return {
            "status": "success",
            "channel_id": channel["id"],
            "channel_name": snippet.get("title"),
            "description": snippet.get(
                "description",
                ""
            ),
            "published_at": snippet.get(
                "publishedAt"
            ),
            "subscriber_count": int(
                statistics.get(
                    "subscriberCount",
                    0
                )
            ),
            "view_count": int(
                statistics.get(
                    "viewCount",
                    0
                )
            ),
            "video_count": int(
                statistics.get(
                    "videoCount",
                    0
                )
            ),
            "uploads_playlist_id": (
                content_details
                .get("relatedPlaylists", {})
                .get("uploads")
            ),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 3. MY VIDEOS
# ============================================================

def get_my_videos(max_results=10):

    try:

        youtube = get_youtube_service()

        channel_response = youtube.channels().list(
            part="contentDetails",
            mine=True,
        ).execute()

        if not channel_response.get("items"):
            return {
                "status": "error",
                "message": "No YouTube channel found.",
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
            maxResults=min(max_results, 50),
        ).execute()

        videos = []
        video_ids = []

        for item in playlist_response.get(
            "items",
            []
        ):

            video_id = (
                item["contentDetails"]["videoId"]
            )

            video_ids.append(video_id)

            snippet = item.get(
                "snippet",
                {}
            )

            videos.append({
                "video_id": video_id,
                "title": snippet.get(
                    "title",
                    ""
                ),
                "description": snippet.get(
                    "description",
                    ""
                ),
                "published_at": snippet.get(
                    "publishedAt"
                ),
                "thumbnail": (
                    snippet
                    .get("thumbnails", {})
                    .get("high", {})
                    .get("url")
                ),
                "url": (
                    "https://www.youtube.com/watch?v="
                    + video_id
                ),
            })

        if video_ids:

            stats_response = youtube.videos().list(
                part="statistics,contentDetails",
                id=",".join(video_ids),
            ).execute()

            stats = {
                item["id"]: item
                for item in stats_response.get(
                    "items",
                    []
                )
            }

            for video in videos:

                item = stats.get(
                    video["video_id"],
                    {}
                )

                statistics = item.get(
                    "statistics",
                    {}
                )

                content_details = item.get(
                    "contentDetails",
                    {}
                )

                video["views"] = int(
                    statistics.get(
                        "viewCount",
                        0
                    )
                )

                video["likes"] = int(
                    statistics.get(
                        "likeCount",
                        0
                    )
                )

                video["comments"] = int(
                    statistics.get(
                        "commentCount",
                        0
                    )
                )

                video["duration"] = (
                    content_details.get(
                        "duration"
                    )
                )

        return {
            "status": "success",
            "count": len(videos),
            "videos": videos,
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 4. VIDEO STATS
# ============================================================

def get_video_stats(video_id):

    try:

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id,
        ).execute()

        if not response.get("items"):
            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id,
            }

        video = response["items"][0]

        snippet = video.get(
            "snippet",
            {}
        )

        statistics = video.get(
            "statistics",
            {}
        )

        content_details = video.get(
            "contentDetails",
            {}
        )

        return {
            "status": "success",
            "video_id": video["id"],
            "title": snippet.get("title"),
            "description": snippet.get(
                "description",
                ""
            ),
            "channel_id": snippet.get(
                "channelId"
            ),
            "channel_title": snippet.get(
                "channelTitle"
            ),
            "published_at": snippet.get(
                "publishedAt"
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
            "duration": content_details.get(
                "duration"
            ),
            "thumbnail": (
                snippet
                .get("thumbnails", {})
                .get("high", {})
                .get("url")
            ),
            "url": (
                "https://www.youtube.com/watch?v="
                + video["id"]
            ),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 5. VIDEO DETAILS
# ============================================================

def get_video_details(video_id):

    try:

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part=(
                "snippet,"
                "statistics,"
                "contentDetails,"
                "topicDetails,"
                "status,"
                "recordingDetails"
            ),
            id=video_id,
        ).execute()

        if not response.get("items"):
            return {
                "status": "error",
                "message": "Video not found.",
            }

        return {
            "status": "success",
            "video": response["items"][0],
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 6. YOUTUBE KEYWORD RESEARCH
# ============================================================

def youtube_keyword_research(
    query,
    max_results=20
):

    try:

        youtube = get_youtube_service()

        search_response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=min(
                max_results,
                50
            ),
        ).execute()

        video_ids = []
        results = []

        for item in search_response.get(
            "items",
            []
        ):

            video_id = item["id"]["videoId"]

            video_ids.append(video_id)

            snippet = item["snippet"]

            results.append({
                "video_id": video_id,
                "title": snippet.get(
                    "title",
                    ""
                ),
                "channel_title": snippet.get(
                    "channelTitle"
                ),
                "published_at": snippet.get(
                    "publishedAt"
                ),
                "description": snippet.get(
                    "description",
                    ""
                ),
                "thumbnail": (
                    snippet
                    .get("thumbnails", {})
                    .get("high", {})
                    .get("url")
                ),
                "url": (
                    "https://www.youtube.com/watch?v="
                    + video_id
                ),
            })

        if video_ids:

            stats_response = youtube.videos().list(
                part="statistics",
                id=",".join(video_ids),
            ).execute()

            stats = {
                item["id"]: item.get(
                    "statistics",
                    {}
                )
                for item in stats_response.get(
                    "items",
                    []
                )
            }

            for result in results:

                statistics = stats.get(
                    result["video_id"],
                    {}
                )

                result["views"] = int(
                    statistics.get(
                        "viewCount",
                        0
                    )
                )

                result["likes"] = int(
                    statistics.get(
                        "likeCount",
                        0
                    )
                )

                result["comments"] = int(
                    statistics.get(
                        "commentCount",
                        0
                    )
                )

        return {
            "status": "success",
            "keyword": query,
            "result_count": len(results),
            "results": results,
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 7. SEARCH YOUTUBE
# ============================================================

def search_youtube(
    query,
    max_results=10
):

    return youtube_keyword_research(
        query=query,
        max_results=max_results,
    )


# ============================================================
# 8. TRENDING VIDEOS
# ============================================================

def get_trending_videos(
    region_code="IN",
    category_id=None,
    max_results=10
):

    try:

        youtube = get_youtube_service()

        request = {
            "part": (
                "snippet,"
                "statistics,"
                "contentDetails"
            ),
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": min(
                max_results,
                50
            ),
        }

        if category_id:
            request["videoCategoryId"] = str(
                category_id
            )

        response = youtube.videos().list(
            **request
        ).execute()

        videos = []

        for item in response.get(
            "items",
            []
        ):

            snippet = item.get(
                "snippet",
                {}
            )

            statistics = item.get(
                "statistics",
                {}
            )

            videos.append({
                "video_id": item["id"],
                "title": snippet.get(
                    "title"
                ),
                "channel_title": snippet.get(
                    "channelTitle"
                ),
                "published_at": snippet.get(
                    "publishedAt"
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
                "thumbnail": (
                    snippet
                    .get("thumbnails", {})
                    .get("high", {})
                    .get("url")
                ),
                "url": (
                    "https://www.youtube.com/watch?v="
                    + item["id"]
                ),
            })

        return {
            "status": "success",
            "region": region_code,
            "count": len(videos),
            "videos": videos,
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 9. ANALYZE VIDEO COMMENTS
# ============================================================

def analyze_video_comments(
    video_id,
    max_results=100
):

    try:

        youtube = get_youtube_service()

        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(
                max_results,
                100
            ),
            textFormat="plainText",
        ).execute()

        comments = []
        words = []

        for item in response.get(
            "items",
            []
        ):

            comment = (
                item["snippet"]
                ["topLevelComment"]
                ["snippet"]
            )

            text = comment.get(
                "textDisplay",
                ""
            )

            comments.append({
                "author": comment.get(
                    "authorDisplayName"
                ),
                "text": text,
                "likes": comment.get(
                    "likeCount",
                    0
                ),
                "published_at": comment.get(
                    "publishedAt"
                ),
            })

            words.extend(
                text.lower().split()
            )

        common_words = Counter(
            words
        ).most_common(20)

        return {
            "status": "success",
            "video_id": video_id,
            "comment_count_analyzed": len(
                comments
            ),
            "comments": comments,
            "common_words": common_words,
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 10. COMPARE VIDEOS
# ============================================================

def compare_videos(video_ids):

    try:

        if isinstance(
            video_ids,
            str
        ):

            video_ids = [
                x.strip()
                for x in video_ids.split(",")
                if x.strip()
            ]

        if not video_ids:
            return {
                "status": "error",
                "message": "No video IDs provided.",
            }

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part=(
                "snippet,"
                "statistics,"
                "contentDetails"
            ),
            id=",".join(video_ids),
        ).execute()

        videos = []

        for item in response.get(
            "items",
            []
        ):

            snippet = item.get(
                "snippet",
                {}
            )

            statistics = item.get(
                "statistics",
                {}
            )

            videos.append({
                "video_id": item["id"],
                "title": snippet.get(
                    "title"
                ),
                "published_at": snippet.get(
                    "publishedAt"
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
                "duration": (
                    item
                    .get("contentDetails", {})
                    .get("duration")
                ),
                "url": (
                    "https://www.youtube.com/watch?v="
                    + item["id"]
                ),
            })

        videos.sort(
            key=lambda x: x["views"],
            reverse=True,
        )

        return {
            "status": "success",
            "count": len(videos),
            "videos": videos,
        }

    except Exception as e:

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e),
        }


# ============================================================
# 11. UPDATE VIDEO TITLE
# ============================================================

def update_video_title(
    video_id,
    new_title
):

    try:

        if not new_title:
            return {
                "status": "error",
                "message": "New title cannot be empty.",
            }

        new_title = new_title.strip()

        if not new_title:
            return {
                "status": "error",
                "message": "New title cannot be empty.",
            }

        if len(new_title) > 100:
            return {
                "status": "error",
                "message": (
                    "YouTube title must be 100 characters "
                    "or fewer."
                ),
                "length": len(new_title),
            }

        youtube = get_youtube_service()

        # Get the current snippet first.
        response = youtube.videos().list(
            part="snippet",
            id=video_id,
        ).execute()

        if not response.get("items"):
            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id,
            }

        existing = response["items"][0]

        old_snippet = existing.get(
            "snippet",
            {}
        )

        old_title = old_snippet.get(
            "title",
            ""
        )

        # YouTube requires categoryId when updating snippet.
        category_id = old_snippet.get(
            "categoryId"
        )

        if not category_id:
            category_id = "22"

        update_snippet = {
            "title": new_title,
            "description": old_snippet.get(
                "description",
                ""
            ),
            "categoryId": category_id,
        }

        # Preserve tags.
        if "tags" in old_snippet:
            update_snippet["tags"] = old_snippet["tags"]

        # Preserve language settings.
        if old_snippet.get(
            "defaultLanguage"
        ):
            update_snippet["defaultLanguage"] = (
                old_snippet["defaultLanguage"]
            )

        if old_snippet.get(
            "defaultAudioLanguage"
        ):
            update_snippet["defaultAudioLanguage"] = (
                old_snippet["defaultAudioLanguage"]
            )

        # Perform the actual update.
        updated = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": update_snippet,
            },
        ).execute()

        updated_title = (
            updated
            .get("snippet", {})
            .get("title", new_title)
        )

        return {
            "status": "success",
            "message": (
                "YouTube video title updated successfully."
            ),
            "video_id": video_id,
            "old_title": old_title,
            "new_title": updated_title,
            "url": (
                "https://www.youtube.com/watch?v="
                + video_id
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
