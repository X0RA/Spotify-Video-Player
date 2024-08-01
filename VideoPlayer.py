import sys
import os
import vlc
from PyQt5 import QtWidgets, QtGui, QtCore
import time
from SpotifyPlayer import SpotifyPlayer
from SettingsPanel import show_settings_panel, get_settings


class MusicVideoPlayer(QtWidgets.QMainWindow):
    """A music video player using VLC and PyQt5 with support for separate video and audio streams."""
    media_loaded = QtCore.pyqtSignal(str)
    seek_complete = QtCore.pyqtSignal()

    def __init__(self, spotify_player=None, master=None):
        super().__init__(master)
        self.spotify_player = spotify_player
        self._load_settings()
        self._initialize_players()
        self._create_ui()
        self._setup_signals()
        self._apply_initial_settings()
        self.is_seeking = False

    def _load_settings(self):
        settings = get_settings()
        self.start_muted = settings.get('START_MUTED', True)
        self.start_fullscreen = settings.get('START_FULLSCREEN', False)
        

    def _initialize_players(self):
        self.instance = vlc.Instance('--no-xlib')
        self.video_player = self.instance.media_player_new()
        self.audio_player = self.instance.media_player_new()
        self.isPaused = False
        self.video_media = None
        self.audio_media = None
        self.media_name = None
        self.paused_before_seek = False
        self.seek_timer = QtCore.QTimer()
        self.seek_timer.timeout.connect(self._check_seek_complete)
        self.seek_start_time = None

    def _create_ui(self):
        self.setWindowTitle("Music Video Player")
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        self.videoframe = self._create_video_frame()
        
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.videoframe)
        central_widget.setLayout(layout)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_ui)

    def _create_video_frame(self):
        videoframe = QtWidgets.QFrame()
        palette = videoframe.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        videoframe.setPalette(palette)
        videoframe.setAutoFillBackground(True)
        videoframe.installEventFilter(self)
        return videoframe

    def _setup_signals(self):
        self.media_loaded.connect(self._on_media_loaded)
        self.seek_complete.connect(self._on_seek_complete)
        self.shortcut_fullscreen = QtWidgets.QShortcut(QtGui.QKeySequence("F"), self)
        self.shortcut_fullscreen.activated.connect(self.toggle_fullscreen)
        self.shortcut_mute = QtWidgets.QShortcut(QtGui.QKeySequence("M"), self)
        self.shortcut_mute.activated.connect(self.toggle_mute)
        self.shortcut_play_pause = QtWidgets.QShortcut(QtGui.QKeySequence("SPACE"), self)
        self.shortcut_play_pause.activated.connect(self.toggle_play_pause)
        self.shortcut_toggle_spotify_mute = QtWidgets.QShortcut(QtGui.QKeySequence("S"), self)
        self.shortcut_toggle_spotify_mute.activated.connect(self.toggle_spotify_mute)
        self.shortcut_toggle_spotify_mute = QtWidgets.QShortcut(QtGui.QKeySequence("N"), self)
        self.shortcut_toggle_spotify_mute.activated.connect(self.spotify_player.next_song)
        self.shortcut_toggle_spotify_mute = QtWidgets.QShortcut(QtGui.QKeySequence("P"), self)
        self.shortcut_toggle_spotify_mute.activated.connect(self.spotify_player.previous_song)
        self.shortcut_settings = QtWidgets.QShortcut(QtGui.QKeySequence("H"), self)
        self.shortcut_settings.activated.connect(self.show_settings)
        
    def show_settings(self):
        if show_settings_panel(self):
            self._load_settings()
        
    def _apply_initial_settings(self):
        if self.start_muted:
            self.toggle_mute()
        self.show()
        if self.start_fullscreen:
            QtCore.QTimer.singleShot(100, self.toggle_fullscreen)

    def eventFilter(self, source, event):
        return super().eventFilter(source, event)

    def _get_black_palette(self):
        palette = self.videoframe.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        return palette

    def toggle_spotify_mute(self):
        if hasattr(self, 'spotify_player'):
            self.spotify_player.toggle_mute()
        else:
            print("Spotify player not initialized")

    def toggle_play_pause(self):
        if not self.isPaused:
            self.pause()
        else:
            self.play()

    def play(self):
        self.video_player.play()
        if self.audio_media:
            self.audio_player.play()
        self.isPaused = False
        self.synchronize_players()
        self.update_ui()

    def pause(self):
        self.video_player.pause()
        if self.audio_media:
            self.audio_player.pause()
        self.isPaused = True
        # self.synchronize_players()
        self.update_ui()
        
    def synchronize_players(self):
        if self.audio_media:
            video_time = self.video_player.get_time()
            audio_time = self.audio_player.get_time()
            if abs(video_time - audio_time) > 50: 
                self.audio_player.set_time(video_time)
        
    def toggle_mute(self):
        self.audio_player.audio_toggle_mute()

    def get_buffered_amount(self):
        video_buffered = 0
        audio_buffered = 0
        
        if self.video_player:
            video_stats = self.video_player.get_stats()
            video_demux_read_bytes = video_stats.get('demux_read_bytes', 0)
            video_input_bitrate = video_stats.get('input_bitrate', 0)
            
            if video_input_bitrate > 0:
                video_buffered = (video_demux_read_bytes * 8) / (video_input_bitrate * 1000) * 1000

        if self.audio_media and self.audio_player:
            audio_stats = self.audio_player.get_stats()
            audio_demux_read_bytes = audio_stats.get('demux_read_bytes', 0)
            audio_input_bitrate = audio_stats.get('input_bitrate', 0)
            
            if audio_input_bitrate > 0:
                audio_buffered = (audio_demux_read_bytes * 8) / (audio_input_bitrate * 1000) * 1000

        return (video_buffered, audio_buffered if self.audio_media else None)

    def seek(self, time_ms):
        if self.video_media:
            self.is_seeking = True
            self.paused_before_seek = self.isPaused
            self.target_seek_time = time_ms
            self.video_player.set_time(time_ms)
            if self.audio_media:
                self.audio_player.set_time(time_ms)
            
            self.seek_start_time = time.time()
            QtCore.QTimer.singleShot(200, self._check_seek_complete)
        else:
            print("Error: No media loaded.")

    def _check_seek_complete(self):
        current_video_time = self.video_player.get_time()
        video_buffered, audio_buffered = self.get_buffered_amount()
        
        video_seek_complete = abs(current_video_time - self.target_seek_time) < 500 and video_buffered > 2000
        audio_seek_complete = True  # Default to True if there's no audio

        if self.audio_media:
            current_audio_time = self.audio_player.get_time()
            audio_seek_complete = abs(current_audio_time - self.target_seek_time) < 500 and audio_buffered > 2000

        if video_seek_complete and audio_seek_complete:
            if self.video_player.get_state() in [vlc.State.Playing, vlc.State.Paused]:
                self.seek_complete.emit()
                return

        if time.time() - self.seek_start_time > 10:  # 10 second timeout
            print("Seek timeout")
            self.seek_complete.emit()
        else:
            QtCore.QTimer.singleShot(100, self._check_seek_complete)

    @QtCore.pyqtSlot()
    def _on_seek_complete(self):
        self.is_seeking = False
        if not self.paused_before_seek:
            self.play()
        else:
            self.pause()
        self.paused_before_seek = None
        self.synchronize_players()
        self.update_ui()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def play_streams(self, streams: tuple):
        video_stream, audio_stream = streams

        if not video_stream or not audio_stream:
            print("Both video and audio streams must be provided.")
            return

        self.video_media = self.instance.media_new(video_stream)
        self.audio_media = self.instance.media_new(audio_stream)

        self.video_media.add_option('avcodec-hw=d3d11va')
        self.audio_media.add_option('avcodec-hw=d3d11va')

        self.video_player.set_media(self.video_media)
        self.audio_player.set_media(self.audio_media)

        try:
            self.video_player.play()
            self.audio_player.play()
            self.media_loaded.emit(video_stream)
        except Exception as e:
            print(f"Error playing streams: {e}")

    @QtCore.pyqtSlot(str)
    def _on_media_loaded(self, media_path):
        try:
            self._set_platform_specific_window()
            self.video_player.play()
            if self.audio_media:
                self.audio_player.play()
            self.timer.start()
        except Exception as e:
            print(f"Error in _on_media_loaded: {e}")

    def play_media(self, media_path: str, song_name: str = None):
        if not media_path:
            return

        self.media_name = song_name
        self.setWindowTitle(f"Music Video Player - {song_name}" if song_name else "Music Video Player")

        try:
            media = self.instance.media_new(media_path)
            self.video_player.set_media(media)
            self.video_media = media
            self.audio_media = None  # Reset audio_media for combined streams
            self.video_media.parse()
            self.media_loaded.emit(media_path)
        except Exception as e:
            print(f"Error playing media: {e}")

    def _set_platform_specific_window(self):
        if sys.platform.startswith('linux'):
            self.video_player.set_xwindow(int(self.videoframe.winId()))
        elif sys.platform == "win32":
            self.video_player.set_hwnd(int(self.videoframe.winId()))
        elif sys.platform == "darwin":
            self.video_player.set_nsobject(int(self.videoframe.winId()))
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

    def update_ui(self):
        if not QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread():
            return
        base_title = f"{self.media_name}" if self.media_name else "Music Video Player"
        status = "Paused" if self.isPaused else "Seeking" if self.is_seeking else "Playing"
        self.setWindowTitle(f"{base_title} ({status})")
        
        video_state = self.video_player.get_state()
        if video_state == vlc.State.Ended:
            self.isPaused = True
        elif video_state in [vlc.State.Playing, vlc.State.Paused]:
            self.isPaused = (video_state == vlc.State.Paused)
        
        if video_state == vlc.State.Error:
            print("Video playback error detected. Attempting to reset...")
            self.video_player.stop()
            self.video_player.play()
        
        if self.audio_media and self.audio_player.get_state() == vlc.State.Error:
            print("Audio playback error detected. Attempting to reset...")
            self.audio_player.stop()
            self.audio_player.play()
