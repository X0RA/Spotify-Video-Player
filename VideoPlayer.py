import sys
import os.path
import vlc
from PyQt5 import QtWidgets, QtGui, QtCore

class MusicVideoPlayer(QtWidgets.QMainWindow):
    """A simple music video player using VLC and PyQt5."""
    media_loaded = QtCore.pyqtSignal(str)

    def __init__(self, master=None):
        super().__init__(master)
        self.setWindowTitle("Music Video Player")
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.isPaused = False
        self.media = None
        self._create_ui()
        self.media_loaded.connect(self._on_media_loaded)  

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
            self.pause()  # Assuming this is a method that correctly pauses the media.
        else:
            self.play()  # Assuming this is a method that correctly plays the media.
    
    def play(self):
        """Plays the currently loaded media."""
        if not self.mediaplayer.is_playing():
            self.mediaplayer.play()
            self.isPaused = False
            self.update_ui()
    
    def pause(self):
        """Pauses the currently playing media."""
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.isPaused = True
            self.update_ui()

    def play_media(self, media_path: str):
        """
        Plays a media file from a given path or URL.

        Args:
            media_path (str): The path or URL of the media file to play.
        """
        if not media_path:
            return

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
        Updates the user interface elements.  Override this method to add custom UI updates.
        """
        if self.isPaused:
            self.setWindowTitle("Music Video Player (Paused)")
        else:
            self.setWindowTitle("Music Video Player")
        pass
