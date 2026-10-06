import os
from collections import Counter

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# ============================================================
# SCOPES
# ============================================================

# Write-enabled YouTube scope.
# This is required for videos.update().
YOUTUBE_SCOPE = (
    "https://www.googleapis.com/auth/youtube"
)

YOUTUBE_ANALYTICS_SCOPE = (
    "https://www.googleapis.com/auth/yt-analytics.readonly"
)


# ============================================================
# CREDENTIALS
# ============================================================

def get_credentials():

    access_token = os.getenv(
        "YOUTUBE_ACCESS_TOKEN"
    )

    refresh_token = os.getenv(
        "YOUTUBE_REFRESH_TOKEN"
    )

    client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    if not refresh_token and not access_token:
        raise RuntimeError(
            "YouTube authorization required. "
            "Please visit /oauth/login."
        )

    if not client_id:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID environment variable is missing."
        )

    if not client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET environment variable is missing."
        )

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[
            YOUTUBE_SCOPE,
            YOUTUBE_ANALYTICS_SCOPE
        ],
    )

    # --------------------------------------------------------
    # Refresh access token automatically
    # --------------------------------------------------------

    if not credentials.valid:

        if credentials.expired and credentials.refresh_token:

            credentials.refresh(
                Request()
            )

        elif not credentials.token:

            raise RuntimeError(
                "YouTube access token is unavailable. "
                "Please visit /oauth/login."
            )

    # Keep latest access token in process memory.
    # Do NOT store the token in GitHub.
    if credentials.token:

        os.environ[
            "YOUTUBE_ACCESS_TOKEN"
        ] = credentials.token

    return credentials


# ============================================================
# YOUTUBE DATA API
# ============================================================

def get_youtube_service():

    credentials = get_credentials()

    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False
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
        cache_discovery=False
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
    )
):

    youtube = get_youtube_service()

    channel_response = youtube.channels().list(
        part="id,snippet,statistics",
        mine=True
    ).execute()

    if not channel_response.get("items"):

        return {
            "status": "error",
            "message": "No YouTube channel found."
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
        sort="day"
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
        )
    }


# ============================================================
# 2. CHANNEL INFORMATION
# ============================================================

def get_channel_info():

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

        "channel_name": snippet.get(
            "title"
        ),

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
            .get(
                "relatedPlaylists",
                {}
            )
            .get(
                "uploads"
            )
        )
    }


# ============================================================
# 3. MY VIDEOS
# ============================================================

def get_my_videos(
    max_results=10
):

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
        maxResults=min(
            max_results,
            50
        )
    ).execute()

    videos = []

    video_ids = []

    for item in playlist_response.get(
        "items",
        []
    ):

        video_id = (
            item["contentDetails"]
            ["videoId"]
        )

        video_ids.append(
            video_id
        )

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
                .get(
                    "thumbnails",
                    {}
                )
                .get(
                    "high",
                    {}
                )
                .get(
                    "url"
                )
            ),

            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
            )
        })

    if video_ids:

        stats_response = youtube.videos().list(
            part="statistics,contentDetails",
            id=",".join(video_ids)
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
        "videos": videos
    }


# ============================================================
# 4. VIDEO STATS
# ============================================================

def get_video_stats(
    video_id
):

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

        "title": snippet.get(
            "title"
        ),

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
            .get(
                "thumbnails",
                {}
            )
            .get(
                "high",
                {}
            )
            .get(
                "url"
            )
        ),

        "url": (
            f"https://www.youtube.com/watch?v={video['id']}"
        )
    }


# ============================================================
# 5. VIDEO DETAILS
# ============================================================

def get_video_details(
    video_id
):

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
        id=video_id
    ).execute()

    if not response.get("items"):

        return {
            "status": "error",
            "message": "Video not found."
        }

    return {
        "status": "success",
        "video": response["items"][0]
    }


# ============================================================
# 6. SEARCH YOUTUBE / KEYWORD RESEARCH
# ============================================================

def youtube_keyword_research(
    query,
    max_results=20
):

    youtube = get_youtube_service()

    search_response = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=min(
            max_results,
            50
        )
    ).execute()

    video_ids = []

    results = []

    for item in search_response.get(
        "items",
        []
    ):

        video_id = item["id"]["videoId"]

        video_ids.append(
            video_id
        )

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
                .get(
                    "thumbnails",
                    {}
                )
                .get(
                    "high",
                    {}
                )
                .get(
                    "url"
                )
            ),

            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
            )
        })

    if video_ids:

        stats_response = youtube.videos().list(
            part="statistics",
            id=",".join(video_ids)
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
        "results": results
    }


# ============================================================
# 7. TRENDING VIDEOS
# ============================================================

def get_trending_videos(
    region_code="IN",
    category_id=None,
    max_results=10
):

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
        )
    }

    if category_id:

        request[
            "videoCategoryId"
        ] = str(
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
                .get(
                    "thumbnails",
                    {}
                )
                .get(
                    "high",
                    {}
                )
                .get(
                    "url"
                )
            ),

            "url": (
                f"https://www.youtube.com/watch?v={item['id']}"
            )
        })

    return {
        "status": "success",
        "region": region_code,
        "count": len(videos),
        "videos": videos
    }


# ============================================================
# 8. COMMENTS ANALYSIS
# ============================================================

def analyze_video_comments(
    video_id,
    max_results=100
):

    youtube = get_youtube_service()

    response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=min(
            max_results,
            100
        ),
        textFormat="plainText"
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
            )
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
        "common_words": common_words
    }


# ============================================================
# 9. VIDEO PERFORMANCE COMPARISON
# ============================================================

def compare_videos(
    video_ids
):

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
            "message": "No video IDs provided."
        }

    youtube = get_youtube_service()

    response = youtube.videos().list(
        part=(
            "snippet,"
            "statistics,"
            "contentDetails"
        ),
        id=",".join(
            video_ids
        )
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
                item.get(
                    "contentDetails",
                    {}
                ).get(
                    "duration"
                )
            ),

            "url": (
                f"https://www.youtube.com/watch?v={item['id']}"
            )
        })

    videos.sort(
        key=lambda x: x["views"],
        reverse=True
    )

    return {
        "status": "success",
        "count": len(videos),
        "videos": videos
    }


# ============================================================
# 10. GENERAL YOUTUBE SEARCH
# ============================================================

def search_youtube(
    query,
    max_results=10
):

    return youtube_keyword_research(
        query=query,
        max_results=max_results
    )


# ============================================================
# 11. UPDATE VIDEO TITLE
# ============================================================

def update_video_title(
    video_id,
    new_title
):
    """
    Update the title of a YouTube video owned
    by the authenticated account.

    The existing description, tags and category
    are preserved.
    """

    try:

        youtube = get_youtube_service()

        # ----------------------------------------------------
        # Validate video ID
        # ----------------------------------------------------

        video_id = str(
            video_id
        ).strip()

        if not video_id:

            return {
                "status": "error",
                "tool": "update_video_title",
                "message": "Video ID cannot be empty."
            }

        # ----------------------------------------------------
        # Validate title
        # ----------------------------------------------------

        if new_title is None:

            return {
                "status": "error",
                "tool": "update_video_title",
                "message": "New title is required."
            }

        new_title = str(
            new_title
        ).strip()

        if not new_title:

            return {
                "status": "error",
                "tool": "update_video_title",
                "message": "New title cannot be empty."
            }

        # YouTube title limit
        if len(new_title) > 100:

            return {
                "status": "error",
                "tool": "update_video_title",
                "message": (
                    "YouTube titles must be 100 characters "
                    "or fewer."
                ),
                "character_count": len(
                    new_title
                )
            }

        # ----------------------------------------------------
        # Get current video
        # ----------------------------------------------------

        response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        items = response.get(
            "items",
            []
        )

        if not items:

            return {
                "status": "error",
                "tool": "update_video_title",
                "message": "Video not found.",
                "video_id": video_id
            }

        video = items[0]

        snippet = video.get(
            "snippet",
            {}
        )

        old_title = snippet.get(
            "title",
            ""
        )

        # ----------------------------------------------------
        # Prevent unnecessary API update
        # ----------------------------------------------------

        if old_title == new_title:

            return {
                "status": "success",
                "message": "Title is already the same.",
                "video_id": video_id,
                "old_title": old_title,
                "new_title": new_title,
                "changed": False,
                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                )
            }

        # ----------------------------------------------------
        # Preserve existing metadata
        # ----------------------------------------------------

        category_id = snippet.get(
            "categoryId"
        )

        if not category_id:

            return {
                "status": "error",
                "tool": "update_video_title",
                "message": (
                    "Could not determine the video's "
                    "category ID."
                )
            }

        body = {
            "id": video_id,

            "snippet": {

                "title": new_title,

                "categoryId": category_id,

                "description": snippet.get(
                    "description",
                    ""
                ),

                "tags": snippet.get(
                    "tags",
                    []
                ),

                "defaultLanguage": snippet.get(
                    "defaultLanguage"
                ),

                "defaultAudioLanguage": snippet.get(
                    "defaultAudioLanguage"
                )
            }
        }

        # Remove None values from snippet.
        body["snippet"] = {
            key: value
            for key, value in body["snippet"].items()
            if value is not None
        }

        # ----------------------------------------------------
        # Update YouTube
        # ----------------------------------------------------

        updated = youtube.videos().update(
            part="snippet",
            body=body
        ).execute()

        updated_title = (
            updated
            .get("snippet", {})
            .get("title")
        )

        return {
            "status": "success",
            "message": "Video title updated successfully.",
            "video_id": video_id,
            "old_title": old_title,
            "new_title": updated_title,
            "changed": True,
            "character_count": len(
                updated_title or ""
            ),
            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
            )
        }

    except Exception as e:

        return {
            "status": "error",
            "tool": "update_video_title",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "video_id": video_id
        }
