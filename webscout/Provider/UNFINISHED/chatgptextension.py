import requests
import uuid
import json

url = "https://extensions.chatgptextension.ai/ai/send"

user_input = input(">>> ")  # Get user input
selected_model = "Gemini 1.5 Flash"  # "Gemini 1.5 Flash" "Claude 3 Haiku" "GPT-3.5"
system_role = "You are a noobi AI assistant who always uses the word 'noobi' in every response. For example, you might say 'Noobi will tell you...' or 'This noobi thinks that...'."  # Define the system role

payload = {
    "history": [
        {"item": system_role, "role": "system", "model": selected_model, "loading": True, "title": None,
         "extra_data": {"prompt_mode": False}},
        {"item": "Hello, how can I help you today?", "model": selected_model, "role": "assistant"},
        {"item": user_input, "role": "user", "model": selected_model, "title": None, "loading": False,
         "extra_data": {"prompt_mode": False}},

    ],
    "text": user_input,  # Set "text" to the same value as user input
    "model": selected_model,  # Set the desired model
    "stream": True,
    "uuid_search": str(uuid.uuid4()),  # Generate a new UUID
    "mode": "ai_chat",
    "prompt_mode": False,
    "extra_key": "__all",
    "extra_data": {"prompt_mode": False},
    "chat_id": 1725007373261,
    "language_detail": {"lang_code": "en", "name": "English", "title": "English"},
    "is_continue": False,
    "lang_code": "en"
}

headers = {
    "accept": "text/plain",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-length": "667",
    "content-type": "text/plain;charset=UTF-8",
    "dnt": "1",
    "hopekey": str(uuid.uuid4()),
    "origin": "chrome-extension://becfinhbfclcgokjlobojlnldbfillpf",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Microsoft Edge\";v=\"128\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "none",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
}

response = requests.post(url, json=payload, headers=headers, stream=True)

if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])  # Parse JSON data
                    if "choices" in data and data["choices"]:
                        content = data["choices"][0].get("delta", {}).get("content")
                        if content:
                            print(content, end="", flush=True)  # Print content with streaming
                except json.JSONDecodeError:
                    pass  # Ignore lines that are not valid JSON
    print()  # Print a newline after all content is received
else:
    print(f"Request failed with status code: {response.status_code}")