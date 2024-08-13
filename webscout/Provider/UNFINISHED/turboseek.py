import requests
import json

# Define the URL
url = "https://www.turboseek.io/api/getAnswer"

# Define the headers
headers = {
    "authority": "www.turboseek.io",
    "method": "POST",
    "path": "/api/getAnswer",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-length": "63",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.turboseek.io",
    "priority": "u=1, i",
    "referer": "https://www.turboseek.io/?ref=taaft&utm_source=taaft&utm_medium=referral",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
}

# Define the payload
payload = {
    "question": input(">>> "),
    "sources": []
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

full_text = ""
for line in response.text.split('\n'):
    if line.startswith("data: "):
        try:
            data = json.loads(line[6:])
            if "text" in data:
                full_text += data["text"]
        except json.JSONDecodeError:
            pass
for c in full_text:
    print(c, end="", flush=True)
