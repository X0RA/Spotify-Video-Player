from typing import List, Dict, Any

import yt_dlp
from yt_dlp.utils import DownloadError
from janome.tokenizer import Tokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class YoutubeSearcher:
    YDL_OPTS = {
        'quiet': True, 'skip_download': True, 'no_warnings': True,
        'noplaylist': True, 'nocheckcertificate': True, 'geo_bypass': True,
        'default_search': 'ytsearchviewcount', 'prefer_insecure': True,
        'extract_flat': True,
    }

    def __init__(self):
        self.ydl = yt_dlp.YoutubeDL(self.YDL_OPTS)

    def tokenize_japanese(self, text):
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(text)
        return " ".join([token.surface for token in tokens])

    def text_similarity(self, data: dict, track: dict) -> str:
        lang = ""
        is_japanese = any(
            '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in
            data['title'])

        if is_japanese:
            lang = "Japanese"
            title1 = self.tokenize_japanese(data['title'])
            title2 = self.tokenize_japanese(track['track'])
            channel1 = self.tokenize_japanese(data['channel'])
            channel2 = self.tokenize_japanese(track['artists'][0])
        else:
            title1 = data['title'].lower()
            title2 = track['track'].lower()
            channel1 = data['channel'].lower()
            channel2 = track['artists'][0].lower()

        vectorizer = TfidfVectorizer()

        # Compute TF-IDF vectors
        vectors_title = vectorizer.fit_transform([title1, title2]).toarray()
        vectors_channel = vectorizer.fit_transform([channel1, channel2]).toarray()
        vectors_combo = vectorizer.fit_transform([f"{title1} - {channel1}", f"{title2} - {channel2}"]).toarray()

        # Compute cosine similarities
        sim_title = round(cosine_similarity(vectors_title)[0][1] * 50)
        sim_channel = round(cosine_similarity(vectors_channel)[0][1] * 50)
        sim_individual = sim_title + sim_channel
        sim_combo = round(cosine_similarity(vectors_combo)[0][1] * 100)

        if lang == "Japanese":
            return max(sim_individual, sim_combo) * 1.8
        else:
            return max(sim_individual, sim_combo) * 1.2

    def rank_videos(self, results: Dict[str, Any], track: Dict[str, Any]) -> List[Dict[str, Any]]:
        for result in results['entries']:
            result['rank'] = self.text_similarity(result, track)

        results = [result for result in results['entries'] if result['rank'] >= 50]

        # Adjust ranks based on view count
        results.sort(key=lambda x: x['view_count'], reverse=True)
        for i, item in enumerate(results[:3]):
            item['rank'] += [10, 6, 3][i]

        # Adjust ranks based on duration similarity
        results = [item for item in results if abs(item['duration'] - track['duration_ms'] / 1000) <= 40]
        results.sort(key=lambda x: abs(x['duration'] - track['duration_ms'] / 1000))
        for i, item in enumerate(results[:3]):
            item['rank'] -= [6, 4, 2][i]

        # Adjust ranks based on good words in the title
        good_words = {"official": 12, "music video": 18, "mv": 15, "lyric": 8, 'live': -10, "Official HD Video": 12,
                      "Official Music Video": 12, "Animated": 10}
        for item in results:
            for word, score in good_words.items():
                if word.lower() in item['title'].lower():
                    item['rank'] += score

        # Filter out results with bad words in the title
        bad_words = ["歌ってみた", 'sped up', "fan-made", "acoustic ver", "remix", "cover", "live", "instrumental",
                     "vocal only", "Instrument", "slowed", "reverb"]
        results = [item for item in results if not any(
            bad_word.lower() in item['title'].replace(track['track'], '').lower() for bad_word in bad_words)]

        # Adjust rank if the channel matches the artist
        for item in results:
            if track['artists'][0].lower() in item['channel'].lower():
                item['rank'] += 20

        # Adjust ranks if the channel is verified
        for item in results:
            if item.get('channel_is_verified', True):
                item['rank'] += 30

                # New score modifier: increase score if the searched title is in the video title
                for item in results:
                    if track['track'].lower() in item['title'].lower():
                        item['rank'] += 20  # Adjust this score as needed

        results.sort(key=lambda x: x['rank'], reverse=True)

        for item in results:
            print(f"Title: {item['title']}, Rank: {item['rank']}")

        return results

    def search(self, track: dict, rank: bool = True, search_count: int = 20) -> dict or None:
        if not isinstance(track, dict):
            raise ValueError("Invalid track")

        query = f"ytsearch{search_count}:{track['artists'][0]} {track['track']} official music video"

        try:
            results = self.ydl.extract_info(query, download=False)
            valid_entries = [r for r in results.get('entries', []) if r.get('title') and r.get('uploader')]
            # strip all the entries that have a url that starts with https://www.youtube.com/shorts/
            valid_entries = [r for r in valid_entries if not r.get('url', '').startswith('https://www.youtube.com/shorts/')]

            if not valid_entries:
                print("No suitable videos found.")
                return None

            if rank:
                ranked_results = self.rank_videos({'entries': valid_entries}, track)
                return ranked_results[0] if ranked_results else None
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
