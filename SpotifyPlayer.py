from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
import time

class SpotifyPlayer:
    """ Manages interaction with the Spotify API, tracks currently playing songs,and notifies listeners about changes in playback state."""
    def __init__(self):
        load_dotenv()
        cid = os.getenv('CLIENT_ID')
        csecret = os.getenv('CLIENT_SECRET')
        self.refresh_timeout = float(os.getenv('REFRESH_TIMEOUT', 1))
        scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state user-library-read user-library-modify"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cid, client_secret=csecret, redirect_uri="http://localhost:8990/callback", scope=scope))
        self.currentlyPlaying = None
        self.is_playing = None
        self.listeners = []
        self.start_track_updater()

    def add_listener(self, listener):
        self.listeners.append(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def notify_listeners(self, event_type):
        """
        Notifies all registered listeners about a playback event (track change, play, pause).
        Args:
            event_type (str): The type of event ('track_update', 'play', 'pause').
        """
        for listener in self.listeners:
            listener.notify(event_type, self.currentlyPlaying)

    def get_current_track(self) -> dict or None:
        """Retrieves the currently playing track from the Spotify API."""
        track = self.sp.current_playback()
        if track and track['item']:
            return {
                "time_of_update": time.time(),
                "timestamp": track['timestamp'],
                "progress_ms": track['progress_ms'],
                "artists": [artist['name'] for artist in track['item']['artists']],
                "track": track['item']['name'],
                "album": track['item']['album']['name'],
                "duration_ms": track['item']['duration_ms'],
                "is_playing": track['is_playing'],
                "track_id": track['item']['id']
            }
        return None

    def update_currently_playing(self):
        """Continuously monitors the currently playing track and notifies listeners of changes."""
        while True:
            current_track = self.get_current_track()
            if current_track:
                track_id = current_track['track_id']
                if not self.currentlyPlaying or track_id != self.currentlyPlaying['track_id']:
                    self.currentlyPlaying = current_track
                    self.notify_listeners('track_update')
                if current_track['is_playing'] != self.is_playing:
                    self.is_playing = current_track['is_playing']
                    self.notify_listeners('play' if self.is_playing else 'pause')
            else:
                self.is_playing = False
                self.currentlyPlaying = None
            time.sleep(self.refresh_timeout)

    def start_track_updater(self):
        """Starts the background thread to update the currently playing track."""
        thread = threading.Thread(target=self.update_currently_playing)
        thread.daemon = True
        thread.start()
