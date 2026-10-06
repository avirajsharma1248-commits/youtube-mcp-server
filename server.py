import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

YOUTUBE_SCOPE = (
    "https://www.googleapis.com/auth/youtube.readonly"
)


# =========================================================
# GET YOUTUBE CREDENTIALS
# =========================================================

def get_credentials():

    access_token = os.getenv(
        "YOUTUBE_ACCESS_TOKEN"
    )

    refresh_token = os.getenv(
        "YOUTUBE_REFRESH_TOKEN"
    )

    if not access_token:
        raise RuntimeError(
            "YouTube authorization required. "
            "Please visit /oauth/login first."
        )

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv(
            "GOOGLE_CLIENT_ID"
        ),
        client_secret=os.getenv(
            "GOOGLE_CLIENT_SECRET"
        ),
        scopes=[
            YOUTUBE_SCOPE
        ],
    )

    return credentials


# =========================================================
# GET YOUTUBE SERVICE
# =========================================================

def get_youtube_service():

    credentials = get_credentials()

    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        credentials=credentials,
        cache_discovery=False
    )

    return youtube


# =========================================================
# CHANNEL INFORMATION
# =========================================================

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

    statistics = channel.get(
        "statistics",
        {}
    )

    snippet = channel.get(
        "snippet",
        {}
    )

    content_details = channel.get(
        "contentDetails",
        {}
    )

    return {
        "status": "success",

        "channel_id": channel.get(
            "id"
        ),

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

        "country": snippet.get(
            "country"
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

        "hidden_subscriber_count": statistics.get(
            "hiddenSubscriberCount",
            False
        ),

        "uploads_playlist_id": (
            content_details
            .get("relatedPlaylists", {})
            .get("uploads")
        )
    }


# =========================================================
# GET MY VIDEOS
# =========================================================

def get_my_videos(
    max_results=10
):

    youtube = get_youtube_service()

    # -----------------------------------------------------
    # Get authenticated channel
    # -----------------------------------------------------

    channel_response = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    if not channel_response.get(
        "items"
    ):

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

    # -----------------------------------------------------
    # Get uploaded videos
    # -----------------------------------------------------

    playlist_response = (
        youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(
                max_results,
                50
            )
        ).execute()
    )

    video_ids = []

    basic_videos = []

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

        basic_videos.append(
            {
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

                "channel_id": snippet.get(
                    "channelId"
                ),

                "channel_title": snippet.get(
                    "channelTitle"
                ),

                "thumbnail": (
                    snippet
                    .get("thumbnails", {})
                    .get("high", {})
                    .get("url")
                ),

                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                )
            }
        )

    if not video_ids:

        return {
            "status": "success",
            "count": 0,
            "videos": []
        }

    # -----------------------------------------------------
    # Get video statistics
    # -----------------------------------------------------

    video_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()

    stats_by_id = {}

    for video in video_response.get(
        "items",
        []
    ):

        video_id = video["id"]

        stats_by_id[
            video_id
        ] = {

            "views": int(
                video.get(
                    "statistics",
                    {}
                ).get(
                    "viewCount",
                    0
                )
            ),

            "likes": int(
                video.get(
                    "statistics",
                    {}
                ).get(
                    "likeCount",
                    0
                )
            ),

            "comments": int(
                video.get(
                    "statistics",
                    {}
                ).get(
                    "commentCount",
                    0
                )
            ),

            "duration": (
                video.get(
                    "contentDetails",
                    {}
                ).get(
                    "duration"
                )
            ),

            "definition": (
                video.get(
                    "contentDetails",
                    {}
                ).get(
                    "definition"
                )
            ),

            "caption": (
                video.get(
                    "contentDetails",
                    {}
                ).get(
                    "caption"
                )
            )
        }

    # -----------------------------------------------------
    # Combine information
    # -----------------------------------------------------

    videos = []

    for video in basic_videos:

        video_id = video[
            "video_id"
        ]

        video_stats = stats_by_id.get(
            video_id,
            {}
        )

        video.update(
            video_stats
        )

        videos.append(
            video
        )

    return {
        "status": "success",
        "count": len(videos),
        "videos": videos
    }


# =========================================================
# SEARCH YOUTUBE
# =========================================================

def search_youtube(
    query,
    max_results=10
):

    youtube = get_youtube_service()

    response = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=min(
            max_results,
            50
        )
    ).execute()

    results = []

    for item in response.get(
        "items",
        []
    ):

        video_id = (
            item["id"]
            ["videoId"]
        )

        snippet = item[
            "snippet"
        ]

        results.append(
            {
                "video_id": video_id,

                "title": snippet.get(
                    "title",
                    ""
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

                "thumbnail": (
                    snippet
                    .get("thumbnails", {})
                    .get("high", {})
                    .get("url")
                ),

                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                )
            }
        )

    return {
        "status": "success",
        "query": query,
        "count": len(results),
        "results": results
    }


# =========================================================
# GET VIDEO STATISTICS
# =========================================================

def get_video_stats(
    video_id
):

    youtube = get_youtube_service()

    response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()

    if not response.get(
        "items"
    ):

        return {
            "status": "error",
            "message": "Video not found."
        }

    video = response[
        "items"
    ][0]

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

        "video_id": video[
            "id"
        ],

        "title": snippet.get(
            "title",
            ""
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

        "definition": content_details.get(
            "definition"
        ),

        "caption": content_details.get(
            "caption"
        ),

        "thumbnail": (
            snippet
            .get("thumbnails", {})
            .get("high", {})
            .get("url")
        ),

        "url": (
            f"https://www.youtube.com/watch?v={video_id}"
        )
    }
