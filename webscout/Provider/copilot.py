import os
import json
import base64
import asyncio
import requests
from urllib.parse import quote
from typing import Optional, Dict, Any, List, Union, Generator

from curl_cffi.requests import Session, CurlWsFlag

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions
from webscout import LitAgent

try:
    has_curl_cffi = True
except ImportError:
    has_curl_cffi = False

try:
    import nodriver
    has_nodriver = True
except ImportError:
    has_nodriver = False


class NoValidHarFileError(Exception):
    pass


class CopilotConversation:
    conversation_id: str

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id


class Copilot(Provider):
    """
    A class to interact with the Microsoft Copilot API.
    """
    
    AVAILABLE_MODELS = ["Copilot"]
    url = "https://copilot.microsoft.com"
    websocket_url = "wss://copilot.microsoft.com/c/api/chat?api-version=2"
    conversation_url = f"{url}/c/api/conversations"

    _access_token: str = None
    _cookies: dict = None

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2000,
        timeout: int = 900,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "Copilot"
    ):
        """Initializes the Copilot API client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        # Use LitAgent for user-agent
        self.headers = {
            'User-Agent': LitAgent().random(),
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': self.url,
            'Referer': f'{self.url}/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.proxies = proxies

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def ask(
        self,
        prompt: str,
        stream: bool = True,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        images = None,
        api_key: str = None,
        **kwargs
    ) -> Union[Dict[str, Any], Generator]:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        # Main logic for calling Copilot API
        def for_stream():
            try:
                if not has_curl_cffi:
                    raise Exception('Install or update "curl_cffi" package | pip install -U curl_cffi')

                websocket_url = self.websocket_url
                headers = None
                
                if images is not None:
                    if api_key is not None:
                        self._access_token = api_key
                    if self._access_token is None:
                        try:
                            self._access_token, self._cookies = readHAR(self.url)
                        except NoValidHarFileError as h:
                            if has_nodriver:
                                yield {"type": "login", "provider": self.label, "url": os.environ.get("webscout_login", "")}
                                self._access_token, self._cookies = asyncio.run(get_access_token_and_cookies(self.url, self.proxies.get("https")))
                            else:
                                raise Exception("nodriver package is required for image uploads. Install it with: pip install nodriver")
                    websocket_url = f"{websocket_url}&accessToken={quote(self._access_token)}"
                    headers = {"authorization": f"Bearer {self._access_token}"}

                with Session(
                    timeout=self.timeout,
                    proxy=self.proxies.get("https"),
                    impersonate="chrome",
                    headers=headers,
                    cookies=self._cookies,
                ) as session:
                    if self._access_token is not None:
                        self._cookies = session.cookies.jar if hasattr(session.cookies, "jar") else session.cookies
                    
                    response = session.get(f"{self.url}/c/api/user")
                    if response.status_code == 401:
                        raise exceptions.AuthenticationError("Status 401: Invalid access token")
                    if response.status_code != 200:
                        raise exceptions.APIConnectionError(f"Status {response.status_code}: {response.text}")
                    user = response.json().get('firstName')
                    if user is None:
                        self._access_token = None

                    # Create or use existing conversation
                    conversation = kwargs.get("conversation", None)
                    if conversation is None:
                        response = session.post(self.conversation_url)
                        if response.status_code != 200:
                            raise exceptions.APIConnectionError(f"Status {response.status_code}: {response.text}")
                        conversation_id = response.json().get("id")
                        conversation = CopilotConversation(conversation_id)
                        if kwargs.get("return_conversation", False):
                            yield conversation
                    else:
                        conversation_id = conversation.conversation_id

                    # Handle image uploads if any
                    uploaded_images = []
                    if images is not None and has_nodriver:
                        for image, _ in images:
                            # Convert image to bytes if needed
                            if isinstance(image, str):
                                if image.startswith("data:"):
                                    # Data URL
                                    header, encoded = image.split(",", 1)
                                    data = base64.b64decode(encoded)
                                else:
                                    # File path or URL
                                    try:
                                        with open(image, "rb") as f:
                                            data = f.read()
                                    except FileNotFoundError:
                                        response = requests.get(image)
                                        if response.status_code != 200:
                                            raise Exception(f"Failed to download image from URL: {image}")
                                        data = response.content
                            else:
                                data = image

                            # Upload image
                            response = session.post(
                                f"{self.url}/c/api/images",
                                files={"file": ("image.png", data, "image/png")},
                                headers={"authorization": f"Bearer {self._access_token}"}
                            )
                            if response.status_code != 200:
                                raise exceptions.APIConnectionError(f"Failed to upload image: {response.text}")
                            uploaded_images.append(response.json().get("id"))

                    # Send message
                    payload = {
                        "conversationId": conversation_id,
                        "message": conversation_prompt,
                        "images": uploaded_images,
                    }

                    response = session.post(
                        f"{self.conversation_url}/{conversation_id}/messages",
                        json=payload,
                        headers={"authorization": f"Bearer {self._access_token}"}
                    )
                    if response.status_code != 200:
                        raise exceptions.APIConnectionError(f"Failed to send message: {response.text}")

                    # Stream response
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("type") == "message":
                                    content = data.get("content", "")
                                    if content:
                                        yield content if raw else dict(text=content)
                            except json.JSONDecodeError:
                                continue

                    self.last_response = {"text": ""}
                    self.conversation.update_chat_history(prompt, self.get_message(self.last_response))

            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"An error occurred: {str(e)}")

        def for_non_stream():
            # Run the generator to completion
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = True,
        optimizer: str = None,
        conversationally: bool = False,
        images = None,
        api_key: str = None,
        **kwargs
    ) -> Union[str, Generator]:
        """Generate response as a string using chat method"""
        def for_stream():
            for response in self.ask(prompt, True, optimizer=optimizer, conversationally=conversationally, images=images, api_key=api_key, **kwargs):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(prompt, False, optimizer=optimizer, conversationally=conversationally, images=images, api_key=api_key, **kwargs)
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if has_nodriver:
    async def get_access_token_and_cookies(url: str, proxy: str = None, target: str = "ChatAI"):
        """Get access token and cookies using nodriver"""
        browser = await get_nodriver(proxy)
        try:
            await browser.goto(url)
            await browser.wait_for_selector("button[data-testid='login-button']")
            await browser.click("button[data-testid='login-button']")
            await browser.wait_for_selector("input[type='email']")
            await browser.fill("input[type='email']", os.environ.get("webscout_email", ""))
            await browser.click("button[type='submit']")
            await browser.wait_for_selector("input[type='password']")
            await browser.fill("input[type='password']", os.environ.get("webscout_password", ""))
            await browser.click("button[type='submit']")
            await browser.wait_for_selector("button[data-testid='login-button']", timeout=10000)
            cookies = await browser.cookies()
            access_token = None
            for cookie in cookies:
                if cookie["name"] == "U":
                    access_token = cookie["value"]
                    break
            return access_token, {cookie["name"]: cookie["value"] for cookie in cookies}
        finally:
            await browser.close()

    async def get_nodriver(proxy=None, user_data_dir=None):
        """Get nodriver instance"""
        if user_data_dir is None:
            user_data_dir = os.path.join(os.path.expanduser("~"), ".webscout")
        os.makedirs(user_data_dir, exist_ok=True)
        return await nodriver.launch(
            proxy=proxy,
            user_data_dir=user_data_dir,
            headless=True,
        )

def readHAR(url: str):
    """Read HAR file for access token and cookies"""
    har_file = os.path.join(os.path.expanduser("~"), ".webscout", "copilot.har")
    if not os.path.exists(har_file):
        raise NoValidHarFileError("No valid HAR file found")
    with open(har_file, "r") as f:
        har = json.load(f)
    for entry in har["log"]["entries"]:
        if entry["request"]["url"] == url:
            cookies = {}
            for cookie in entry["request"]["cookies"]:
                cookies[cookie["name"]] = cookie["value"]
            access_token = None
            for cookie in cookies:
                if cookie == "U":
                    access_token = cookies[cookie]
                    break
            return access_token, cookies
    raise NoValidHarFileError("No valid HAR file found")


if __name__ == "__main__":
    from rich import print
    ai = Copilot(timeout=900)
    response = ai.chat(input("> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)