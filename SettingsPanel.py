import json
import os
from PyQt5 import QtWidgets, QtCore
from platformdirs import user_data_dir



class SettingsPanel(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_dir = user_data_dir("spotify-video-player") # Directory for the settings file
        self.settings_file = os.path.join(self.settings_dir, 'settings.json')
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.settings = {}
        self.load_settings()
        self.create_widgets()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                'CLIENT_ID': '',
                'CLIENT_SECRET': '',
                'REFRESH_TIMEOUT': '1',
                'START_MUTED': False,
                'START_FULLSCREEN': False
            }

    def save_settings(self):
        os.makedirs(self.settings_dir, exist_ok=True)  # Ensure the directory exists
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)

    def create_widgets(self):
        self.client_id = QtWidgets.QLineEdit(self.settings.get('CLIENT_ID', ''))
        self.client_secret = QtWidgets.QLineEdit(self.settings.get('CLIENT_SECRET', ''))
        self.refresh_timeout = QtWidgets.QLineEdit(str(self.settings.get('REFRESH_TIMEOUT', '1')))
        self.start_muted = QtWidgets.QCheckBox("Start Muted")
        self.start_muted.setChecked(self.settings.get('START_MUTED', False))
        self.start_fullscreen = QtWidgets.QCheckBox("Start Fullscreen")
        self.start_fullscreen.setChecked(self.settings.get('START_FULLSCREEN', False))

        self.layout.addWidget(QtWidgets.QLabel("Spotify Client ID:"))
        self.layout.addWidget(self.client_id)
        self.layout.addWidget(QtWidgets.QLabel("Spotify Client Secret:"))
        self.layout.addWidget(self.client_secret)
        self.layout.addWidget(QtWidgets.QLabel("Refresh Timeout:"))
        self.layout.addWidget(self.refresh_timeout)
        self.layout.addWidget(self.start_muted)
        self.layout.addWidget(self.start_fullscreen)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.on_save)
        self.layout.addWidget(self.save_button)

    def on_save(self):
        self.settings['CLIENT_ID'] = self.client_id.text()
        self.settings['CLIENT_SECRET'] = self.client_secret.text()
        self.settings['REFRESH_TIMEOUT'] = self.refresh_timeout.text()
        self.settings['START_MUTED'] = self.start_muted.isChecked()
        self.settings['START_FULLSCREEN'] = self.start_fullscreen.isChecked()
        self.save_settings()
        self.accept()

@staticmethod
def get_settings():
    settings_file = os.path.join(user_data_dir("spotify-video-player"), 'settings.json')
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                return json.load(f)
    except (OSError, IOError) as e:
        print(f"Error reading file: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    return {}

def show_settings_panel(parent=None):
    dialog = SettingsPanel(parent)
    result = dialog.exec_()
    return result == QtWidgets.QDialog.Accepted