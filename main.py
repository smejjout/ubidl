# Downloader for ubicast media servers

import sys
import re
import requests
import json
import ffmpeg


if len(sys.argv) == 1:
    print(f"Usage:\
        {sys.argv[0]} <permalink>")
    exit()

with open("config.json") as config_file:
    config = json.load(config_file)
    api_key = config["api_key"]
    ubicast_server = config["ubicast_server"]

urls = sys.argv[1:]


def download(url):
    oid = re.sub('.*permalink', "", url).strip("/")
    params = {
        "api_key": api_key,
        "oid": oid,
        "html5": "mp4_mp3_m3u8"
    }

    res = requests.get(f"{ubicast_server}/api/v2/medias/modes/",
                       params=params, verify=False)
    dict_vid = json.loads(res.content)
    url_vid = dict_vid["720p"]["resource"]["url"]
    url_audio = dict_vid["audio"]["tracks"][0]["url"]

    params.pop("html5")
    res = requests.get(f"{ubicast_server}/api/v2/medias/get/",
                       params=params, verify=False)
    info_vid = json.loads(res.content)
    title = info_vid["info"]["title"]

    audio = ffmpeg.input(url_audio)
    video = ffmpeg.input(url_vid)
    stream = ffmpeg.output(audio, video, title+".mkv", codec="copy")
    ffmpeg.run(stream)


for url in urls:
    download(url)
