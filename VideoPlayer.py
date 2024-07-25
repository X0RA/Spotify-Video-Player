import sys
import os
import vlc
from PyQt5 import QtWidgets, QtGui, QtCore
from dotenv import load_dotenv

class MusicVideoPlayer(QtWidgets.QMainWindow):
    """A music video player using VLC and PyQt5 with support for separate video and audio streams."""
    media_loaded = QtCore.pyqtSignal(str)
    seek_complete = QtCore.pyqtSignal()  # Correctly define the signal here

    def __init__(self, master=None):
        super().__init__(master)
        self._load_settings()
        self._initialize_players()
        self._create_ui()
        self._setup_signals()
        self._apply_initial_settings()
        self.is_seeking = False

    def _load_settings(self):
        load_dotenv()
        self.start_muted = os.getenv('START_MUTED', 'False').lower() in ('true', '1', 't')
        self.start_fullscreen = os.getenv('START_FULLSCREEN', 'False').lower() in ('true', '1', 't')

    def _initialize_players(self):
        self.instance = vlc.Instance('--no-xlib')
        self.video_player = self.instance.media_player_new()
        self.audio_player = self.instance.media_player_new()
        self.isPaused = False
        self.video_media = None
        self.audio_media = None
        self.media_name = None

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

    def toggle_play_pause(self):
        if self.video_player.is_playing():
            self.pause()
        else:
            self.play()

    def play(self):
        if not self.video_player.is_playing() and not self.is_seeking:
            self.video_player.play()
            self.audio_player.play()
            self.isPaused = False
            self.update_ui()

    def pause(self):
        if self.video_player.is_playing():
            self.video_player.pause()
            self.audio_player.pause()
            self.isPaused = True
            self.update_ui()

    def toggle_mute(self):
        self.audio_player.audio_toggle_mute()


    def seek(self, time_ms):
        if self.video_media and self.audio_media:
            self.is_seeking = True
            position = time_ms / self.video_media.get_duration()
            
            # Pause both players
            self.video_player.pause()
            self.audio_player.pause()
            
            # Set position for both players
            self.video_player.set_position(position)
            self.audio_player.set_position(position)
            
            # Use QTimer to check seek completion
            QtCore.QTimer.singleShot(50, self._check_seek_complete)


    def _check_seek_complete(self):
        if self.video_player.is_playing() or self.video_player.get_state() == vlc.State.Paused:
            self.seek_complete.emit()
        else:
            QtCore.QTimer.singleShot(50, self._check_seek_complete)

    @QtCore.pyqtSlot()
    def _on_seek_complete(self):
        self.is_seeking = False
        if not self.isPaused:
            self.video_player.play()
            self.audio_player.play()

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

        # Create media for video and audio streams
        self.video_media = self.instance.media_new(video_stream)
        self.audio_media = self.instance.media_new(audio_stream)

        # Set hardware acceleration
        self.video_media.add_option('avcodec-hw=d3d11va')
        self.audio_media.add_option('avcodec-hw=d3d11va')

        # Set the media to the respective players
        self.video_player.set_media(self.video_media)
        self.audio_player.set_media(self.audio_media)

        # Play the media
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
            self.audio_player.play()
            self.audio_player.audio_set_volume(100)
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
        status = "Paused" if self.isPaused else "Seeking" if self.is_seeking else ""
        self.setWindowTitle(f"{base_title} ({status})" if status else base_title)
        if self.video_player.get_state() == vlc.State.Error or self.audio_player.get_state() == vlc.State.Error:
            print("Playback error detected. Attempting to reset...")
            self.video_player.stop()
            self.audio_player.stop()
            self.video_player.play()
            self.audio_player.play()