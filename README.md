
# Spotify Video Player

## Introduction
The Spotify Video Player is a tool that allows you to sync and play videos based on your Spotify playback

## Getting Started
To get started, you'll need to set up your environment and configure the player.

### Settings
The Spotify Video Player uses settings to store user preferences and API credentials. These settings are stored in a JSON file located in the user's data directory. The settings panel will show up on the first run of the application and can subsequently be opened with `h` on the video player.

#### Location of Settings File
The settings file is stored in a platform-specific user data directory:

On Windows: `C:\Users\<Username>\AppData\Local\spotify-video-player\settings.json`
On macOS: `/Users/<Username>/Library/Application Support/spotify-video-player/settings.json`
On Linux: `/home/<Username>/.local/share/spotify-video-player/settings.json`

#### Spotify API Credentials
To use this application, you need to obtain Spotify API credentials:

Go to https://developer.spotify.com/dashboard/
Log in with your Spotify account (or create one if you don't have it)
Click on "Create an App"
Fill in the app name and description
Once created, you'll see your Client ID and you can click "Show Client Secret" to reveal your Client Secret

### Installation

This project requires VLC to be installed as it's player and bindings:
https://www.videolan.org/vlc/

Also, if installing globally, I recommend the nightly install of yt-dlp (which is in the requirements). This might also need to be kept up to date. Modern youtube provides separate audio and video streams but only one stream for a combined stream which is only at 480p or something. That one has the best support at the moment since the separate steams need to be kept in sync (at least with my implementation).

To install the required packages, follow these steps:

1. Create a Virtual Environment (Optional):

- Windows:
```
python -m venv your-env-name
your-env-name\Scripts\activate
```

- Linux and macOS:
```
python3 -m venv your-env-name
source your-env-name/bin/activate
```


2. Install Requirements:
Install the necessary packages using the provided requirements.txt file:

```
pip install -r requirements.txt
```


## Usage

After setting up your environment and installing the requirements, you can start the `main.js` file. It should just do it's thing... or not idk.

### Controls

It mainly syncs playback from spotify

### Keybinds

The video player has the following keybindings:

- `f`: Toggle fullscreen mode.
- `m`: Mute or unmute the player.
- `space`: Play/Pause toggle
- `s`: Toggle mute on spotify
- `n`: Next song on spotify
- `p`: Previous song on spotify
- `h`: Open the settings panel


## TODO
- If you want to watch the videos (since sometimes they are longer than the actual song) over having them just for visual aesthetic then add options for fully letting the videos play out then after initiating the song change on spotify (realistically spotify is just the playlist at this point why not just scrape the playlist)
- More controls on the player (maybe some cool hover ones)
- Option to sync up with spotify right after the video loads
- Fix some of the seeking issues
