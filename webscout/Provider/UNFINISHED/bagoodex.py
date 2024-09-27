import requests

url = "https://bagoodex.io/front-api/chat"

payload = {
    "prompt": "You are AI",
    "messages": [{"content": "Hi, this is chatgpt, let's talk", "role": "assistant"}],
    "input": input(">>> "),
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
