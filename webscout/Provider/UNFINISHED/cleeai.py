from uuid import uuid4
import requests

# Define the URL
url = "https://qna-api.cleeai.com/open_research"

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.cleeai.com",
    "priority": "u=1, i",
    "referer": "https://www.cleeai.com/",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
}

# Define the JSON payload
payload = {
    "data": {
        "question": "who is Abhay koul(HelpingAI)",
        "question_id": 69237,
        "query_id": uuid4().hex,
        "source_list": [],
        "followup_qas": [],
        "with_upload": True
    }
}

# Make the POST request with streaming
response = requests.post(url, headers=headers, json=payload, stream=True)

# Print the response status code
print(f"Status Code: {response.status_code}")

# Stream the response content
if response.status_code == 200:
    for chunk in response.iter_content(chunk_size=64):
        print(chunk.decode('utf-8'), end='', flush=True)