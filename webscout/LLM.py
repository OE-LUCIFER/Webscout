import argparse
import requests
import json
from typing import List, Dict, Union

class LLM:
    def __init__(self, model: str, system_message: str = "You are a Helpful AI."):
        self.model = model
        self.conversation_history = [{"role": "system", "content": system_message}]

    def chat(self, messages: List[Dict[str, str]]) -> Union[str, None]:
        url = "https://api.deepinfra.com/v1/openai/chat/completions"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        data = json.dumps(
            {
                'model': self.model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 8028,
                'stop': [],
                'stream': False #dont change it
            }, separators=(',', ':')
        )
        try:
            result = requests.post(url=url, data=data, headers=headers)
            return result.json()['choices'][0]['message']['content']
        except:
            return None
