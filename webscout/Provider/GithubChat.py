import requests
import json
import time
from typing import Any, Dict, List, Optional, Union, Generator

from webscout.AIutel import Conversation
from webscout.AIutel import Optimizers
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent

class GithubChat(Provider):
    """
    A class to interact with the GitHub Copilot Chat API.
    Uses cookies for authentication and supports streaming responses.
    """
    
    # Available models
    AVAILABLE_MODELS = [
        "gpt-4o",
        "o3-mini", 
        "o1", 
        "claude-3.5-sonnet",
        "claude-3.7-sonnet",
        "claude-3.7-sonnet-thought",
        "gemini-2.0-flash-001"

    ]
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2000,
        timeout: int = 60,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "gpt-4o",
        cookie_path: str = "cookies.json"
    ):
        """Initialize the GithubChat client."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {', '.join(self.AVAILABLE_MODELS)}")
            
        self.url = "https://github.com/copilot"
        self.api_url = "https://api.individual.githubcopilot.com"
        self.cookie_path = cookie_path
        self.session = requests.Session()
        self.session.proxies.update(proxies)
        
        # Load cookies for authentication
        self.cookies = self.load_cookies()
        
        # Set up headers for all requests
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": LitAgent().random(),
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Origin": "https://github.com",
            "Referer": "https://github.com/copilot",
            "GitHub-Verified-Fetch": "true",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        
        # Apply cookies to session
        if self.cookies:
            self.session.cookies.update(self.cookies)
        
        # Set default model
        self.model = model
        
        # Provider settings
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        
        # Available optimizers
        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        
        # Set up conversation
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
        
        # Store conversation data
        self._conversation_id = None
        self._access_token = None

    def load_cookies(self):
        """Load cookies from a JSON file"""
        try:
            with open(self.cookie_path, 'r') as f:
                cookies_data = json.load(f)
                
            # Convert the cookie list to a dictionary format for requests
            cookies = {}
            for cookie in cookies_data:
                # Only include cookies that are not expired and have a name and value
                if 'name' in cookie and 'value':
                    # Check if the cookie hasn't expired
                    if 'expirationDate' not in cookie or cookie['expirationDate'] > time.time():
                        cookies[cookie['name']] = cookie['value']
            
            return cookies
        except Exception:
            return {}

    def get_access_token(self):
        """Get GitHub Copilot access token."""
        if self._access_token:
            return self._access_token
            
        url = "https://github.com/github-copilot/chat/token"
        
        try:
            response = self.session.post(url, headers=self.headers)
            
            if response.status_code == 401:
                raise exceptions.AuthenticationError("Authentication failed. Please check your cookies.")
                
            if response.status_code != 200:
                raise exceptions.FailedToGenerateResponseError(f"Failed to get access token: {response.status_code}")
                
            data = response.json()
            self._access_token = data.get("token")
            
            if not self._access_token:
                raise exceptions.FailedToGenerateResponseError("Failed to extract access token from response")
                
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"Failed to get access token: {str(e)}")

    def create_conversation(self):
        """Create a new conversation with GitHub Copilot."""
        if self._conversation_id:
            return self._conversation_id
            
        access_token = self.get_access_token()
        url = f"{self.api_url}/github/chat/threads"
        
        headers = self.headers.copy()
        headers["Authorization"] = f"GitHub-Bearer {access_token}"
        
        try:
            response = self.session.post(url, headers=headers)
            
            if response.status_code == 401:
                # Token might be expired, try refreshing
                self._access_token = None
                access_token = self.get_access_token()
                headers["Authorization"] = f"GitHub-Bearer {access_token}"
                response = self.session.post(url, headers=headers)
                
            if response.status_code not in [200, 201]:
                raise exceptions.FailedToGenerateResponseError(f"Failed to create conversation: {response.status_code}")
                
            data = response.json()
            self._conversation_id = data.get("thread_id")
            
            if not self._conversation_id:
                raise exceptions.FailedToGenerateResponseError("Failed to extract conversation ID from response")
                
            return self._conversation_id
            
        except requests.exceptions.RequestException as e:
            raise exceptions.FailedToGenerateResponseError(f"Failed to create conversation: {str(e)}")

    def process_response(self, response, prompt: str):
        """Process streaming response and extract content."""
        full_text = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
                
            try:
                # Parse each line (remove "data: " prefix)
                json_str = line[6:]
                if json_str == "[DONE]":
                    break
                    
                data = json.loads(json_str)
                
                # Handle different response types
                if data.get("type") == "content":
                    token = data.get("body", "")
                    full_text += token
                    resp = {"text": token}
                    yield resp
                    
            except json.JSONDecodeError:
                continue
        
        # Update conversation history only for saving to file if needed
        if full_text:
            self.last_response = {"text": full_text}
            self.conversation.update_chat_history(prompt, full_text)
    
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        """Send a message to the GitHub Copilot Chat API"""
        
        # Apply optimizers if specified
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")
        
        # Make sure we have a conversation ID
        try:
            conversation_id = self.create_conversation()
        except exceptions.FailedToGenerateResponseError as e:
            raise exceptions.FailedToGenerateResponseError(f"Failed to create conversation: {e}")
            
        access_token = self.get_access_token()
        
        url = f"{self.api_url}/github/chat/threads/{conversation_id}/messages"
        
        # Update headers for this specific request
        headers = self.headers.copy()
        headers["Authorization"] = f"GitHub-Bearer {access_token}"
        
        # Prepare the request payload
        request_data = {
            "content": conversation_prompt,
            "intent": "conversation",
            "references": [],
            "context": [],
            "currentURL": f"https://github.com/copilot/c/{conversation_id}",
            "streaming": True,
            "confirmations": [],
            "customInstructions": [],
            "model": self.model,
            "mode": "immersive"
        }
        
        def for_stream():
            try:
                response = self.session.post(
                    url, 
                    json=request_data,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout
                )
                
                if response.status_code == 401:
                    # Token might be expired, try refreshing
                    self._access_token = None
                    access_token = self.get_access_token()
                    headers["Authorization"] = f"GitHub-Bearer {access_token}"
                    response = self.session.post(
                        url,
                        json=request_data,
                        headers=headers,
                        stream=True,
                        timeout=self.timeout
                    )
                
                # If still not successful, raise exception
                if response.status_code != 200:
                    raise exceptions.FailedToGenerateResponseError(f"Request failed with status code {response.status_code}")
                
                # Process the streaming response
                yield from self.process_response(response, prompt)
                
            except Exception as e:
                if isinstance(e, requests.exceptions.RequestException):
                    if hasattr(e, 'response') and e.response is not None:
                        status_code = e.response.status_code 
                        if status_code == 401:
                            raise exceptions.AuthenticationError("Authentication failed. Please check your cookies.")
                
                # If anything else fails
                raise exceptions.FailedToGenerateResponseError(f"Request failed: {str(e)}")

        def for_non_stream():
            response_text = ""
            for response in for_stream():
                if "text" in response:
                    response_text += response["text"]
            self.last_response = {"text": response_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[str, Generator]:
        """Generate a response to a prompt"""
        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)
                
        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, False, optimizer=optimizer, conversationally=conversationally
                )
            )
            
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Extract message text from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")

if __name__ == "__main__":
    # Simple test code
    from rich import print
    
    try:
        ai = GithubChat()
        response = ai.chat("Python code to count r in strawberry", stream=True)
        for chunk in response:
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"An error occurred: {e}")
