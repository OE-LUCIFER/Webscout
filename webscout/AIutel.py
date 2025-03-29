import json
import platform
import subprocess
from typing import Union



def sanitize_stream(
    chunk: str, intro_value: str = "data:", to_json: bool = True
) -> Union[str, dict]:
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
        help (str, optional): Help info in case of exception. Defaults to None.
    Returns:
        tuple : (is_successful, object[Exception|Subprocess.run])
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

from .conversation import Conversation

from .optimizers import Optimizers

from .Extra.autocoder import AutoCoder

from .prompt_manager import AwesomePrompts