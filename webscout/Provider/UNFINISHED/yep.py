from uuid import uuid4
import cloudscraper
import json

# Create a Cloudscraper session
scraper = cloudscraper.create_scraper()

# URL of the API endpoint
url = 'https://api.yep.com/v1/chat/completions'

# Headers
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
    'Content-Type': 'application/json; charset=utf-8',
    'DNT': '1',
    'Origin': 'https://yep.com',
    'Referer': 'https://yep.com/',
    'Sec-CH-UA': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    'Sec-CH-UA-Mobile': '?0',
    'Sec-CH-UA-Platform': '"Windows"',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
}

# Initial cookies
cookies = {
    '__Host-session': uuid4().hex,
}

# Data to be sent in the POST request
data = {
    "stream": True,
    "max_tokens": 1280,
    "top_p": 0.7,
    "temperature": 0.6,
    "messages": [
        {"content": input(">>> "), "role": "user"}
    ],
    "model": "Mixtral-8x7B-Instruct-v0.1"
}

# Make the POST request
response = scraper.post(url, headers=headers, cookies=cookies, json=data)

# Check the response
if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                json_data = decoded_line[6:]
                if json_data == "[DONE]":
                    break
                try:
                    data = json.loads(json_data)
                    content = data["choices"][0]["delta"].get("content", "")
                    for c in content:
                        print(c, end="", flush=True)
                except json.decoder.JSONDecodeError:
                    pass