
# Spotify Video Player

## Introduction
The Spotify Video Player is a tool that allows you to sync and play videos based on your Spotify playback

## Getting Started
To get started, you'll need to set up your environment and configure the player.

### Environment Configuration
Within the .env file you'll find some config options and required api creds.

#### Spotify
Add your Spotify API credentials to the .env file. This includes **CLIENT_ID**, **CLIENT_SECRET**.

#### Player Settings:
**START_MUTED**: Set this flag to True if you want the player to start muted by default, otherwise set it to False.

**SYNC_PLAYBACK**: Set this flag to True to keep the player in sync with your Spotify playback. If you prefer to play videos as just 'something to glance at' without worrying about synchronization, set it to False. Also you might not get the video you want who knows.

*This is broken, probs just because i'm on osx and it's a piece of shit*
~~**START_FULLSCREEN*: Set this flag to True if you want the player to start in fullscreen mode.~~

### Installation

To install the required packages, follow these steps:

1. Create a Virtual Environment (Optional but Recommended):

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

Ya just click it to play pause

### Keybinds

The video player has the following keybindings:

- `f`: Toggle fullscreen mode.
- `m`: Mute or unmute the player.
- `space`: Play/Pause toggle