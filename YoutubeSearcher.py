import yt_dlp
import json
from yt_dlp.utils import DownloadError

class YoutubeSearcher:
    """A class for searching and ranking YouTube videos based on relevance to a specific track"""
    YDL_OPTS = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'default_search': 'ytsearchviewcount',
        'prefer_insecure': True,
        'extract_flat': True
    }

    def __init__(self):
        self.ydl = yt_dlp.YoutubeDL(self.YDL_OPTS)

    @staticmethod
    def _rank_video(result: dict, track: dict) -> int:
        """
        Calculate a rank for a YouTube video based on its relevance to the given track.
    
        Args:
            result (dict): YouTube video metadata.
            track (dict): Track information.
    
        Returns:
            int: The calculated rank for the video.
        """
        track_words = [
            artist.lower() for artist in track.get('artists', [])] + [
            track['track'].lower(),
            track['album'].lower()
        ]
    
        title = result.get('title', "").lower()
        uploader = result.get('uploader', "").lower()
        channel = result.get('channel', "").lower()

        title_match = sum(1 for word in track_words if word in title)
        uploader_match = sum(1 for word in track_words if word in uploader)
        channel_match = sum(1 for word in track_words if word in channel)
        view_count = min(result.get('view_count', 0) / 1_000_000, 5)
        duration_match = abs(result.get('duration', 0) - track['duration_ms'] / 1000) <= 120
    
        rank = (
            3 * title_match +
            2 * uploader_match +
            1 * channel_match +
            2 * (1 if duration_match else 0)
        )
        return rank

    def rank_videos(self, search_results: dict, track: dict) -> dict:
        """
        Rank all videos in the search results by their relevance to the given track.

        Args:
            search_results (dict): Dictionary containing video results under 'entries'.
            track (dict): Dictionary containing track information.

        Returns:
            dict: The modified search_results dictionary with ranked entries.
        """
        if 'entries' not in search_results:
            raise ValueError("Invalid search_results format: missing 'entries' key.")
        
        for result in search_results['entries']:
            result['rank'] = self._rank_video(result, track)
        search_results['entries'].sort(key=lambda x: x['rank'], reverse=True)
        return search_results

    def search(self, track: dict, rank: bool = True, search_count: int = 20) -> dict or None:
        """
        Search for YouTube videos related to the given track and optionally rank the results

        Args:
            track (dict): Dictionary containing track information.
            rank (bool, optional): Whether to rank the results. Defaults to True.
            search_count (int, optional): Number of search results to retrieve. Defaults to 20.

        Returns:
            dict or None: Top-ranked video or complete search results, or None if no suitable videos are found.
        """
        if not isinstance(track, dict):
            raise ValueError("Invalid track")

        query = f"{track['artists'][0]} {track['track']} official music video"

        try:
            results = self.ydl.extract_info(f"ytsearch{search_count}:{query}", download=False)
        except DownloadError as e:
            print(f"Error during YouTube search: {e}")
            return None

        results['entries'] = [result for result in results['entries'] if result.get('title') and result.get('uploader')]

        if not results['entries']:
            print("No suitable videos found.")
            return None

        if rank:
            ranked_results = self.rank_videos(results, track)
            return ranked_results['entries'][0] if ranked_results['entries'] else None
        else:
            return results['entries'][0] if results['entries'] else None

    @staticmethod
    def get_video_stream_url(youtube_url: str) -> str or None:
        """Get the direct stream URL for a given YouTube video URL."""
        ydl_opts = {**YoutubeSearcher.YDL_OPTS, 'format': 'best'}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info.get('url')
        except DownloadError as e:
            print(f"Error extracting video URL: {e}")
            return None
