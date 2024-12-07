import os
import json
import platform
import subprocess
import logging
import threading
import time
import datetime
import re
import sys
from rich.markdown import Markdown
from rich.console import Console
from typing import List, Tuple, Union
from typing import NoReturn
import requests
from pathlib import Path
from playsound import playsound
from time import sleep as wait
import pathlib
import urllib.parse

default_path = os.path.join(os.path.expanduser("~"), ".cache", "AIWEBS", "webscout")

def sanitize_stream(
    chunk: str, intro_value: str = "data:", to_json: bool = True
) -> str | dict:
    """Remove streaming flags

    Args:
        chunk (str): Streamig chunk.
        intro_value (str, optional): streaming flag. Defaults to "data:".
        to_json (bool, optional). Return chunk as dictionary. Defaults to True.

    Returns:
        str: Sanitized streaming value.
    """

    if chunk.startswith(intro_value):
        chunk = chunk[len(intro_value) :]

    return json.loads(chunk) if to_json else chunk
def run_system_command(
    command: str,
    exit_on_error: bool = True,
    stdout_error: bool = True,
    help: str = None,
):
    """Run commands against system
    Args:
        command (str): shell command
        exit_on_error (bool, optional): Exit on error. Defaults to True.
        stdout_error (bool, optional): Print out the error. Defaults to True
        help (str, optional): Help info incase of exception. Defaults to None.
    Returns:
        tuple : (is_successfull, object[Exception|Subprocess.run])
    """
    try:
        # Run the command and capture the output
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return (True, result)
    except subprocess.CalledProcessError as e:
        if exit_on_error:
            raise Exception(f"Command failed with exit code {e.returncode}") from e
        else:
            return (False, e)  


from .conversation import Conversation

from .optimizers import Optimizers

from .Extra.autocoder import AutoCoder

from .prompt_manager import AwesomePrompts

class Updates:
    """Webscout latest release info"""

    url = "https://api.github.com/repos/OE-LUCIFER/Webscout/releases/latest"

    @property
    def latest_version(self):
        return self.latest(version=True)

    def executable(self, system: str = platform.system()) -> str:
        """Url pointing to executable for particular system

        Args:
            system (str, optional): system name. Defaults to platform.system().

        Returns:
            str: url
        """
        for entry in self.latest()["assets"]:
            if entry.get("target") == system:
                return entry.get("url")

    def latest(self, whole: bool = False, version: bool = False) -> dict:
        """Check Webscout latest version info

        Args:
            whole (bool, optional): Return whole json response. Defaults to False.
            version (bool, optional): return version only. Defaults to False.

        Returns:
            bool|dict: version str or whole dict info
        """
        import requests

        data = requests.get(self.url).json()
        if whole:
            return data

        elif version:
            return data.get("tag_name")

        else:
            sorted = dict(
                tag_name=data.get("tag_name"),
                tarball_url=data.get("tarball_url"),
                zipball_url=data.get("zipball_url"),
                html_url=data.get("html_url"),
                body=data.get("body"),
            )
            whole_assets = []
            for entry in data.get("assets"):
                url = entry.get("browser_download_url")
                assets = dict(url=url, size=entry.get("size"))
                if ".deb" in url:
                    assets["target"] = "Debian"
                elif ".exe" in url:
                    assets["target"] = "Windows"
                elif "macos" in url:
                    assets["target"] = "Mac"
                elif "linux" in url:
                    assets["target"] = "Linux"

                whole_assets.append(assets)
            sorted["assets"] = whole_assets

            return sorted


class Audio:
    # Request headers
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    cache_dir = pathlib.Path("./audio_cache")
    all_voices: list[str] = [
        "Filiz",
        "Astrid",
        "Tatyana",
        "Maxim",
        "Carmen",
        "Ines",
        "Cristiano",
        "Vitoria",
        "Ricardo",
        "Maja",
        "Jan",
        "Jacek",
        "Ewa",
        "Ruben",
        "Lotte",
        "Liv",
        "Seoyeon",
        "Takumi",
        "Mizuki",
        "Giorgio",
        "Carla",
        "Bianca",
        "Karl",
        "Dora",
        "Mathieu",
        "Celine",
        "Chantal",
        "Penelope",
        "Miguel",
        "Mia",
        "Enrique",
        "Conchita",
        "Geraint",
        "Salli",
        "Matthew",
        "Kimberly",
        "Kendra",
        "Justin",
        "Joey",
        "Joanna",
        "Ivy",
        "Raveena",
        "Aditi",
        "Emma",
        "Brian",
        "Amy",
        "Russell",
        "Nicole",
        "Vicki",
        "Marlene",
        "Hans",
        "Naja",
        "Mads",
        "Gwyneth",
        "Zhiyu",
        "es-ES-Standard-A",
        "it-IT-Standard-A",
        "it-IT-Wavenet-A",
        "ja-JP-Standard-A",
        "ja-JP-Wavenet-A",
        "ko-KR-Standard-A",
        "ko-KR-Wavenet-A",
        "pt-BR-Standard-A",
        "tr-TR-Standard-A",
        "sv-SE-Standard-A",
        "nl-NL-Standard-A",
        "nl-NL-Wavenet-A",
        "en-US-Wavenet-A",
        "en-US-Wavenet-B",
        "en-US-Wavenet-C",
        "en-US-Wavenet-D",
        "en-US-Wavenet-E",
        "en-US-Wavenet-F",
        "en-GB-Standard-A",
        "en-GB-Standard-B",
        "en-GB-Standard-C",
        "en-GB-Standard-D",
        "en-GB-Wavenet-A",
        "en-GB-Wavenet-B",
        "en-GB-Wavenet-C",
        "en-GB-Wavenet-D",
        "en-US-Standard-B",
        "en-US-Standard-C",
        "en-US-Standard-D",
        "en-US-Standard-E",
        "de-DE-Standard-A",
        "de-DE-Standard-B",
        "de-DE-Wavenet-A",
        "de-DE-Wavenet-B",
        "de-DE-Wavenet-C",
        "de-DE-Wavenet-D",
        "en-AU-Standard-A",
        "en-AU-Standard-B",
        "en-AU-Wavenet-A",
        "en-AU-Wavenet-B",
        "en-AU-Wavenet-C",
        "en-AU-Wavenet-D",
        "en-AU-Standard-C",
        "en-AU-Standard-D",
        "fr-CA-Standard-A",
        "fr-CA-Standard-B",
        "fr-CA-Standard-C",
        "fr-CA-Standard-D",
        "fr-FR-Standard-C",
        "fr-FR-Standard-D",
        "fr-FR-Wavenet-A",
        "fr-FR-Wavenet-B",
        "fr-FR-Wavenet-C",
        "fr-FR-Wavenet-D",
        "da-DK-Wavenet-A",
        "pl-PL-Wavenet-A",
        "pl-PL-Wavenet-B",
        "pl-PL-Wavenet-C",
        "pl-PL-Wavenet-D",
        "pt-PT-Wavenet-A",
        "pt-PT-Wavenet-B",
        "pt-PT-Wavenet-C",
        "pt-PT-Wavenet-D",
        "ru-RU-Wavenet-A",
        "ru-RU-Wavenet-B",
        "ru-RU-Wavenet-C",
        "ru-RU-Wavenet-D",
        "sk-SK-Wavenet-A",
        "tr-TR-Wavenet-A",
        "tr-TR-Wavenet-B",
        "tr-TR-Wavenet-C",
        "tr-TR-Wavenet-D",
        "tr-TR-Wavenet-E",
        "uk-UA-Wavenet-A",
        "ar-XA-Wavenet-A",
        "ar-XA-Wavenet-B",
        "ar-XA-Wavenet-C",
        "cs-CZ-Wavenet-A",
        "nl-NL-Wavenet-B",
        "nl-NL-Wavenet-C",
        "nl-NL-Wavenet-D",
        "nl-NL-Wavenet-E",
        "en-IN-Wavenet-A",
        "en-IN-Wavenet-B",
        "en-IN-Wavenet-C",
        "fil-PH-Wavenet-A",
        "fi-FI-Wavenet-A",
        "el-GR-Wavenet-A",
        "hi-IN-Wavenet-A",
        "hi-IN-Wavenet-B",
        "hi-IN-Wavenet-C",
        "hu-HU-Wavenet-A",
        "id-ID-Wavenet-A",
        "id-ID-Wavenet-B",
        "id-ID-Wavenet-C",
        "it-IT-Wavenet-B",
        "it-IT-Wavenet-C",
        "it-IT-Wavenet-D",
        "ja-JP-Wavenet-B",
        "ja-JP-Wavenet-C",
        "ja-JP-Wavenet-D",
        "cmn-CN-Wavenet-A",
        "cmn-CN-Wavenet-B",
        "cmn-CN-Wavenet-C",
        "cmn-CN-Wavenet-D",
        "nb-no-Wavenet-E",
        "nb-no-Wavenet-A",
        "nb-no-Wavenet-B",
        "nb-no-Wavenet-C",
        "nb-no-Wavenet-D",
        "vi-VN-Wavenet-A",
        "vi-VN-Wavenet-B",
        "vi-VN-Wavenet-C",
        "vi-VN-Wavenet-D",
        "sr-rs-Standard-A",
        "lv-lv-Standard-A",
        "is-is-Standard-A",
        "bg-bg-Standard-A",
        "af-ZA-Standard-A",
        "Tracy",
        "Danny",
        "Huihui",
        "Yaoyao",
        "Kangkang",
        "HanHan",
        "Zhiwei",
        "Asaf",
        "An",
        "Stefanos",
        "Filip",
        "Ivan",
        "Heidi",
        "Herena",
        "Kalpana",
        "Hemant",
        "Matej",
        "Andika",
        "Rizwan",
        "Lado",
        "Valluvar",
        "Linda",
        "Heather",
        "Sean",
        "Michael",
        "Karsten",
        "Guillaume",
        "Pattara",
        "Jakub",
        "Szabolcs",
        "Hoda",
        "Naayf",
    ]

    @classmethod
    def text_to_audio(
        cls,
        message: str,
        voice: str = "Brian",
        save_to: Union[Path, str] = None,
        auto: bool = True,
    ) -> Union[str, bytes]:
        """
        Text to speech using StreamElements API

        Parameters:
            message (str): The text to convert to speech
            voice (str, optional): The voice to use for speech synthesis. Defaults to "Brian".
            save_to (bool, optional): Path to save the audio file. Defaults to None.
            auto (bool, optional): Generate filename based on `message` and save to `cls.cache_dir`. Defaults to False.

        Returns:
            result (Union[str, bytes]): Path to saved contents or audio content.
        """
        assert (
            voice in cls.all_voices
        ), f"Voice '{voice}' not one of [{', '.join(cls.all_voices)}]"
        # Base URL for provider API
        url: str = (
            f"https://api.streamelements.com/kappa/v2/speech?voice={voice}&text={{{urllib.parse.quote(message)}}}"
        )
        resp = requests.get(url=url, headers=cls.headers, stream=True)
        if not resp.ok:
            raise Exception(
                f"Failed to perform the operation - ({resp.status_code}, {resp.reason}) - {resp.text}"
            )

        def sanitize_filename(path):
            trash = [
                "\\",
                "/",
                ":",
                "*",
                "?",
                '"',
                "<",
                "|",
                ">",
            ]
            for val in trash:
                path = path.replace(val, "")
            return path.strip()

        if auto:
            filename: str = message + "..." if len(message) <= 40 else message[:40]
            save_to = cls.cache_dir / sanitize_filename(filename)
            save_to = save_to.as_posix()

        # Ensure cache_dir exists
        cls.cache_dir.mkdir(parents=True, exist_ok=True)

        if save_to:
            if not save_to.endswith("mp3"):
                save_to += ".mp3"

            with open(save_to, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=512):
                    fh.write(chunk)
        else:
            return resp.content
        return save_to

    @staticmethod
    def play(path_to_audio_file: Union[Path, str]) -> NoReturn:
        """Play audio (.mp3) using playsound.
        """
        if not Path(path_to_audio_file).is_file():
            raise FileNotFoundError(f"File does not exist - '{path_to_audio_file}'")
        playsound(path_to_audio_file)
# 