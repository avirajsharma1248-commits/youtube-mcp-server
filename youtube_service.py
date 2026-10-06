def get_video_stats(video_id):
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
                "video_id": video_id
            }

        video = response["items"][0]

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})

        return {
            "status": "success",
            "video_id": video["id"],
            "title": snippet.get("title"),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "views": int(statistics.get("viewCount", 0)),
            "likes": int(statistics.get("likeCount", 0)),
            "comments": int(statistics.get("commentCount", 0)),
            "duration": content_details.get("duration"),
            "thumbnail": (
                snippet
                .get("thumbnails", {})
                .get("high", {})
                .get("url")
            ),
            "url": (
                f"https://www.youtube.com/watch?v={video['id']}"
            )
        }

    except Exception as e:
        import traceback

        print("========== GET VIDEO STATS ERROR ==========")
        traceback.print_exc()
        print("============================================")

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "video_id": video_id
        }
