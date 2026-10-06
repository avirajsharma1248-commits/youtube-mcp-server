# =========================================================
# ADDITIONAL MCP TOOLS
# =========================================================

@mcp.tool()
def get_channel_analytics(
    start_date: str,
    end_date: str
) -> dict:
    """
    Get YouTube channel analytics for a date range.
    Date format: YYYY-MM-DD
    """

    from youtube_service import get_channel_analytics as fn

    return fn(
        start_date=start_date,
        end_date=end_date
    )


@mcp.tool()
def get_video_details(
    video_id: str
) -> dict:
    """
    Get complete details about a YouTube video.
    """

    from youtube_service import get_video_details as fn

    return fn(
        video_id=video_id
    )


@mcp.tool()
def youtube_keyword_research(
    query: str,
    max_results: int = 20
) -> dict:
    """
    Research YouTube search results for a keyword.
    """

    from youtube_service import youtube_keyword_research as fn

    return fn(
        query=query,
        max_results=max_results
    )


@mcp.tool()
def get_trending_videos(
    region_code: str = "IN",
    category_id: str = None,
    max_results: int = 10
) -> dict:
    """
    Get popular/trending YouTube videos for a region.
    """

    from youtube_service import get_trending_videos as fn

    return fn(
        region_code=region_code,
        category_id=category_id,
        max_results=max_results
    )


@mcp.tool()
def analyze_video_comments(
    video_id: str,
    max_results: int = 100
) -> dict:
    """
    Retrieve and analyze comments from a YouTube video.
    """

    from youtube_service import analyze_video_comments as fn

    return fn(
        video_id=video_id,
        max_results=max_results
    )


@mcp.tool()
def compare_videos(
    video_ids: str
) -> dict:
    """
    Compare multiple YouTube videos.

    Example:
    video_ids = "abc123,xyz456,test789"
    """

    from youtube_service import compare_videos as fn

    return fn(
        video_ids=video_ids
    )
