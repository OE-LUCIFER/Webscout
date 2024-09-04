import requests
import json
import uuid

url = 'https://sanatanadharma.xyz/api/chat'

headers = {
    'authority': 'sanatanadharma.xyz',
    'method': 'POST',
    'path': '/api/chat',
    'scheme': 'https',
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
    'content-length': '493',
    'content-type': 'application/json',
    'cookie': '_ga=GA1.1.1210057933.1725258600; _gcl_au=1.1.734850924.1725258600; _ga_916S3MSTVF=GS1.1.1725419829.3.0.1725419829.0.0.0',
    'dnt': '1',
    'origin': 'https://sanatanadharma.xyz',
    'priority': 'u=1, i',
    'referer': 'https://sanatanadharma.xyz/?ref=taaft&utm_source=taaft&utm_medium=referral',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
}

payload = {
    "messages": [
        {
            "role": "system",
            "content": "🙏 Namaste! I'm Sanatana Dharma Chatbot, your AI assistant for Bhagavad Gita, Vedas, Puranas, Yoga, and healthy living. Discover insights about karma, the Gayatri Mantra, Vedic interpretations, and more."
        },
        {
            "role": "user",
            "content": input(">>> ")
        }
    ],
    "requestId": str(uuid.uuid4())
}

response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)


for line in response.text:
    print(line, end='', flush=True)