import os
from collections import Counter

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# =========================================================
# SCOPES
# =========================================================

YOUTUBE_READONLY_SCOPE = (
    "https://www.googleapis.com/auth/youtube.readonly"
)

YOUTUBE_SCOPE = (
    "https://www.googleapis.com/auth/youtube"
)

YOUTUBE_ANALYTICS_SCOPE = (
    "https://www.googleapis.com/auth/yt-analytics.readonly"
)


# =========================================================
# CREDENTIALS
# =========================================================

def get_credentials():
    """
    Create Google credentials.

    Refresh token is the important persistent credential.
    Access token is optional because Google can refresh it.
    """

    access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not refresh_token:
        raise RuntimeError(
            "YouTube authorization required. "
            "YOUTUBE_REFRESH_TOKEN is missing. "
            "Please visit /oauth/login and save the refresh token "
            "in Render Environment Variables."
        )

    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=[
            YOUTUBE_READONLY_SCOPE,
            YOUTUBE_SCOPE,
            YOUTUBE_ANALYTICS_SCOPE,
        ],
    )


# =========================================================
# YOUTUBE DATA API SERVICE
# =========================================================

def get_youtube_service():

    credentials = get_credentials()

    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )


# =========================================================
# YOUTUBE ANALYTICS SERVICE
# =========================================================

def get_analytics_service():

    credentials = get_credentials()

    return build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials,
        cache_discovery=False
    )


# =========================================================
# 1. CHANNEL ANALYTICS
# =========================================================

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

    try:

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

    except Exception as e:

        return api_error(
            "get_channel_analytics",
            e
        )


# =========================================================
# 2. CHANNEL INFORMATION
# =========================================================

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

    except Exception as e:

        return api_error(
            "get_channel_info",
            e
        )


# =========================================================
# 3. MY VIDEOS
# =========================================================

def get_my_videos(
    max_results=10
):

    try:

        youtube = get_youtube_service()

        max_results = max(
            1,
            min(
                int(max_results),
                50
            )
        )

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
                    "https://www.youtube.com/watch?v="
                    + video_id
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

    except Exception as e:

        return api_error(
            "get_my_videos",
            e
        )


# =========================================================
# 4. VIDEO STATS
# =========================================================

def get_video_stats(
    video_id
):

    try:

        if not video_id:

            return {
                "status": "error",
                "message": "video_id is required."
            }

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part=(
                "snippet,"
                "statistics,"
                "contentDetails"
            ),
            id=video_id
        ).execute()

        if not response.get("items"):

            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id
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

            "duration": (
                content_details.get(
                    "duration"
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
                "https://www.youtube.com/watch?v="
                + video["id"]
            )
        }

    except Exception as e:

        return api_error(
            "get_video_stats",
            e,
            extra={
                "video_id": video_id
            }
        )


# =========================================================
# 5. VIDEO DETAILS
# =========================================================

def get_video_details(
    video_id
):

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
            id=video_id
        ).execute()

        if not response.get("items"):

            return {
                "status": "error",
                "message": "Video not found.",
                "video_id": video_id
            }

        return {
            "status": "success",
            "video": response["items"][0]
        }

    except Exception as e:

        return api_error(
            "get_video_details",
            e,
            extra={
                "video_id": video_id
            }
        )


# =========================================================
# 6. KEYWORD RESEARCH
# =========================================================

def youtube_keyword_research(
    query,
    max_results=20
):

    try:

        youtube = get_youtube_service()

        max_results = max(
            1,
            min(
                int(max_results),
                50
            )
        )

        search_response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results
        ).execute()

        video_ids = []

        results = []

        for item in search_response.get(
            "items",
            []
        ):

            if "videoId" not in item.get(
                "id",
                {}
            ):
                continue

            video_id = item["id"]["videoId"]

            video_ids.append(
                video_id
            )

            snippet = item.get(
                "snippet",
                {}
            )

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
                    "https://www.youtube.com/watch?v="
                    + video_id
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

    except Exception as e:

        return api_error(
            "youtube_keyword_research",
            e,
            extra={
                "query": query
            }
        )


# =========================================================
# 7. TRENDING VIDEOS
# =========================================================

def get_trending_videos(
    region_code="IN",
    category_id=None,
    max_results=10
):

    try:

        youtube = get_youtube_service()

        max_results = max(
            1,
            min(
                int(max_results),
                50
            )
        )

        request = {
            "part": (
                "snippet,"
                "statistics,"
                "contentDetails"
            ),

            "chart": "mostPopular",

            "regionCode": region_code,

            "maxResults": max_results
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
                    "https://www.youtube.com/watch?v="
                    + item["id"]
                )
            })

        return {
            "status": "success",
            "region": region_code,
            "count": len(videos),
            "videos": videos
        }

    except Exception as e:

        return api_error(
            "get_trending_videos",
            e
        )


# =========================================================
# 8. COMMENTS ANALYSIS
# =========================================================

def analyze_video_comments(
    video_id,
    max_results=100
):

    try:

        youtube = get_youtube_service()

        max_results = max(
            1,
            min(
                int(max_results),
                100
            )
        )

        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
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

    except Exception as e:

        return api_error(
            "analyze_video_comments",
            e,
            extra={
                "video_id": video_id
            }
        )


# =========================================================
# 9. VIDEO COMPARISON
# =========================================================

def compare_videos(
    video_ids
):

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
                "message": (
                    "No video IDs provided."
                )
            }

        video_ids = video_ids[:50]

        youtube = get_youtube_service()

        response = youtube.videos().list(
            part=(
                "snippet,"
                "statistics,"
                "contentDetails"
            ),
            id=",".join(video_ids)
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
                    .get(
                        "contentDetails",
                        {}
                    )
                    .get(
                        "duration"
                    )
                ),

                "url": (
                    "https://www.youtube.com/watch?v="
                    + item["id"]
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

    except Exception as e:

        return api_error(
            "compare_videos",
            e
        )


# =========================================================
# 10. GENERAL SEARCH
# =========================================================

def search_youtube(
    query,
    max_results=10
):

    return youtube_keyword_research(
        query=query,
        max_results=max_results
    )


# =========================================================
# ERROR HANDLER
# =========================================================

def api_error(
    tool_name,
    error,
    extra=None
):
    """
    Return useful error information to MCP/Claude
    instead of hiding everything behind
    'Error executing tool'.
    """

    error_type = type(error).__name__

    error_message = str(error)

    result = {
        "status": "error",

        "tool": tool_name,

        "error_type": error_type,

        "error_message": error_message
    }

    if extra:
        result.update(
            extra
        )

    print(
        "\n========== YOUTUBE API ERROR =========="
    )

    print(
        "Tool:",
        tool_name
    )

    print(
        "Type:",
        error_type
    )

    print(
        "Message:",
        error_message
    )

    print(
        "=======================================\n"
    )

    return result
