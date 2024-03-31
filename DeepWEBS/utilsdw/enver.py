import json
import os

from pathlib import Path
from DeepWEBS.utilsdw.logger import logger


class OSEnver:
    def __init__(self):
        self.envs_stack = []
        self.envs = os.environ.copy()

    def store_envs(self):
        self.envs_stack.append(self.envs)

    def restore_envs(self):
        self.envs = self.envs_stack.pop()

    def set_envs(self, secrets=True, proxies=None, store_envs=True):
        # caller_info = inspect.stack()[1]
        # logger.back(f"OS Envs is set by: {caller_info.filename}")

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
            logger.note(f"Using proxy: [{self.proxy}]")


enver = OSEnver()
