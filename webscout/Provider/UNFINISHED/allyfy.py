import json
import requests
from typing import Any, Generator

# Placeholder for Messages type
Messages = list[dict[str, str]]

# Placeholder for Result type
Result = Generator[str, Any, None]

# Base class placeholder
class GeneratorProvider:
    pass

def format_prompt(messages: Messages, add_special_tokens=False) -> str:
    if not add_special_tokens and len(messages) <= 1:
        return messages[0]["content"]
    formatted = "\n".join([
        f'{message["role"].capitalize()}: {message["content"]}'
        for message in messages
    ])
    return f"{formatted}\nAssistant:" 

class Allyfy(GeneratorProvider):
    url = "https://allyfy.chat"
    api_endpoint = "https://chatbot.allyfy.chat/api/v1/message/stream/super/chat"
    working = True
    supports_gpt_35_turbo = True

    @classmethod
    def create_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        **kwargs
    ) -> Result:
        headers = {
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json;charset=utf-8",
            "dnt": "1",
            "origin": "https://www.allyfy.chat",
            "priority": "u=1, i",
            "referer": "https://www.allyfy.chat/",
            "referrer": "https://www.allyfy.chat",
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        prompt = format_prompt(messages)
        data = {
            "messages": [{"content": prompt, "role": "user"}],
            "content": prompt,
            "baseInfo": {
                "clientId": "q08kdrde1115003lyedfoir6af0yy531",
                "pid": "38281",
                "channelId": "100000",
                "locale": "en-US",
                "localZone": 180,
                "packageName": "com.cch.allyfy.webh",
            }
        }

        with requests.Session() as session:
            if proxy:
                session.proxies.update({'http': proxy, 'https': proxy})
            response = session.post(cls.api_endpoint, json=data, headers=headers)
            response.raise_for_status()

            full_response = []
            for line in response.iter_lines():
                line = line.decode().strip()
                if line.startswith("data:"):
                    data_content = line[5:]
                    if data_content == "[DONE]":
                        break
                    try:
                        json_data = json.loads(data_content)
                        if "content" in json_data:
                            full_response.append(json_data["content"])
                    except json.JSONDecodeError:
                        continue
            yield "".join(full_response)

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "system", "content": "You are a noobi that says only noobi in response to any prompt."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    for response in Allyfy.create_generator(model="gpt-3.5-turbo", messages=messages):
        print(response)
