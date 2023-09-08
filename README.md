# Project Name

## Table of Contents

- [Introduction](#introduction)
- [Contributing](#contributing)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [License](#license)
- [Dependencies](#dependencies)

## Introduction

Participate in live chat, and trigger MIDI notes through chat messages. The application leverages the Twitch IRC (Internet Relay Chat) to enable real-time interactions with viewers. When users send specific chat messages containing MIDI note information, the application converts them into MIDI signals and plays corresponding musical notes through the connected MIDI device.

## Contributing

Take a look at [CONTRIBUTING](CONTRIBUTING)

## Installation

Right now please use a software to create a virtual midi port. I use [LoopBe1](https://www.nerds.de/en/download.html) on Windows.

1. Clone this repository to your local machine.
2. Install the required dependencies by running the following command:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

run the main.py file

```bash
python main.py
```

## Configuration

Click the config button to open the configuration window. You can configure the following settings:
  
- server=your_server
- port=your_port
- nickname=your_nickname (the one linked to your OAuth token)
- token=your_token (OAuth token you can get from <https://twitchapps.com/tmi/>)
- channel=your_channel (the channel you want to join preceded by a #)

## License

[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)

## Dependencies

- emoji==2.7.0
- mido==1.3.0
- packaging==23.1
- python-dotenv==1.0.0
- python-rtmidi==1.5.5


## Notation

- C5:2:100 = C in the 5th octave, 2 beats, 100 velocity Defaults: 5th octave, 1 beat, 100 velocity
- C5:2,E5:2,G5:2 = C, E, G in the 5th octave, 2 beats each played together
- C5:2 E5:2 G5:2 = C, E, G in the 5th octave, 2 beats each played after each other
- C5:2 X:2 G5:2 = C, G in the 5th octave, 2 beats each played after each other with a 2 beat pause in between