import json
import os
from pathlib import Path
from typing import Dict, Optional

from DeepWEBS.utilsdw.logger import OSLogger


class OSEnver:
    """Manages the OS environment variables."""

    def __init__(self) -> None:
        """Initializes the OSEnver object."""
        self.envs_stack: list[Dict[str, str]] = []
        self.envs: Dict[str, str] = os.environ.copy()

    def store_envs(self) -> None:
        """Stores a copy of the current environment variables on a stack."""
        self.envs_stack.append(self.envs.copy())

    def restore_envs(self) -> None:
        """Restores environment variables from the top of the stack."""
        self.envs = self.envs_stack.pop()

    def set_envs(
        self,
        secrets: bool = True,
        proxies: Optional[str] = None,
        store_envs: bool = True,
    ) -> None:
        """Sets environment variables based on the contents of secrets.json.

        Args:
            secrets (bool): Whether to load secrets from secrets.json.
            proxies (Optional[str]): Proxy URL to set as environment variable.
            store_envs (bool): Whether to store a copy of the environment variables
                on the stack.
        """
        if store_envs:
            self.store_envs()

        if secrets:
            secrets_path = Path(__file__).parents[1] / "secrets.json"
            if secrets_path.exists():
                with open(secrets_path, "r") as rf:
                    secrets = json.load(rf)
            else:
                secrets = {}

        if proxies:
            for proxy_env in ["http_proxy", "https_proxy"]:
                if isinstance(proxies, str):
                    self.envs[proxy_env] = proxies
                elif "http_proxy" in secrets.keys():
                    self.envs[proxy_env] = secrets["http_proxy"]
                elif os.getenv("http_proxy"):
                    self.envs[proxy_env] = os.getenv("http_proxy")
                else:
                    continue

        self.proxy = (
            self.envs.get("all_proxy")
            or self.envs.get("http_proxy")
            or self.envs.get("https_proxy")
            or None
        )
        self.requests_proxies = {
            "http": self.proxy,
            "https": self.proxy,
        }

        if self.proxy:
            OSLogger().note(f"Using proxy: [{self.proxy}]")


enver: OSEnver = OSEnver()


