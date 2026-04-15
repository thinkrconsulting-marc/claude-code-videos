#!/usr/bin/env python3
"""
Search YouTube for videos matching a query.

Usage: python tools/search_youtube_videos.py [--query "search term"] [--days 30] [--max-results 25]

Requirements:
- Set YOUTUBE_API_KEY in .env file
- Install: pip install -r requirements.txt
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def search_youtube(query, days, max_results):
    """
    Search YouTube for videos matching the query (including Dutch translations).

    Args:
        query: Search term (e.g., "Claude Code")
        days: Number of days back to search (e.g., 30)
        max_results: Maximum number of results to return

    Returns:
        List of video dictionaries with metadata
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("Missing YOUTUBE_API_KEY in .env")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        # Calculate published after date
        published_after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace('+00:00', 'Z')

        # Search with both English and Dutch queries
        queries = [query, f"{query} Nederlands"]
        all_results = []

        for search_query in queries:
            logger.info(f"Searching YouTube for: '{search_query}' (from last {days} days)")

            # First API call: search for videos
            search_request = youtube.search().list(
                q=search_query,
                type="video",
                part="snippet",
                publishedAfter=published_after,
                maxResults=min(max_results, 50),  # API limit is 50 per call
                order="relevance"
            )
            search_response = search_request.execute()

            if not search_response.get("items"):
                logger.warning(f"No videos found for: '{search_query}'")
                continue

            # Extract video IDs
            video_ids = [item["id"]["videoId"] for item in search_response["items"]]
            logger.info(f"Found {len(video_ids)} videos for '{search_query}'")

            # Second API call: get video statistics (views, likes, duration)
            videos_request = youtube.videos().list(
                id=",".join(video_ids),
                part="statistics,contentDetails,snippet"
            )
            videos_response = videos_request.execute()

            # Build results with full metadata
            for video in videos_response["items"]:
                video_id = video["id"]
                snippet = video["snippet"]
                stats = video["statistics"]
                content = video["contentDetails"]

                result = {
                    "videoId": video_id,
                    "title": snippet["title"],
                    "channel": snippet["channelTitle"],
                    "description": snippet["description"][:200] + "..." if len(snippet["description"]) > 200 else snippet["description"],
                    "publishedAt": snippet["publishedAt"],
                    "viewCount": int(stats.get("viewCount", 0)),
                    "likeCount": int(stats.get("likeCount", 0)),
                    "commentCount": int(stats.get("commentCount", 0)),
                    "duration": content.get("duration", "N/A"),
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                }
                all_results.append(result)

        # Remove duplicates (same videoId)
        seen_ids = set()
        unique_results = []
        for video in all_results:
            if video["videoId"] not in seen_ids:
                seen_ids.add(video["videoId"])
                unique_results.append(video)

        # Sort by view count (descending)
        unique_results.sort(key=lambda x: x["viewCount"], reverse=True)

        # Return top N results
        return unique_results[:max_results]

    except Exception as e:
        logger.error(f"YouTube API error: {e}")
        return []


def print_results(results):
    """Print search results in a readable format."""
    if not results:
        print("\nGeen video's gevonden.")
        return

    print(f"\n{'='*100}")
    print(f"Gevonden {len(results)} video(s) • Gesorteerd op views (meeste bovenaan)")
    print(f"{'='*100}\n")

    for i, video in enumerate(results, 1):
        published = datetime.fromisoformat(video["publishedAt"].replace("Z", "+00:00")).strftime("%d-%m-%Y")
        print(f"{i}. {video['title']}")
        print(f"   Kanaal: {video['channel']}")
        print(f"   Views: {video['viewCount']:,} • Likes: {video['likeCount']:,}")
        print(f"   Gepubliceerd: {published}")
        print(f"   URL: {video['url']}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Search YouTube for videos"
    )
    parser.add_argument("--query", default="Claude Code", help="Search query (default: 'Claude Code')")
    parser.add_argument("--days", type=int, default=30, help="Number of days back to search (default: 30)")
    parser.add_argument("--max-results", type=int, default=25, help="Max results to return (default: 25)")

    args = parser.parse_args()

    logger.info("Starting YouTube search tool")

    # Search
    results = search_youtube(args.query, args.days, args.max_results)

    # Save to .tmp
    output_dir = Path(".tmp")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "youtube_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to {output_file}")

    # Print to console
    print_results(results)

    logger.info("Tool completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
