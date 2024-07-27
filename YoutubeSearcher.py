import yt_dlp
from yt_dlp.utils import DownloadError

class YoutubeSearcher:
    YDL_OPTS = {
        'quiet': True, 'skip_download': True, 'no_warnings': True,
        'noplaylist': True, 'nocheckcertificate': True, 'geo_bypass': True,
        'default_search': 'ytsearchviewcount', 'prefer_insecure': True,
        'extract_flat': True,
    }

    def __init__(self):
        self.ydl = yt_dlp.YoutubeDL(self.YDL_OPTS)

    def _rank_video(self, result: dict, track: dict) -> int:
        track_words = [artist.lower() for artist in track.get('artists', [])] + [
            track['track'].lower(), track['album'].lower()
        ]
        title, uploader, channel = (result.get(key, "").lower() for key in ['title', 'uploader', 'channel'])
        
        title_match = sum(word in title for word in track_words)
        uploader_match = sum(word in uploader for word in track_words)
        channel_match = sum(word in channel for word in track_words)
        duration_match = abs(result.get('duration', 0) - track['duration_ms'] / 1000) <= 120

        return 3 * title_match + 2 * uploader_match + channel_match + 2 * duration_match

    def rank_videos(self, search_results: dict, track: dict) -> dict:
        if 'entries' not in search_results:
            raise ValueError("Invalid search_results format: missing 'entries' key.")
        
        for result in search_results['entries']:
            result['rank'] = self._rank_video(result, track)
        search_results['entries'].sort(key=lambda x: x['rank'], reverse=True)
        return search_results

    def search(self, track: dict, rank: bool = True, search_count: int = 20) -> dict or None:
        if not isinstance(track, dict):
            raise ValueError("Invalid track")

        query = f"ytsearch{search_count}:{track['artists'][0]} {track['track']} official music video"

        try:
            results = self.ydl.extract_info(query, download=False)
            valid_entries = [r for r in results.get('entries', []) if r.get('title') and r.get('uploader')]
            
            if not valid_entries:
                print("No suitable videos found.")
                return None

            if rank:
                ranked_results = self.rank_videos({'entries': valid_entries}, track)
                return ranked_results['entries'][0] if ranked_results['entries'] else None
            else:
                return valid_entries[0]
        except DownloadError as e:
            print(f"Error during YouTube search: {e}")
            return None

    @staticmethod
    def get_video_streams(youtube_url: str, desired_resolution: int = 720) -> tuple[str, str, str] or None:
        """Get the direct stream URLs for video, audio, and combined stream of a given YouTube video URL."""
        def get_best_streams(info):
            video_streams = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') == 'none']
            audio_streams = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            combined_streams = [f for f in info['formats'] if f.get('format_id') == '18']
            
            best_video = max(
                (f for f in video_streams if f.get('height', 0) <= desired_resolution),
                key=lambda f: (f.get('height', 0), f.get('vbr', 0)),
                default=None
            )
            
            best_audio = max(audio_streams, key=lambda f: (f.get('abr') or 0), default=None)
            
            combined_stream = combined_streams[0] if combined_streams else None
            
            return best_video, best_audio, combined_stream

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'no_warnings': True,
            'quiet': True,
            'no_check_certificate': True,
            'prefer_insecure': True,
            'nocheckcertificate': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                if info and 'formats' in info:
                    video_stream, audio_stream, combined_stream = get_best_streams(info)
                    return (
                        video_stream['url'] if video_stream else None,
                        audio_stream['url'] if audio_stream else None,
                        combined_stream['url'] if combined_stream else None
                    )
                print("No suitable video and audio formats found.")
                return None, None, None
        except DownloadError as e:
            print(f"Error extracting video URL: {e}")
            return None, None, None
        except Exception as e:
            print(f"Unexpected error in get_video_streams: {e}")
            return None, None, None