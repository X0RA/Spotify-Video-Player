import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
import time
from SettingsPanel import get_settings

class SpotifyPlayer:
    """ Manages interaction with the Spotify API, tracks currently playing songs,and notifies listeners about changes in playback state."""
    def __init__(self):
        settings = get_settings()
        cid = settings.get('CLIENT_ID', '')
        csecret = settings.get('CLIENT_SECRET', '')
        self.refresh_timeout = float(settings.get('REFRESH_TIMEOUT', 1))
        scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state user-library-read user-library-modify"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cid, client_secret=csecret, redirect_uri="http://localhost:8990/callback", scope=scope))
        self.currentlyPlaying = None
        self.is_playing = None
        self.listeners = []
        self.last_audio_volume = None
        self.start_track_updater()

    def add_listener(self, listener):
        self.listeners.append(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def toggle_mute(self):
        """Toggles mute/unmute on the currently active Spotify device."""
        try:
            current_playback = self.sp.current_playback()
            
            if not current_playback or not current_playback.get('device'):
                return
            
            current_device = current_playback['device']
            current_volume = current_device['volume_percent']
            
            if current_volume == 0 and (self.last_audio_volume is None or self.last_audio_volume == 0):
                # User may have set volume to 0, unmute to a default or last known volume
                new_volume = 50 if self.last_audio_volume is None else self.last_audio_volume
                self.sp.volume(new_volume)
                self.notify_listeners('unmute')
            elif current_volume == 0 and self.last_audio_volume != 0:
                # If currently muted, unmute to the last known volume
                self.sp.volume(self.last_audio_volume)
                self.notify_listeners('unmute')
            else:
                # If not muted, mute the audio and save the current volume
                self.last_audio_volume = current_volume
                self.sp.volume(0)
                self.notify_listeners('mute')

        except Exception as e:
            print(f"Error occurred while trying to toggle mute: {str(e)}")

    def next_song(self):
        """Skips to the next song in the user's Spotify queue."""
        try:
            self.sp.next_track()
            self.notify_listeners('skip')
        except Exception as e:
            print(f"Error occurred while trying to skip to the next song: {str(e)}")

    def previous_song(self):
        """Skips to the previous song in the user's Spotify queue."""
        try:
            self.sp.previous_track()
            self.notify_listeners('previous')
        except Exception as e:
            print(f"Error occurred while trying to skip to the previous song: {str(e)}")

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

    def did_scrub(self, track_update):
        """Determines if the user has scrubbed through the track."""
        current_time = time.time()
        
        # Extract old and new update times and progress
        old_update_time = self.currentlyPlaying['time_of_update']
        old_seek_time = self.currentlyPlaying['progress_ms'] / 1000  
        new_update_time = track_update['time_of_update']
        new_seek_time = track_update['progress_ms'] / 1000 
        
        # Calculate the expected new seek time based on old seek time and elapsed time
        time_elapsed = new_update_time - old_update_time
        expected_seek_time = old_seek_time + time_elapsed
        
        # Determine the actual difference in seek time
        time_difference = new_seek_time - expected_seek_time
        
        # Threshold for determining a skip (this can be adjusted as needed)
        skip_threshold = 5  # seconds
        
        # Check if the difference exceeds the threshold, indicating a skip
        if time_difference > skip_threshold or time_difference < -skip_threshold:
            return True
        else:
            return False

    def update_currently_playing(self):
        """Continuously monitors the currently playing track and notifies listeners of changes."""
        while True:
            current_track = self.get_current_track()
            if current_track:
                if self.currentlyPlaying and current_track['track_id'] == self.currentlyPlaying['track_id'] and self.did_scrub(current_track):
                    self.currentlyPlaying['progress_ms'] = current_track['progress_ms']
                    self.currentlyPlaying['time_of_update'] = current_track['time_of_update']
                    self.notify_listeners('track_scrub')
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
