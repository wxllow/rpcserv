# Designed for Apple Music, in reality, should work with any music
import time
import aiohttp
import requests.utils

CACHED_APPLE_MUSIC_INFO = {
    "title": None,
    "artist": None,
    "album": None,
    "url": None,
    "image": None,
}


def parse_time(time: str) -> int:
    """Parse a time string into seconds."""
    # Time is either formatted as `0` (seconds) or `0:00` (minutes:seconds) and should be returned in seconds as an integer.
    if ":" in time:
        minutes, seconds = time.split(":")
        return int(minutes) * 60 + int(seconds)

    return float(time)


async def get_apple_music_info(title, artist, album, limit=5):
    def encode_uri(text):
        return requests.utils.quote(text, safe="")

    req_param = encode_uri(f"{title} {artist} {album}")

    async with aiohttp.ClientSession() as session:
        async with await session.get(
            f"https://itunes.apple.com/search?term={req_param}&entity=musicTrack&limit={encode_uri(str(limit))}",
        ) as response:
            if response.status == 200:
                # For some reason, itunes returns mimetype as javascript, but its still valid JSON
                data = await response.json(content_type=None)

            if data["resultCount"] < 1:
                return {
                    "url": None,
                    "image": None,
                }

            # Find the first result that matches the artist, album, & title exactly, otherwise, just return the first result
            result = data["results"][0]

            for res in data["results"]:
                if res["artistName"].lower() == artist.lower():
                    if res["collectionName"].lower() == album.lower():
                        if res["trackName"].lower() == title.lower():
                            result = res

            return {
                "url": result["trackViewUrl"],
                "image": result["artworkUrl100"].replace("100x100bb", "512x512bb"),
            }


async def rpcserv(data):
    global CACHED_APPLE_MUSIC_INFO

    # Check if cache has same title, artist, and album
    if (
        CACHED_APPLE_MUSIC_INFO["title"] == data["metadata"]["title"]
        and CACHED_APPLE_MUSIC_INFO["artist"] == data["metadata"]["artist"]
        and CACHED_APPLE_MUSIC_INFO["album"] == data["metadata"]["album"]
    ):
        # Use cached info
        apple_music_info = CACHED_APPLE_MUSIC_INFO
    else:
        print("New song, getting iTunes info")
        apple_music_info = await get_apple_music_info(
            data["metadata"]["title"],
            data["metadata"]["artist"],
            data["metadata"]["album"],
        )
        # Update cache
        CACHED_APPLE_MUSIC_INFO = {
            "title": data["metadata"]["title"],
            "artist": data["metadata"]["artist"],
            "album": data["metadata"]["album"],
            "url": apple_music_info["url"],
            "image": apple_music_info["image"],
        }

    return {
        "buttons": [
            {
                "label": "Listen on Apple Music",
                "url": apple_music_info["url"],
            }
        ]
        if apple_music_info["url"]
        else None,
        "large_image": apple_music_info["image"],
        "start": time.time() - parse_time(data["metadata"]["current_time"]),
    }
