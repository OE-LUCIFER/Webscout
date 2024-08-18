from uuid import uuid4
import requests
import secrets
import json

# Define the URL
url = "https://chatgpt5free.com/wp-json/mwai-ui/v1/chats/submit"

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://chatgpt5free.com",
    "priority": "u=1, i",
    "referer": "https://chatgpt5free.com/chatgpt-5-free/",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "x-wp-nonce": "af6c25ac5a"
}

# Generate a random session ID
random_session_id = secrets.token_hex(16)

# Define the JSON payload
payload = {
    "botId": "default",
    "customId": None,
    "session": random_session_id,
    "chatId": uuid4().hex,
    "newMessage": input(">>> "),
    "newFileId": None,
    "stream": True
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload, stream=True)

# Process and print the response
full_response = ""
for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        if decoded_line.startswith("data: "):
            json_data = json.loads(decoded_line[6:])
            if json_data["type"] == "live":
                full_response += json_data["data"]

for line in full_response:
    print(line, end="", flush=True)