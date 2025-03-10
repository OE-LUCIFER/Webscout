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
                            # print(f"Copilot: {h}")
                            if has_nodriver:
                                yield {"type": "login", "provider": self.label, "url": os.environ.get("webscout_login", "")}
                                self._access_token, self._cookies = asyncio.run(get_access_token_and_cookies(self.url, self.proxies.get("https")))
                            else:
                                raise h
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
                    # print(f"Copilot: User: {user or 'null'}")

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
                        # print(f"Copilot: Created conversation: {conversation_id}")
                    else:
                        conversation_id = conversation.conversation_id
                        # print(f"Copilot: Use conversation: {conversation_id}")

                    # Handle image uploads if any
                    uploaded_images = []
                    if images is not None:
                        for image, _ in images:
                            # Convert image to bytes if needed
                            if isinstance(image, str):
                                if image.startswith("data:"):
                                    # Data URL
                                    header, encoded = image.split(",", 1)
                                    data = base64.b64decode(encoded)
                                else:
                                    # File path or URL
                                    with open(image, "rb") as f:
                                        data = f.read()
                            else:
                                data = image
                                
                            # Get content type
                            content_type = "image/jpeg"  # Default
                            if data[:2] == b'\xff\xd8':
                                content_type = "image/jpeg"
                            elif data[:8] == b'\x89PNG\r\n\x1a\n':
                                content_type = "image/png"
                            elif data[:6] in (b'GIF87a', b'GIF89a'):
                                content_type = "image/gif"
                            elif data[:2] in (b'BM', b'BA'):
                                content_type = "image/bmp"
                            
                            response = session.post(
                                f"{self.url}/c/api/attachments",
                                headers={"content-type": content_type},
                                data=data
                            )
                            if response.status_code != 200:
                                raise exceptions.APIConnectionError(f"Status {response.status_code}: {response.text}")
                            uploaded_images.append({"type":"image", "url": response.json().get("url")})
                            break

                    # Connect to WebSocket
                    wss = session.ws_connect(websocket_url)
                    wss.send(json.dumps({
                        "event": "send",
                        "conversationId": conversation_id,
                        "content": [*uploaded_images, {
                            "type": "text",
                            "text": conversation_prompt,
                        }],
                        "mode": "chat"
                    }).encode(), CurlWsFlag.TEXT)

                    # Process response
                    is_started = False
                    msg = None
                    image_prompt: str = None
                    last_msg = None
                    streaming_text = ""
                    
                    try:
                        while True:
                            try:
                                msg = wss.recv()[0]
                                msg = json.loads(msg)
                            except:
                                break
                            last_msg = msg
                            if msg.get("event") == "appendText":
                                is_started = True
                                content = msg.get("text")
                                streaming_text += content
                                resp = {"text": content}
                                yield resp if raw else resp
                            elif msg.get("event") == "generatingImage":
                                image_prompt = msg.get("prompt")
                            elif msg.get("event") == "imageGenerated":
                                yield {"type": "image", "url": msg.get("url"), "prompt": image_prompt, "preview": msg.get("thumbnailUrl")}
                            elif msg.get("event") == "done":
                                break
                            elif msg.get("event") == "replaceText":
                                content = msg.get("text")
                                streaming_text += content
                                resp = {"text": content}
                                yield resp if raw else resp
                            elif msg.get("event") == "error":
                                raise exceptions.FailedToGenerateResponseError(f"Error: {msg}")
                        
                        if not is_started:
                            raise exceptions.FailedToGenerateResponseError(f"Invalid response: {last_msg}")
                            
                        # Update conversation history
                        self.conversation.update_chat_history(prompt, streaming_text)
                        self.last_response = {"text": streaming_text}
                        
                    finally:
                        wss.close()
                        
            except requests.RequestException as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Error: {str(e)}")

        def for_non_stream():
            streaming_text = ""
            for response in for_stream():
                if isinstance(response, dict) and "text" in response:
                    streaming_text += response["text"]
            self.last_response = {"text": streaming_text}
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
        def for_stream():
            for response in self.ask(prompt, True, optimizer=optimizer, 
                                     conversationally=conversationally, 
                                     images=images, api_key=api_key, **kwargs):
                if isinstance(response, dict) and "text" in response:
                    yield response["text"]
                elif isinstance(response, dict) and "type" in response and response["type"] == "image":
                    yield f"\n![Image]({response['url']})\n"
                    
        def for_non_stream():
            response = self.ask(prompt, False, optimizer=optimizer, 
                                conversationally=conversationally,
                                images=images, api_key=api_key, **kwargs)
            return self.get_message(response)
            
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")


async def get_access_token_and_cookies(url: str, proxy: str = None, target: str = "ChatAI"):
    browser, stop_browser = await get_nodriver(proxy=proxy, user_data_dir="copilot")
    try:
        page = await browser.get(url)
        access_token = None
        while access_token is None:
            access_token = await page.evaluate("""
                (() => {
                    for (var i = 0; i < localStorage.length; i++) {
                        try {
                            item = JSON.parse(localStorage.getItem(localStorage.key(i)));
                            if (item.credentialType == "AccessToken" 
                                && item.expiresOn > Math.floor(Date.now() / 1000)
                                && item.target.includes("target")) {
                                return item.secret;
                            }
                        } catch(e) {}
                    }
                })()
            """.replace('"target"', json.dumps(target)))
            if access_token is None:
                await asyncio.sleep(1)
        cookies = {}
        for c in await page.send(nodriver.cdp.network.get_cookies([url])):
            cookies[c.name] = c.value
        await page.close()
        return access_token, cookies
    finally:
        stop_browser()


def readHAR(url: str):
    api_key = None
    cookies = None
    har_files = []
    # Look for HAR files in common locations
    har_paths = [
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Desktop")
    ]
    for path in har_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(".har"):
                    har_files.append(os.path.join(path, file))
    
    for path in har_files:
        with open(path, 'rb') as file:
            try:
                harFile = json.loads(file.read())
            except json.JSONDecodeError:
                # Error: not a HAR file!
                continue
            for v in harFile['log']['entries']:
                if v['request']['url'].startswith(url):
                    v_headers = {h['name'].lower(): h['value'] for h in v['request']['headers']}
                    if "authorization" in v_headers:
                        api_key = v_headers["authorization"].split(maxsplit=1).pop()
                    if v['request']['cookies']:
                        cookies = {c['name']: c['value'] for c in v['request']['cookies']}
    if api_key is None:
        raise NoValidHarFileError("No access token found in .har files")

    return api_key, cookies


# def get_clarity() -> bytes:
#     body = base64.b64decode("H4sIAAAAAAAAA23RwU7DMAwG4HfJ2aqS2E5ibjxH1cMOnQYqYZvUTQPx7vyJRGGAemj01XWcP+9udg+j80MetDhSyrEISc5GrqrtZnmaTydHbrdUnSsWYT2u+8Obo0Ce/IQvaDBmjkwhUlKKIRNHmQgosqEArWPRDQMx90rxeUMPzB1j+UJvwNIxhTvsPcXyX1T+rizE4juK3mEEhpAUg/JvzW1/+U/tB1LATmhqotoiweMea50PLy2vui4LOY3XfD1dwnkor5fn/e18XBFgm6fHjSzZmCyV7d3aRByAEYextaTHEH3i5pgKGVP/s+DScE5PuLKIpW6FnCi1gY3Rbpqmj0/DI/+L7QEAAA==")
#     return body


async def get_nodriver(proxy=None, user_data_dir=None):
    browser = await nodriver.Browser(
        headless=True,
        proxy=proxy,
        user_data_dir=user_data_dir
    )
    return browser, lambda: browser.close()


if __name__ == "__main__":
    from rich import print
    ai = Copilot(timeout=900)
    response = ai.chat(input("> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)