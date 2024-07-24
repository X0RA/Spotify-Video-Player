import sys
import os
import vlc
from PyQt5 import QtWidgets, QtGui, QtCore
from dotenv import load_dotenv

class MusicVideoPlayer(QtWidgets.QMainWindow):
    """A simple music video player using VLC and PyQt5."""
    media_loaded = QtCore.pyqtSignal(str)

    def __init__(self, master=None):
        load_dotenv()
        self.start_muted = os.getenv('START_MUTED', 'False').lower() in ('true', '1', 't')
        self.start_fullscreen = os.getenv('START_FULLSCREEN', 'False').lower() in ('true', '1', 't')
        super().__init__(master)
        self.setWindowTitle("Music Video Player")
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.isPaused = False
        self.media = None
        self._create_ui()
        self.media_name = None
        self.media_loaded.connect(self._on_media_loaded)
        self.shortcut_fullscreen = QtWidgets.QShortcut(QtGui.QKeySequence("F"), self)
        self.shortcut_fullscreen.activated.connect(self.make_fullscreen)
        self.shortcut_mute = QtWidgets.QShortcut(QtGui.QKeySequence("M"), self)
        self.shortcut_mute.activated.connect(self.mute)
        if self.start_muted:
            self.mute()

        self.show()
        #TODO how is the fullscreening so broken on osx 
        # if self.start_fullscreen:
        #     QtCore.QTimer.singleShot(100, self.make_fullscreen)

    def _create_ui(self):
        """Creates the user interface elements."""
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
    
        # Video frame (where video will be rendered)
        self.videoframe = QtWidgets.QFrame()
        self.videoframe.setPalette(self._get_black_palette())
        self.videoframe.setAutoFillBackground(True)
    
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.videoframe)
        central_widget.setLayout(layout)
        
        # Invisible button to toggle play/pause
        self.toggle_button = QtWidgets.QPushButton("", self.videoframe)
        self.toggle_button.setGeometry(0, 0, self.videoframe.width(), self.videoframe.height())
        self.toggle_button.setFlat(True)
        self.toggle_button.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self.toggle_button.clicked.connect(self.toggle_play_pause)
        
        # Adjust the button size when the window is resized
        self.videoframe.installEventFilter(self)
    
        # Timer for UI updates
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200) 
        self.timer.timeout.connect(self.update_ui)

    def eventFilter(self, source, event):
        """Event filter to adjust the button size when the video frame is resized."""
        if event.type() == QtCore.QEvent.Resize and source == self.videoframe:
            self.toggle_button.setGeometry(0, 0, self.videoframe.width(), self.videoframe.height())
        return super().eventFilter(source, event)

    def _get_black_palette(self):
        """Helper to create a black palette for the videoframe."""
        palette = self.videoframe.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        return palette
    
    def toggle_play_pause(self):
        """Toggles between playing and pausing the media."""
        if self.mediaplayer.is_playing():
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Plays the currently loaded media."""
        if not self.mediaplayer.is_playing():
            self.mediaplayer.play()
            self.isPaused = False
            self.update_ui()

    def mute(self):
        """Mutes the audio."""
        self.mediaplayer.audio_toggle_mute()

    def seek(self, time):
        """Seeks the media to the specified time in milliseconds."""
        time = time / self.media.get_duration()
        self.mediaplayer.set_position(time)

    def make_fullscreen(self):
        """Toggles fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def pause(self):
        """Pauses the currently playing media."""
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.isPaused = True
            self.update_ui()

    def play_media(self, media_path: str, song_name: str = None):
        """
        Plays a media file from a given path or URL.

        Args:
            media_path (str): The path or URL of the media file to play.
        """
        if not media_path:
            return
        
        if song_name:
            self.media_name = song_name
            self.setWindowTitle(f"Music Video Player - {song_name}")

        try:
            media_path = media_path if media_path.startswith('http') else os.path.expanduser(media_path)
            self.media = self.instance.media_new(media_path)
            self.mediaplayer.set_media(self.media)
            self.media.parse()

            self.media_loaded.emit(media_path)

        except Exception as e:
            print(f"Error playing media: {e}")

    @QtCore.pyqtSlot(str)
    def _on_media_loaded(self, media_path):
        """Slot connected to the media_loaded signal."""
        try:
            if sys.platform.startswith('linux'):
                self.mediaplayer.set_xwindow(int(self.videoframe.winId()))
            elif sys.platform == "win32":
                self.mediaplayer.set_hwnd(int(self.videoframe.winId()))
            elif sys.platform == "darwin":
                self.mediaplayer.set_nsobject(int(self.videoframe.winId()))
            else:
                raise RuntimeError(f"Unsupported platform: {sys.platform}")

            self.mediaplayer.play()
            self.timer.start()
        except Exception as e:
            print(f"Error in _on_media_loaded: {e}")

    def update_ui(self):
        """
        Updates the user interface elements. Override this method to add custom UI updates.
        """
        base_title = f"{self.media_name}" if self.media_name else "Music Video Player"
        if self.isPaused:
            self.setWindowTitle(f"{base_title} (Paused)")
        else:
            self.setWindowTitle(base_title)