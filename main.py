import sys
import threading
import time
from PyQt5 import QtWidgets, QtCore
from SpotifyPlayer import SpotifyPlayer
from YoutubeSearcher import YoutubeSearcher
from VideoPlayer import MusicVideoPlayer

class MyListener:
    def __init__(self, youtube_searcher: YoutubeSearcher, video_player: MusicVideoPlayer):
        self.youtube_searcher = youtube_searcher
        self.video_player = video_player

    def notify(self, event_type: str, currently_playing: dict):
        if event_type == 'track_update' and currently_playing:
            self.handle_new_track(currently_playing)
        elif event_type in ['play', 'pause']:
            getattr(self.video_player, event_type)()
        elif event_type == 'track_scrub' and currently_playing:
            self.handle_track_scrub(currently_playing)
        else:
            print(f"Received Spotify event: {event_type}")

    def handle_track_scrub(self, track_update: dict):
        if track_update:
            print(f"Scrubbing to {track_update['progress_ms']} ms")
            current_time = time.time()
            seek_time = track_update['progress_ms'] / 1000
            seek_to_time = max(0, current_time - track_update['time_of_update'] + seek_time)
            self.video_player.seek(int(seek_to_time * 1000))

    def handle_new_track(self, track: dict):
        print(f"Searching YouTube for: {track['track']} by {track['artists']}")
        search_result = self.youtube_searcher.search(track, rank=True)
        if search_result:
            video_stream, audio_stream, combined_stream = self.youtube_searcher.get_video_streams(search_result['url'])
            if combined_stream:
                print(f"got combined stream")
                media_name = f"{track['artists'][0]} - {track['track']}"
                self.video_player.play_media(combined_stream, media_name)
            if video_stream and audio_stream and not combined_stream:
                self.video_player.play_streams((video_stream, audio_stream))
            else:
                print("Error: No streams?!.")
        else:
            print("Error: Could not find a suitable YouTube video.")

def run_spotify_listener(listener: MyListener):
    sp = SpotifyPlayer()
    sp.add_listener(listener)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting Spotify listener...")
    finally:
        sp.remove_listener(listener)

def main():
    app = QtWidgets.QApplication(sys.argv)
    video_player = MusicVideoPlayer()
    video_player.show()
    video_player.resize(640, 480)
    youtube_searcher = YoutubeSearcher()
    listener = MyListener(youtube_searcher, video_player)

    try:
        threading.Thread(target=run_spotify_listener, args=(listener,), daemon=True).start()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        del youtube_searcher
        del video_player
        app.quit()

if __name__ == "__main__":
    main()