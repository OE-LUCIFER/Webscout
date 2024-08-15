from uuid import uuid4
import requests
import textwrap

# Define the URL
url = "https://artifacts.e2b.dev/api/chat"

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-length": "257",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://artifacts.e2b.dev",
    "priority": "u=1, i",
    "referer": "https://artifacts.e2b.dev/",
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
    "messages": [
        {
            "role": "user",
            "content": input(">>> ")
        }
    ],
    "userID": uuid4().hex,
    "template": "code-interpreter-multilang",
    "model": {
        "id": "gpt-4o",
        "provider": "OpenAI",
        "providerId": "openai",
        "name": "GPT-4o",
        "hosted": True
    },
    "config": {
        "model": "gpt-4o"
    }
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

# Process and print the response content
if response.status_code == 200:
    content = response.text
    processed_content = ''.join([part.split(':')[1].strip('"') for part in content.split('\n') if part])
    
    # Split the content into paragraphs
    paragraphs = processed_content.split('\\n\\n')
    
    print("\n" + "="*50 + "\n")
    
    for i, paragraph in enumerate(paragraphs):
        # Remove numbering if present
        if paragraph.startswith(tuple(f"{n}." for n in range(1, 10))):
            paragraph = paragraph[3:]
        
        # Add bold formatting to titles
        if "**" in paragraph:
            title, content = paragraph.split("**", 2)[1:]
            print(f"\n{title.strip().upper()}\n")
            paragraph = content.strip()
        
        wrapped_text = textwrap.fill(paragraph.strip(), width=70)
        print(wrapped_text)
        
        # Add a newline after each paragraph except the last one
        if i < len(paragraphs) - 1:
            print()
    
    print("\n" + "="*50)

