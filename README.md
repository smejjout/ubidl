# ubidl

Downloader for ubicast media server.

Change the config according to your situation.

You can find you API key using this guide: https://ubicast.tv/static/mediaserver/docs/api/index.html#authentication

# Installation

You must have ffmpeg installed: https://www.ffmpeg.org/download.html

You must run this command to install the dependencies :

```
pip install -r requirements.txt
```

# Config

The config.json file must have this format :

```json
{
    "api_key": "aaaaa-bbbbb-ccccc-ddddd-eeeee",
    "ubicast_server": "https://ubicast.server.com/"
}
```

# Usage

```
python main.py <link> [, <link>, <link>, <link>, ...]
```
