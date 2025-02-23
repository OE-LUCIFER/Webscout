
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
from webscout.Litlogger import Logger, LogFormat

class PiAI(Provider):
    """
    PiAI is a provider class for interacting with the Pi.ai chat API.

    Attributes:
        knowledge_cutoff (str): The knowledge cutoff date for the model
        AVAILABLE_VOICES (Dict[str, int]): Available voice options for audio responses
    """

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        logging: bool = False,
    ):
        """
        Initializes the PiAI provider with specified parameters.
        """
        self.scraper = cloudscraper.create_scraper()
        self.url = 'https://pi.ai/api/chat'
        self.AVAILABLE_VOICES: Dict[str, str] = {
            "William": 1,
            "Samantha": 2,
            "Peter": 3,
            "Amy": 4,
            "Alice": 5,
            "Harry": 6
        }
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
            '__Host-session': 'Ca5SoyAMJEaaB79jj1T69',
            '__cf_bm': 'g07oaL0jcstNfKDyZv7_YFjN0jnuBZjbMiXOWhy7V7A-1723536536-1.0.1.1-xwukd03L7oIAUqPG.OHbFNatDdHGZ28mRGsbsqfjBlpuy.b8w6UZIk8F3knMhhtNzwo4JQhBVdtYOlG0MvAw8A'
        }

        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {} if self.is_conversation else {'text': ""}
        self.conversation_id = None

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
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
        self.session.proxies = proxies

        self.logger = Logger(name="PiAI", format=LogFormat.MODERN_EMOJI) if logging else None
        
        self.knowledge_cutoff = "December 2023"
        
        if self.is_conversation:
            self.start_conversation()

        if self.logger:
            self.logger.info("PiAI instance initialized successfully")

    def start_conversation(self) -> str:
        """
        Initializes a new conversation and returns the conversation ID.
        """
        if self.logger:
            self.logger.debug("Starting new conversation")
            
        response = self.scraper.post(
            "https://pi.ai/api/chat/start",
            headers=self.headers,
            cookies=self.cookies,
            json={},
            timeout=self.timeout
        )
        
        if not response.ok:
            if self.logger:
                self.logger.error(f"Failed to start conversation. Status code: {response.status_code}")
            raise Exception(f"Failed to start conversation: {response.status_code}")
            
        data = response.json()
        self.conversation_id = data['conversations'][0]['sid']
        
        if self.logger:
            self.logger.info(f"Conversation started successfully with ID: {self.conversation_id}")
            
        return self.conversation_id

    def ask(
        self,
        prompt: str,
        voice_name: Optional[str] = None,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        output_file: str = None
    ) -> dict:
        """
        Interact with Pi.ai by sending a prompt and receiving a response.
        """
        if self.logger:
            self.logger.debug(f"Processing request - Prompt: {prompt[:50]}... Voice: {voice_name}")

        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                if self.logger:
                    self.logger.error(f"Invalid optimizer requested: {optimizer}")
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        data = {
            'text': conversation_prompt,
            'conversation': self.conversation_id
        }

        def for_stream():
            response = self.scraper.post(
                self.url, 
                headers=self.headers, 
                cookies=self.cookies, 
                json=data, 
                stream=True, 
                timeout=self.timeout
            )
            
            if not response.ok:
                if self.logger:
                    self.logger.error(f"API request failed. Status code: {response.status_code}")
                raise Exception(f"API request failed: {response.status_code}")

            output_str = response.content.decode('utf-8')
            sids = re.findall(r'"sid":"(.*?)"', output_str)
            second_sid = sids[1] if len(sids) >= 2 else None

            if voice_name and second_sid:
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
                        if self.logger:
                            self.logger.warning("Failed to parse JSON from stream")
                        continue

            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        voice_name: Optional[str] = None,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        output_file: str = "PiAi.mp3"
    ) -> str:
        """
        Generates a response based on the provided prompt.
        """
        if self.logger:
            self.logger.debug(f"Chat request initiated - Prompt: {prompt[:50]}...")

        if voice_name and voice_name not in self.AVAILABLE_VOICES:
            if self.logger:
                self.logger.error(f"Invalid voice requested: {voice_name}")
            raise ValueError(f"Voice '{voice_name}' not one of [{', '.join(self.AVAILABLE_VOICES.keys())}]")

        def for_stream():
            for response in self.ask(
                prompt, 
                voice_name, 
                True, 
                optimizer=optimizer, 
                conversationally=conversationally,
                output_file=output_file
            ):
                yield self.get_message(response).encode('utf-8').decode('utf-8')

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    voice_name,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                    output_file=output_file
                )
            ).encode('utf-8').decode('utf-8')

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response"""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response["text"]

    def download_audio_threaded(self, voice_name: str, second_sid: str, output_file: str) -> None:
        """Downloads audio in a separate thread."""
        if self.logger:
            self.logger.debug(f"Starting audio download - Voice: {voice_name}, SID: {second_sid}")

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
                if self.logger:
                    self.logger.error(f"Audio download failed. Status code: {audio_response.status_code}")
                return
                
            audio_response.raise_for_status()
            
            with open(output_file, "wb") as file:
                file.write(audio_response.content)
                
            if self.logger:
                self.logger.info(f"Audio file successfully downloaded to: {output_file}")
                
        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"Audio download failed: {str(e)}")

if __name__ == '__main__':
    from rich import print
    ai = PiAI(logging=True)
    response = ai.chat(input(">>> "), stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
