# Project Name

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Dependencies](#dependencies)

## Introduction

The Music Chat Client with MIDI Integration is a unique chat application that allows users to join a Twitch channel, participate in live chat, and trigger MIDI notes through chat messages. The application leverages the Twitch IRC (Internet Relay Chat) to enable real-time interactions with viewers. When users send specific chat messages containing MIDI note information, the application converts them into MIDI signals and plays corresponding musical notes through the connected MIDI device. This project is perfect for music streamers and enthusiasts who want to engage with their audience in a creative and interactive way.

## Installation

1. Clone this repository to your local machine.
2. Install the required dependencies by running the following command:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file and add the following environment variables:
  
- server=your_server
- port=your_port
- nickname=your_nickname (the one linked to your OAuth token)
- token=your_token (OAuth token you can get from <https://twitchapps.com/tmi/>)
- channel=your_channel (the channel you want to join preceded by a #)

## Usage

run the main.py file

```bash
python main.py
```

## Dependencies

- emoji==2.7.0
- mido==1.3.0
- packaging==23.1
- python-dotenv==1.0.0
- python-rtmidi==1.5.5
