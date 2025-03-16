from uuid import uuid4
import cloudscraper
import json
import re
import threading
import requests
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts
from webscout.AIbase import Provider
from typing import Dict, Union, Any, Optional
from webscout import LitAgent

class PiAI(Provider):
    """
    PiAI is a provider class for interacting with the Pi.ai chat API.

    Attributes:
        knowledge_cutoff (str): The knowledge cutoff date for the model
        AVAILABLE_VOICES (Dict[str, int]): Available voice options for audio responses
        AVAILABLE_MODELS (List[str]): Available model options for the API
    """
    AVAILABLE_MODELS = ["inflection_3_pi"]
    AVAILABLE_VOICES: Dict[str, int] = {
        "voice1": 1,
        "voice2": 2,
        "voice3": 3,
        "voice4": 4,
        "voice5": 5,
        "voice6": 6,
        "voice7": 7,
        "voice8": 8
    }

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 2048,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        voice: bool = False,
        voice_name: str = "voice3",
        output_file: str = "PiAI.mp3",
        model: str = "inflection_3_pi",
    ):
        """
        Initializes PiAI with voice support.
        
        Args:
            voice (bool): Enable/disable voice output
            voice_name (str): Name of the voice to use (if None, uses default)
            output_file (str): Path to save voice output (default: PiAI.mp3)
        """
        # Voice settings
        self.voice_enabled = voice
        self.voice_name = voice_name
        self.output_file = output_file

        if voice and voice_name and voice_name not in self.AVAILABLE_VOICES:
            raise ValueError(f"Voice '{voice_name}' not available. Choose from: {list(self.AVAILABLE_VOICES.keys())}")

        # Initialize other attributes
        self.scraper = cloudscraper.create_scraper()
        self.url = 'https://pi.ai/api/chat'
        self.headers = {
            'Accept': 'text/event-stream',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Content-Type': 'application/json',
            'DNT': '1',
            'Origin': 'https://pi.ai',
            'Referer': 'https://pi.ai/talk',
            'Sec-CH-UA': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': LitAgent().random(),
            'X-Api-Version': '3'
        }
        self.cookies = {
            '__cf_bm': uuid4().hex
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {} if self.is_conversation else {'text': ""}
        self.conversation_id = None

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )

        # Setup conversation
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            ) if act else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies
        
        if self.is_conversation:
            self.start_conversation()

    def start_conversation(self) -> str:
        """
        Initializes a new conversation and returns the conversation ID.
        """
        response = self.scraper.post(
            "https://pi.ai/api/chat/start",
            headers=self.headers,
            cookies=self.cookies,
            json={},
            timeout=self.timeout
        )
        
        if not response.ok:
            raise Exception(f"Failed to start conversation: {response.status_code}")
            
        data = response.json()
        self.conversation_id = data['conversations'][0]['sid']
        
        return self.conversation_id

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        voice: bool = None,
        voice_name: str = None,
        output_file: str = None
    ) -> dict:
        """
        Interact with Pi.ai by sending a prompt and receiving a response.
        
        Args:
            prompt (str): The prompt to send
            stream (bool): Whether to stream the response
            raw (bool): Return raw response format
            optimizer (str): Prompt optimizer to use
            conversationally (bool): Use conversation context
            voice (bool): Override default voice setting
            voice_name (str): Override default voice name
            output_file (str): Override default output file path
        """
        # Voice configuration
        voice = self.voice_enabled if voice is None else voice
        voice_name = self.voice_name if voice_name is None else voice_name
        output_file = self.output_file if output_file is None else output_file

        if voice and voice_name and voice_name not in self.AVAILABLE_VOICES:
            raise ValueError(f"Voice '{voice_name}' not available. Choose from: {list(self.AVAILABLE_VOICES.keys())}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        data = {
            'text': conversation_prompt,
            'conversation': self.conversation_id
        }

        def process_stream():
            response = self.scraper.post(
                self.url, 
                headers=self.headers, 
                cookies=self.cookies, 
                json=data, 
                stream=True, 
                timeout=self.timeout
            )
            
            if not response.ok:
                raise Exception(f"API request failed: {response.status_code}")

            output_str = response.content.decode('utf-8')
            sids = re.findall(r'"sid":"(.*?)"', output_str)
            second_sid = sids[1] if len(sids) >= 2 else None

            if voice and voice_name and second_sid:
                threading.Thread(
                    target=self.download_audio_threaded, 
                    args=(voice_name, second_sid, output_file)
                ).start()

            streaming_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        parsed_data = json.loads(line[6:])
                        if 'text' in parsed_data:
                            streaming_text += parsed_data['text']
                            resp = dict(text=streaming_text)
                            self.last_response.update(resp)
                            yield parsed_data if raw else resp
                    except json.JSONDecodeError:
                        continue

            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        if stream:
            return process_stream()
        else:
            # For non-stream, collect all responses and return the final one
            for res in process_stream():
                pass
            return self.last_response

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        voice: bool = None,
        voice_name: str = None,
        output_file: str = None
    ) -> str:
        """
        Generates a response based on the provided prompt.
        
        Args:
            prompt (str): The prompt to send
            stream (bool): Whether to stream the response
            optimizer (str): Prompt optimizer to use
            conversationally (bool): Use conversation context
            voice (bool): Override default voice setting
            voice_name (str): Override default voice name
            output_file (str): Override default output file path
        """
        # Use instance defaults if not specified
        voice = self.voice_enabled if voice is None else voice
        voice_name = self.voice_name if voice_name is None else voice_name
        output_file = self.output_file if output_file is None else output_file

        if voice and voice_name and voice_name not in self.AVAILABLE_VOICES:
            raise ValueError(f"Voice '{voice_name}' not available. Choose from: {list(self.AVAILABLE_VOICES.keys())}")

        if stream:
            def stream_generator():
                for response in self.ask(
                    prompt,
                    stream=True,
                    optimizer=optimizer,
                    conversationally=conversationally,
                    voice=voice,
                    voice_name=voice_name,
                    output_file=output_file
                ):
                    yield self.get_message(response).encode('utf-8').decode('utf-8')
            return stream_generator()
        else:
            response = self.ask(
                prompt,
                stream=False,
                optimizer=optimizer,
                conversationally=conversationally,
                voice=voice,
                voice_name=voice_name,
                output_file=output_file
            )
            return self.get_message(response)

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

    def download_audio_threaded(self, voice_name: str, second_sid: str, output_file: str) -> None:
        """Downloads audio in a separate thread."""
        params = {
            'mode': 'eager',
            'voice': f'voice{self.AVAILABLE_VOICES[voice_name]}',
            'messageSid': second_sid,
        }
        
        try:
            audio_response = self.scraper.get(
                'https://pi.ai/api/chat/voice', 
                params=params, 
                cookies=self.cookies, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            if not audio_response.ok:
                return
                
            audio_response.raise_for_status()
            
            with open(output_file, "wb") as file:
                file.write(audio_response.content)
                
        except requests.exceptions.RequestException:
            pass

if __name__ == '__main__':
    from rich import print
    ai = PiAI()
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
