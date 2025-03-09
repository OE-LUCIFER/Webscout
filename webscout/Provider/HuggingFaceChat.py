import requests
import uuid
import json
import time
import random
import re
from typing import Any, Dict, List, Optional, Union, Generator

from webscout.AIutel import Conversation
from webscout.AIbase import Provider
from webscout import exceptions
from webscout import LitAgent

class HuggingFaceChat(Provider):
    """
    A class to interact with the Hugging Face Chat API.
    Uses cookies for authentication and supports streaming responses.
    """
    
    # Available models (default models - will be updated dynamically)
    AVAILABLE_MODELS = [
        'meta-llama/Llama-3.3-70B-Instruct',
        'Qwen/Qwen2.5-72B-Instruct',
        'CohereForAI/c4ai-command-r-plus-08-2024',
        'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B',
        'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
        'Qwen/QwQ-32B',
        'Qwen/Qwen2.5-Coder-32B-Instruct',
        'meta-llama/Llama-3.2-11B-Vision-Instruct',
        'NousResearch/Hermes-3-Llama-3.1-8B',
        'mistralai/Mistral-Nemo-Instruct-2407',
        'microsoft/Phi-3.5-mini-instruct',
        'meta-llama/Llama-3.1-8B-Instruct'

    ]
    
    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2000,
        timeout: int = 60,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        model: str = "Qwen/QwQ-32B",
        cookie_path: str = "cookies.json"
    ):
        """Initialize the HuggingFaceChat client."""
        self.url = "https://huggingface.co/chat"
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
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://huggingface.co",
            "Referer": "https://huggingface.co/chat",
            "Sec-Ch-Ua": "\"Chromium\";v=\"120\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "DNT": "1",
            "Priority": "u=1, i"
        }
        
        # Apply cookies to session
        if self.cookies:
            self.session.cookies.update(self.cookies)
        
        # Update available models
        self.update_available_models()
        
        # Set default model if none provided
        self.model = model
        
        # Provider settings
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}

        # Initialize a simplified conversation history for file saving only
        self.conversation = Conversation(is_conversation, max_tokens, filepath, update_file)
        
        # Store conversation data for different models
        self._conversation_data = {}

    def update_available_models(self):
        """Update the available models list from HuggingFace"""
        try:
            models = self.get_models()
            if models and len(models) > 0:
                self.AVAILABLE_MODELS = models
        except Exception:
            # Fallback to default models list if fetching fails
            pass
    
    @classmethod
    def get_models(cls):
        """Fetch available models from HuggingFace."""
        try:
            response = requests.get("https://huggingface.co/chat")
            text = response.text
            models_match = re.search(r'models:(\[.+?\]),oldModels:', text)
            
            if not models_match:
                return cls.AVAILABLE_MODELS
                
            models_text = models_match.group(1)
            models_text = re.sub(r',parameters:{[^}]+?}', '', models_text)
            models_text = models_text.replace('void 0', 'null')
            
            def add_quotation_mark(match):
                return f'{match.group(1)}"{match.group(2)}":'
                
            models_text = re.sub(r'([{,])([A-Za-z0-9_]+?):', add_quotation_mark, models_text)
            
            models_data = json.loads(models_text)
            # print([model["id"] for model in models_data])
            return [model["id"] for model in models_data]
        except Exception:
            return cls.AVAILABLE_MODELS

    def load_cookies(self):
        """Load cookies from a JSON file"""
        try:
            with open(self.cookie_path, 'r') as f:
                cookies_data = json.load(f)
                
            # Convert the cookie list to a dictionary format for requests
            cookies = {}
            for cookie in cookies_data:
                # Only include cookies that are not expired and have a name and value
                if 'name' in cookie and 'value' in cookie:
                    # Check if the cookie hasn't expired
                    if 'expirationDate' not in cookie or cookie['expirationDate'] > time.time():
                        cookies[cookie['name']] = cookie['value']
            
            return cookies
        except Exception:
            return {}

    def create_conversation(self, model: str):
        """Create a new conversation with the specified model."""
        url = "https://huggingface.co/chat/conversation"
        payload = {"model": model}
        
        # Update referer for this specific request
        headers = self.headers.copy()
        headers["Referer"] = f"https://huggingface.co/chat/models/{model}"
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            
            if response.status_code == 401:
                raise exceptions.AuthenticationError("Authentication failed. Please check your cookies.")
            
            # Handle other error codes
            if response.status_code != 200:
                return None
                
            data = response.json()
            conversation_id = data.get("conversationId")
            
            # Store conversation data
            if model not in self._conversation_data:
                self._conversation_data[model] = {
                    "conversationId": conversation_id,
                    "messageId": str(uuid.uuid4())  # Initial message ID
                }
            
            # Update cookies if needed
            if 'hf-chat' in response.cookies:
                self.cookies["hf-chat"] = response.cookies['hf-chat']
                
            return conversation_id
        except requests.exceptions.RequestException:
            return None
    
    def fetch_message_id(self, conversation_id: str) -> str:
        """Fetch the latest message ID for a conversation."""
        try:
            url = f"https://huggingface.co/chat/conversation/{conversation_id}/__data.json?x-sveltekit-invalidated=11"
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the JSON data from the response
            json_data = None
            for line in response.text.split('\n'):
                if line.strip():
                    try:
                        parsed = json.loads(line)
                        if isinstance(parsed, dict) and "nodes" in parsed:
                            json_data = parsed
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not json_data:
                # Fall back to a UUID if we can't parse the response
                return str(uuid.uuid4())
            
            # Extract message ID using the same pattern as in the example
            if json_data.get("nodes", []) and json_data["nodes"][-1].get("type") == "error":
                return str(uuid.uuid4())
                
            data = json_data["nodes"][1]["data"]
            keys = data[data[0]["messages"]]
            message_keys = data[keys[-1]]
            message_id = data[message_keys["id"]]
            
            return message_id
            
        except Exception:
            # Fall back to a UUID if there's an error
            return str(uuid.uuid4())
    
    def generate_boundary(self):
        """Generate a random boundary for multipart/form-data requests"""
        boundary_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        boundary = "----WebKitFormBoundary"
        boundary += "".join(random.choice(boundary_chars) for _ in range(16))
        return boundary
    
    def process_response(self, response, prompt: str):
        """Process streaming response and extract content."""
        full_text = ""
        sources = None
        reasoning_text = ""
        has_reasoning = False
        
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
                
            try:
                # Parse each line as JSON
                data = json.loads(line)
                
                # Handle different response types
                if "type" not in data:
                    continue
                    
                if data["type"] == "stream" and "token" in data:
                    token = data["token"].replace("\u0000", "")
                    full_text += token
                    resp = {"text": token}
                    yield resp
                elif data["type"] == "finalAnswer":
                    final_text = data.get("text", "")
                    if final_text and not full_text:
                        full_text = final_text
                        resp = {"text": final_text}
                        yield resp
                elif data["type"] == "webSearch" and "sources" in data:
                    sources = data["sources"]
                elif data["type"] == "reasoning":
                    has_reasoning = True
                    if data.get("subtype") == "stream" and "token" in data:
                        reasoning_text += data["token"]
                    # elif data.get("subtype") == "status":
                    #     # For status updates in reasoning, we can just append them as a comment
                    #     if data.get("status"):
                    #         reasoning_text += f"\n# {data['status']}"
                    
                    # If we have reasoning, prepend it to the next text output
                    if reasoning_text and not full_text:
                        resp = {"text": f"<think>\n{reasoning_text}\n</think>\n", "is_reasoning": True}
                        yield resp
                    
            except json.JSONDecodeError:
                continue
        
        # Update conversation history only for saving to file if needed
        if full_text and self.conversation.file:
            if has_reasoning:
                full_text_with_reasoning = f"<think>\n{reasoning_text}\n</think>\n{full_text}"
                self.last_response = {"text": full_text_with_reasoning}
                self.conversation.update_chat_history(prompt, full_text_with_reasoning)
            else:
                self.last_response = {"text": full_text}
                self.conversation.update_chat_history(prompt, full_text)
        
        return full_text
    
    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        web_search: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        """Send a message to the HuggingFace Chat API"""
        model = self.model
        
        # Check if we have a conversation for this model
        if model not in self._conversation_data:
            conversation_id = self.create_conversation(model)
            if not conversation_id:
                raise exceptions.FailedToGenerateResponseError(f"Failed to create conversation with model {model}")
        else:
            conversation_id = self._conversation_data[model]["conversationId"]
            # Refresh message ID
            self._conversation_data[model]["messageId"] = self.fetch_message_id(conversation_id)
        
        url = f"https://huggingface.co/chat/conversation/{conversation_id}"
        message_id = self._conversation_data[model]["messageId"]
        
        # Data to send - use the prompt directly without generating a complete prompt
        # since HuggingFace maintains conversation state internally
        request_data = {
            "inputs": prompt,
            "id": message_id,
            "is_retry": False,
            "is_continue": False,
            "web_search": web_search,
            "tools": ["66e85bb396d054c5771bc6cb", "00000000000000000000000a"]
        }
        
        # Update headers for this specific request
        headers = self.headers.copy()
        headers["Referer"] = f"https://huggingface.co/chat/conversation/{conversation_id}"
        
        # Create multipart form data
        boundary = self.generate_boundary()
        multipart_headers = headers.copy()
        multipart_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        
        # Serialize the data to JSON
        data_json = json.dumps(request_data, separators=(',', ':'))
        
        # Create the multipart form data body
        body = f"--{boundary}\r\n"
        body += f'Content-Disposition: form-data; name="data"\r\n'
        body += f"Content-Type: application/json\r\n\r\n"
        body += f"{data_json}\r\n"
        body += f"--{boundary}--\r\n"
        
        multipart_headers["Content-Length"] = str(len(body))
        
        def for_stream():
            try:
                # Try with multipart/form-data first
                response = None
                try:
                    response = self.session.post(
                        url, 
                        data=body,
                        headers=multipart_headers,
                        stream=True,
                        timeout=self.timeout
                    )
                except requests.exceptions.RequestException:
                    pass
                
                # If multipart fails or returns error, try with regular JSON
                if not response or response.status_code != 200:
                    response = self.session.post(
                        url, 
                        json=request_data,
                        headers=headers,
                        stream=True,
                        timeout=self.timeout
                    )
                
                # If both methods fail, raise exception
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
                
                # Try another model if current one fails
                if len(self.AVAILABLE_MODELS) > 1:
                    current_model_index = self.AVAILABLE_MODELS.index(self.model) if self.model in self.AVAILABLE_MODELS else 0
                    next_model_index = (current_model_index + 1) % len(self.AVAILABLE_MODELS)
                    self.model = self.AVAILABLE_MODELS[next_model_index]
                    
                    # Create new conversation with the alternate model
                    conversation_id = self.create_conversation(self.model)
                    if conversation_id:
                        # Try again with the new model
                        yield from self.ask(prompt, stream=True, raw=raw, optimizer=optimizer, 
                                          conversationally=conversationally, web_search=web_search)
                        return
                
                # If we get here, all models failed
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
        web_search: bool = False
    ) -> Union[str, Generator]:
        """Generate a response to a prompt"""
        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally, web_search=web_search
            ):
                yield self.get_message(response)
                
        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt, False, optimizer=optimizer, conversationally=conversationally, web_search=web_search
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
        ai = HuggingFaceChat()
        response = ai.chat("how many r in strawberry", stream=True, web_search=False)
        for chunk in response:
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"An error occurred: {e}")