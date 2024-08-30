import requests
import json
import textwrap

# Define the URL
url = "https://www.elmo.chat/api/v1/prompt"

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-length": "763",
    "content-type": "text/plain;charset=UTF-8",
    "dnt": "1",
    "origin": "chrome-extension://ipnlcfhfdicbfbchfoihipknbaeenenm",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
}

# Define the JSON payload
payload = {
    "metadata": {
        "system": {
            "language": "en-US"
        },
        "website": {
            "url": "chrome-extension://ipnlcfhfdicbfbchfoihipknbaeenenm/options.html",
            "origin": "chrome-extension://ipnlcfhfdicbfbchfoihipknbaeenenm",
            "title": "Elmo Chat - Your AI Web Copilot",
            "xpathIndexLength": 0,
            "favicons": [],
            "language": "en",
            "content": "",
            "type": "html",
            "selection": "",
            "hash": "d41d8cd98f00b204e9800998ecf8427e"
        }
    },
    "regenerate": True,
    "conversation": [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Provide clear, concise, and well-structured information. Organize your responses into paragraphs for better readability."
        },
        {
            "role": "user",
            "content": input(">>> ") #/insight  HelpingAI-9B
        }
    ],
    "enableCache": False
}

# Make the POST request with stream=True
response = requests.post(url, headers=headers, json=payload, stream=True)

# Print the response status code
print(f"Status Code: {response.status_code}")

# Process the streaming response
if response.status_code == 200:
    full_response = ""
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('0:'):
                chunk = decoded_line.split(':"')[1].strip('"')
                formatted_output = chunk.replace('\\n', '\n').replace('\\n\\n', '\n\n')
                for line in formatted_output:
                    print(line, end="", flush=True)
