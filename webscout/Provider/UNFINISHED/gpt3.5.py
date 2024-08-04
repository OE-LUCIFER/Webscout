import json
import requests

# Define the URL
url = "https://api.farfalle.dev/chat"

# Define the headers
headers = {
    "accept": "text/event-stream",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.farfalle.dev",
    "priority": "u=1, i",
    "referer": "https://www.farfalle.dev/",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
}

# Define the payload
payload = {
    "query": "write me eassy on modi",
    "model": "gpt-3.5-turbo",
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload, stream=True)

if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data:"):
                data = decoded_line[len("data:"):].strip()
                if data:
                    event = json.loads(data)
                    if event.get("event") == "final-response":
                        message = event['data'].get('message', '')
                        print(message, end="", flush=True)
else:
    print(f"Request failed with status code: {response.status_code}")