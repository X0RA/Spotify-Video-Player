import sys
import threading
import time
from PyQt5 import QtWidgets
from SpotifyPlayer import SpotifyPlayer
from YoutubeSearcher import YoutubeSearcher
from VideoPlayer import MusicVideoPlayer

class MyListener:
    """Listens to SpotifyPlayer events and triggers corresponding actions in the video player."""
    def __init__(self, youtube_searcher: YoutubeSearcher, video_player: MusicVideoPlayer):
        self.youtube_searcher = youtube_searcher
        self.video_player = video_player

    def notify(self, event_type: str, currently_playing: dict):
        """Handles SpotifyPlayer events: track update, play, or pause"""
        if event_type == 'track_update' and currently_playing:
            self.handle_new_track(currently_playing)
        if event_type == 'play':
            self.video_player.play()
        if event_type == 'pause':
            self.video_player.pause()
        else:
            print(f"Received Spotify event: {event_type}")

    def handle_new_track(self, track: dict):
        """Searches for a YouTube video for the new track and plays it"""
        print("Searching YouTube for:", track['track'], "by", track['artists'])
        search_result = self.youtube_searcher.search(track, rank=True)
        if search_result:
            direct_url = self.youtube_searcher.get_video_stream_url(search_result['url'])
            if direct_url:
                print("Playing video:", direct_url)
                self.video_player.play_media(direct_url)
            else:
                print("Error: Could not get a direct video URL.")
        else:
            print("Error: Could not find a suitable YouTube video.")


def run_spotify_listener(listener: MyListener):
    """
    Function to be run in a separate thread for continuously listening to Spotify events.
    """
    sp = SpotifyPlayer()
    sp.add_listener(listener)
    try:
        while True:
            time.sleep(1)  # Poll Spotify every second
    except KeyboardInterrupt:
        print("Exiting Spotify listener...")
    finally:
        # Clean up:
        sp.remove_listener(listener)
        del sp  # Explicitly delete the SpotifyPlayer object


def main():
    """
    Main entry point for the application. Sets up the UI, initializes objects, and starts threads.
    """
    app = QtWidgets.QApplication(sys.argv)
    video_player = MusicVideoPlayer()
    video_player.show()
    video_player.resize(640, 480)
    youtube_searcher = YoutubeSearcher()
    listener = MyListener(youtube_searcher, video_player)

    try:
        listener_thread = threading.Thread(target=run_spotify_listener, args=(listener,), daemon=True)
        listener_thread.start()
        sys.exit(app.exec_())
    except Exception as e:  
        print(f"An error occurred: {e}")
    finally:
        del youtube_searcher  
        del video_player
        app.quit() 

if __name__ == "__main__":
    main()
