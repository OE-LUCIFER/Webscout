import uuid
import requests
import json

# Define the URL
url = "https://api.julius.ai/api/chat/message"

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "authorization": "Bearer",
    "content-length": "206",
    "content-type": "application/json",
    "conversation-id": str(uuid.uuid4()),
    "dnt": "1",
    "interactive-charts": "true",
    "is-demo": "temp_14aabbb1-95bc-4203-a678-596258d6fdf3",
    "is-native": "false",
    "orient-split": "true",
    "origin": "https://julius.ai",
    "platform": "undefined",
    "priority": "u=1, i",
    "referer": "https://julius.ai/",
    "request-id": str(uuid.uuid4()),
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "visitor-id": str(uuid.uuid4())
}

# Define the payload
payload = {
    "message": {"content": input(">>> "), "role": "user"},
    "provider": "default",
    "chat_mode": "auto",
    "client_version": "20240130",
    "theme": "dark",
    "new_images": None,
    "new_attachments": None,
    "dataframe_format": "json",
    "selectedModels": ["Gemini Flash"], #Llama 3, GPT-4o, GPT-3.5, Command R, Gemini Flash, Gemini 1.5

}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)
# Initialize an empty string to concatenate contents
full_content = ""

# Split the response by lines and parse each line as JSON
for line in response.text.splitlines():
    try:
        # Parse the JSON line
        data = json.loads(line)
        # Check if 'content' exists in the JSON
        if 'content' in data:
            # Concatenate the content
            full_content += data['content']
    except json.JSONDecodeError:
        # Handle JSON decode error
        print("Failed to decode JSON:", line)
for c in full_content:
    print(c, end="", flush=True)

