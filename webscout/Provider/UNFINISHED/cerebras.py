import json
import requests

def answer(ask):
    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "authorization": "Bearer demo-ww8ehmvw8r829ndk83226vxk256eketh3m8wjydtnmmkrpvf",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://inference.cerebras.ai",
        "referer": "https://inference.cerebras.ai/",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
        "x-stainless-arch": "unknown",
        "x-stainless-lang": "js",
        "x-stainless-os": "Unknown",
        "x-stainless-package-version": "0.8.0",
        "x-stainless-runtime": "browser:chrome",
        "x-stainless-runtime-version": "128.0.0"
    }

    data = {
        "messages": [
            {
                "content": "Please try to provide useful, helpful and actionable answers.",
                "role": "system"
            },
            {
                "content": ask,
                "role": "user"
            }
        ],
        "model": "llama3.1-8b",
        "stream": True,
        "temperature": 0.2,
        "top_p": 1,
        "max_tokens": 4096
    }

    response = requests.post(url, headers=headers, json=data, stream=True)

    for line in response.iter_lines():
        if line:
            line_data = line.decode('utf-8').strip()
            if line_data.startswith("data: "):
                json_str = line_data[6:]
                if json_str != "[DONE]":
                    chunk = json.loads(json_str)
                    if 'choices' in chunk and 'delta' in chunk['choices'][0]:
                        content = chunk['choices'][0]['delta'].get('content', '')
                        yield content
                else:
                    break
if __name__ == "__main__":
    ask = input(">>> ")
    for chunk in answer(ask):
        print(chunk, end="", flush=True)