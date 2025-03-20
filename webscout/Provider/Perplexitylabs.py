import ssl
import json
import time
import socket
import random
from threading import Thread, Event
from curl_cffi import requests
from websocket import WebSocketApp
from typing import Dict, Any, Union, Generator, List, Optional

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent

class PerplexityLabs(Provider):
    """
    A client for interacting with the Perplexity AI Labs API.
    """
    
    AVAILABLE_MODELS = [
        "r1-1776", 
        "sonar-pro", 
        "sonar", 
        "sonar-reasoning-pro", 
        "sonar-reasoning"
    ]
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 60,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "r1-1776",
        connection_timeout: float = 10.0,
        max_retries: int = 3,
    ):
        """
        Initialize the Perplexity client.
        
        Args:
            is_conversation: Whether to maintain conversation context
            max_tokens: Maximum token limit for responses
            timeout: Response timeout in seconds
            intro: Conversation intro/system prompt
            filepath: Path for conversation history persistence
            update_file: Whether to update the conversation file
            proxies: Optional proxy configuration
            history_offset: History truncation limit
            act: Persona to use for responses
            model: Default model to use
            connection_timeout: Maximum time to wait for connection
            max_retries: Number of connection retry attempts
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model}. Choose from: {self.AVAILABLE_MODELS}")
            
        self.model = model
        self.connection_timeout = connection_timeout
        self.timeout = timeout 
        self.max_retries = max_retries
        self.connected = Event()
        self.last_answer = None
        
        # Initialize session with headers using LitAgent user agent
        self.session = requests.Session(headers={
            'User-Agent': LitAgent().random(),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'dnt': '1',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not;A=Brand";v="24", "Chromium";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        })
        
        # Apply proxies if provided
        self.session.proxies.update(proxies)
        
        # Set up conversation handling
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens

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
            
        # Initialize connection
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize the connection to Perplexity with retries"""
        for attempt in range(1, self.max_retries + 1):
            try:
                # Get a session ID via polling
                self.timestamp = format(random.getrandbits(32), '08x')
                poll_url = f'https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}'
                
                response = self.session.get(poll_url)
                if response.status_code != 200:
                    if attempt == self.max_retries:
                        raise ConnectionError(f"Failed to get session ID: HTTP {response.status_code}")
                    continue
                
                # Extract the session ID
                try:
                    self.sid = json.loads(response.text[1:])['sid']
                except (json.JSONDecodeError, KeyError) as e:
                    if attempt == self.max_retries:
                        raise ConnectionError(f"Failed to parse session ID: {e}")
                    continue
                
                # Authenticate the session
                auth_url = f'https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.timestamp}&sid={self.sid}'
                auth_response = self.session.post(auth_url, data='40{"jwt":"anonymous-ask-user"}')
                
                if auth_response.status_code != 200 or auth_response.text != 'OK':
                    if attempt == self.max_retries:
                        raise ConnectionError("Authentication failed")
                    continue
                
                # Setup SSL socket
                context = ssl.create_default_context()
                context.minimum_version = ssl.TLSVersion.TLSv1_3
                try:
                    self.sock = context.wrap_socket(
                        socket.create_connection(('www.perplexity.ai', 443), timeout=self.connection_timeout), 
                        server_hostname='www.perplexity.ai'
                    )
                except (socket.timeout, socket.error, ssl.SSLError) as e:
                    if attempt == self.max_retries:
                        raise ConnectionError(f"Socket connection failed: {e}")
                    continue
                
                # Setup WebSocket
                ws_url = f'wss://www.perplexity.ai/socket.io/?EIO=4&transport=websocket&sid={self.sid}'
                cookies = '; '.join([f'{key}={value}' for key, value in self.session.cookies.get_dict().items()])
                
                self.connected.clear()
                self.ws = WebSocketApp(
                    url=ws_url,
                    header={'User-Agent': self.session.headers['User-Agent']},
                    cookie=cookies,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    socket=self.sock
                )
                
                # Start WebSocket in a thread
                self.ws_thread = Thread(target=self.ws.run_forever, daemon=True)
                self.ws_thread.start()
                
                # Wait for connection to be established
                if self.connected.wait(timeout=self.connection_timeout):
                    return
                
            except Exception as e:
                if attempt == self.max_retries:
                    raise exceptions.FailedToGenerateResponseError(f"Failed to connect: {e}")
            
            # If we get here, the attempt failed, wait before retrying
            if attempt < self.max_retries:
                retry_delay = 2 ** attempt  # Exponential backoff
                time.sleep(retry_delay)
        
        raise exceptions.FailedToGenerateResponseError("Failed to connect to Perplexity after multiple attempts")

    def _on_open(self, ws):
        """Handle websocket open event"""
        ws.send('2probe')
        ws.send('5')
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle websocket close event"""
        self.connected.clear()
    
    def _on_message(self, ws, message):
        """Handle websocket message events"""
        if message == '2':
            ws.send('3')
            
        elif message == '3probe':
            self.connected.set()

        elif message.startswith('40'):
            self.connected.set()
            
        elif message.startswith('42'):
            try:
                response = json.loads(message[2:])[1]
                if 'final' in response or 'partial' in response:
                    self.last_answer = response
            except (json.JSONDecodeError, IndexError):
                pass
    
    def _on_error(self, ws, error):
        """Handle websocket error events"""
        self.connected.clear()
    
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        model: str = None
    ) -> Union[Dict[str, Any], Generator]:
        """
        Send a query to Perplexity AI and get a response.
        
        Args:
            prompt: The question to ask
            stream: Whether to stream the response
            raw: Return raw response format
            optimizer: Optimizer function to apply to prompt
            conversationally: Use conversation context
            model: Override the model to use
            
        Returns:
            If stream=True: Generator yielding response updates
            If stream=False: Final response dictionary
        """
        # Check if connection is still active and reconnect if needed
        if not self.connected.is_set():
            self._initialize_connection()
        
        # Use specified model or default
        use_model = model or self.model
        if use_model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {use_model}. Choose from: {', '.join(self.AVAILABLE_MODELS)}")
        
        # Process prompt with conversation and optimizers
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")
        
        self.last_answer = None
        
        # Send the query through websocket
        payload = json.dumps([
            'perplexity_labs',
            {
                'messages': [{'role': 'user', 'content': conversation_prompt}],
                'model': use_model,
                'source': 'default',
                'version': '2.18',
            }
        ])
        self.ws.send('42' + payload)
        
        def for_stream():
            """Handle streaming responses"""
            last_seen = None
            start_time = time.time()
            streaming_text = ""
            
            while True:
                # Check for timeout
                if time.time() - start_time > self.timeout:
                    raise exceptions.FailedToGenerateResponseError("Response stream timed out")
                
                # If we have a new response different from what we've seen
                if self.last_answer != last_seen:
                    last_seen = self.last_answer
                    if last_seen is not None:
                        if 'output' in last_seen:
                            current_output = last_seen['output']
                            # For delta output in streaming
                            delta = current_output[len(streaming_text):]
                            streaming_text = current_output
                            resp = dict(text=delta)
                            yield resp if raw else resp
                
                # If we have the final response, add to history and return
                if self.last_answer and self.last_answer.get('final', False):
                    answer = self.last_answer
                    self.conversation.update_chat_history(prompt, streaming_text)
                    return
                
                time.sleep(0.01)
        
        def for_non_stream():
            """Handle non-streaming responses"""
            start_time = time.time()
            
            while True:
                # Check for successful response
                if self.last_answer and self.last_answer.get('final', False):
                    answer = self.last_answer
                    self.conversation.update_chat_history(prompt, answer['output'])
                    return answer if raw else dict(text=answer['output'])
                
                # Check for timeout
                if time.time() - start_time > self.timeout:
                    raise exceptions.FailedToGenerateResponseError("Response timed out")
                
                time.sleep(0.01)
        
        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        model: str = None
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send a query and get just the text response.
        
        Args:
            prompt: The question to ask
            stream: Whether to stream the response
            optimizer: Optimizer function to apply to prompt
            conversationally: Use conversation context
            model: Override the model to use
            
        Returns:
            If stream=True: Generator yielding text chunks
            If stream=False: Complete response text
        """
        def for_stream():
            for response in self.ask(
                prompt, 
                stream=True, 
                optimizer=optimizer, 
                conversationally=conversationally,
                model=model
            ):
                yield self.get_message(response)
                
        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, 
                    stream=False, 
                    optimizer=optimizer, 
                    conversationally=conversationally,
                    model=model
                )
            )
            
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Extract text from response dictionary"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]


if __name__ == "__main__":
    print("-" * 80)
    print(f"{'Model':<50} {'Status':<10} {'Response'}")
    print("-" * 80)
    
    # Test all available models
    working = 0
    total = len(PerplexityLabs.AVAILABLE_MODELS)
    
    for model in PerplexityLabs.AVAILABLE_MODELS:
        try:
            test_ai = PerplexityLabs(model=model, timeout=60)
            response = test_ai.chat("Say 'Hello' in one word", stream=True)
            response_text = ""
            for chunk in response:
                response_text += chunk
                print(f"\r{model:<50} {'Testing...':<10}", end="", flush=True)
            
            if response_text and len(response_text.strip()) > 0:
                status = "✓"
                # Truncate response if too long
                display_text = response_text.strip()[:50] + "..." if len(response_text.strip()) > 50 else response_text.strip()
            else:
                status = "✗"
                display_text = "Empty or invalid response"
            print(f"\r{model:<50} {status:<10} {display_text}")
        except Exception as e:
            print(f"\r{model:<50} {'✗':<10} {str(e)}")
