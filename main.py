# Downloader for ubicast media servers

from os.path import exists
import sys
import re
import requests
import json
import ffmpeg


def remove_forbidden_characters(string: str) -> str:
    """ Removes the forbidden characters from a string.

    Args:
        string (str): The requested string.

    Returns:
        str: The requested string without the forbidden characters.
    """
    return re.sub(r"(\\|\/|:|\*|\?|\"|<|>|\|)", " ", string).strip()


class UbicastDownloader:
    def __init__(self, ubicast_server: str, api_key: str, verify: bool = False):
        """ Create an Ubicast Downloader object.

        Args:
            ubicast_server (str): The ubicast server url.
            api_key (str): The ubicast API key.
            verify (bool, optional): True if the connection must be secure, False otherwise. Defaults to False.
        """
        self.__ubicast_server = ubicast_server
        self.__api_key = api_key
        self.__verify = verify

    def oid_from_permalink(self, url: str) -> str:
        """ Get the oid from an ubicast permalink URL.

        Args:
            url (str): The requested URL.

        Raises:
            ValueError: if the URL is not a permalink.

        Returns:
            str: The oid of the URL.
        """
        # Value Checking
        if "/permalink/" not in url:
            raise ValueError("The requested URL is not a permalink.")

        return re.sub(r"(.*/permalink/|/)", "", url)

    def oid_from_videolink(self, url: str) -> str:
        """ Get the oid from an ubicast videolink URL.

        Args:
            url (str): The requested URL.

        Raises:
            ValueError: if the URL is not a videolink or if the data from the ubicast server is unreadable.
            ConnectionError: if the ubicast server is unreachable.

        Returns:
            str: The oid of the URL.
        """
        # Value Checking
        if "/videos/" not in url:
            raise ValueError("The requested URL is not a videolink.")

        slug = re.sub(r"(.*/videos/|/)", "", url)

        params = {"api_key": self.__api_key, "slug": slug}

        # Try to get info from the server
        try:
            res = requests.get(
                f"{self.__ubicast_server}/api/v2/medias/get/", params=params, verify=self.__verify)
        except:
            raise ConnectionError("The ubicast server is unreachable.")

        # Try to read the data
        try:
            return json.loads(res.content)["info"]["oid"]
        except:
            raise ValueError("The data from the ubicast server is unreadable.")

    def get_oid(self, url: str) -> str:
        """ Get the oid of an ubicast URL.

        Args:
            url (str): The requested URL.

        Raises:
            ValueError: if the requested URL is unrecognized or if the data from the ubicast server is unreadable.
            ConnectionError: if the ubicast server is unreachable.

        Returns:
            str: The oid of the requested URL.
        """
        if "/permalink/" in url:
            return self.oid_from_permalink(url)
        elif "/videos/" in url:
            return self.oid_from_videolink(url)
        else:
            raise ValueError("The requested URL is unrecognized.")

    def get_oid_info(self, oid: str) -> dict:
        """ Get informations about an oid.

        Args:
            oid (str): The requested oid.

        Raises:
            ConnectionError: if the ubicast server is unreachable.
            ValueError: if the data from the ubicast server is unreadable.

        Returns:
            dict: The oid informations.
        """
        params = {"api_key": self.__api_key,
                  "oid": oid, "html5": "mp4_mp3_m3u8"}

        # Try to get the video info from the server
        try:
            res = requests.get(
                f"{self.__ubicast_server}/api/v2/medias/modes/", params=params, verify=self.__verify)
        except:
            raise ConnectionError("The ubicast server is unreachable.")

        # Try to read the data
        try:
            info = json.loads(res.content)

            # Create video info
            video_tracks = info["names"] if "names" in info else []
            if "audio" in video_tracks:
                video_tracks.remove("audio")

            # Get audio info
            audio_tracks = []
            if (
                "audio" in info
                and info["audio"] is not None
                and "tracks" in info["audio"]
                and info["audio"]["tracks"] is not None
            ):
                for track in info["audio"]["tracks"]:
                    audio_tracks.append(
                        {
                            "language": track["language"] if "language" in track else None,
                            "title": track["title"] if "title" in track else None,
                        }
                    )

            # Return the info
            return {"video": video_tracks, "audio": audio_tracks}
        except:
            raise ValueError("The data from the ubicast server is unreadable.")

    def download(self, oid: str, path: str, video_track_name: str = None, audio_track_id: int = None,  extension: str = ".mp4"):
        """ Download a file from the ubicast server.

        Args:
            oid (str): The requested oid.
            path (str): The download path.
            video_track_name (str, optional): The video track name. Defaults to None.
            audio_track_id (int, optional): The audio track id. Defaults to None.
            extension (str, optional): The file extension. Defaults to ".mp4".

        Raises:
            NotADirectoryError: if the path is invalid.
            ValueError: if a parameters has an invalid value or if the data from the ubicast server is unreadable.
            ConnectionError: if the ubicast server is unreachable.
        """
        # Value Checking
        if not exists(path):
            raise NotADirectoryError("The path is invalid.")
        if video_track_name is None and audio_track_id is None:
            raise ValueError(
                "There must be a video track or an audio track selected.")

        # Get the video info
        dict_vid = self.get_oid_info(oid)

        # Value Checking
        if video_track_name is not None and len(dict_vid["video"]) == 0:
            raise ValueError("There is no video track available.")

        if audio_track_id is not None and len(dict_vid["audio"]) == 0:
            raise ValueError("There is no audio track available.")

        if video_track_name is not None and video_track_name not in dict_vid["video"]:
            raise ValueError("The chosen video track is invalid.")

        if audio_track_id is not None and (audio_track_id < 0 or len(dict_vid["audio"]) <= audio_track_id):
            raise ValueError("The chosen audio track is invalid.")

        # Get the title
        params1 = {"api_key": self.__api_key, "oid": oid}
        params2 = {"api_key": self.__api_key,
                   "oid": oid, "html5": "mp4_mp3_m3u8"}

        try:
            res1 = requests.get(
                f"{self.__ubicast_server}/api/v2/medias/get/", params=params1, verify=self.__verify)
            res2 = requests.get(
                f"{self.__ubicast_server}/api/v2/medias/modes/", params=params2, verify=self.__verify)
        except:
            raise ConnectionError("The ubicast server is unreachable.")

        try:
            title = remove_forbidden_characters(
                json.loads(res1.content)["info"]["title"])
            info = json.loads(res2.content)
        except:
            raise ValueError("The data from the ubicast server is unreadable.")

        # Create the filepath
        filepath = f"{path}/{title}{extension}"
        number = 0
        while exists(filepath):
            filepath = f"{path}/{title} ({number}){extension}"
            number += 1

        # Create the args
        args = []
        if video_track_name is not None:
            video_url = info[video_track_name]["resource"]["url"]
            args.append(ffmpeg.input(video_url))

        if audio_track_id is not None:
            audio_url = info["audio"]["tracks"][audio_track_id]["url"]
            args.append(ffmpeg.input(audio_url))

        args.append(filepath)

        stream = ffmpeg.output(*args, codec="copy")

        # Try to download
        ffmpeg.run(stream)


def choice(options: list, prompt: str):
    """ Asks the user to select an item from a list of optiosn.

    Args:
        options (list): The list of options.
        prompt (str): The message that will be displayed after the options.

    Returns:
        Any: The selected option from the list.
    """
    i = 1
    for option in options:
        print(f"{option} : {i}")
        i = i + 1

    choices = [str(c) for c in range(1, len(options) + 1)]

    while True:
        output = input(prompt)
        if output in choices:
            output = int(output) - 1
            output = options[output]
            return output
        else:
            print("Bad option. Options: " + ", ".join(options))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"Usage: {sys.argv[0]} <link> [, <link>, <link>, <link>, ...]")
        exit()

    # Read the config file
    with open("config.json") as config_file:
        config = json.load(config_file)
        api_key = config["api_key"]
        ubicast_server = config["ubicast_server"]
        verify = config["verify"] if "verify" in config else False

    ubidl = UbicastDownloader(ubicast_server, api_key, verify)

    urls = sys.argv[1:]
    for url in urls:
        try:
            # Get the url oid
            oid = ubidl.get_oid(url)

            # Get the video info
            dict_vid = ubidl.get_oid_info(oid)

            # Choose the tracks
            video_track_name = choice(dict_vid["video"], "Choose a stream: ")
            audio_track_id = 0 if len(dict_vid["audio"]) > 0 else None

            # Download
            ubidl.download(oid, "./", video_track_name, audio_track_id)

        except KeyboardInterrupt:
            exit(1)

        except Exception as err:
            print(err)
