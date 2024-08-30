import requests
import re
import json

# Define the URL and the payload
url = "https://search.lepton.run/api/query"
ask = input(">>> ")
payload = json.dumps({"query": ask})

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-type": "text/plain;charset=UTF-8",
    "dnt": "1",
    "origin": "https://search.lepton.run",
    "priority": "u=1, i",
    "referer": "https://search.lepton.run/search?q=BYSyA&rid=aqZSHQomzwBBF3fyHnrND",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
}

# Send the POST request
response = requests.post(url, data=payload, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Retrieve the response text
    response_text = response.text

    # Find the start and end markers
    start_marker = "__LLM_RESPONSE__"
    end_marker = "__RELATED_QUESTIONS__"
    
    # Extract the content between the markers
    start_index = response_text.find(start_marker) + len(start_marker)
    end_index = response_text.find(end_marker)
    
    if start_index != -1 and end_index != -1:
        extracted_text = response_text[start_index:end_index].strip()
        
        # Remove citations using regular expression
        cleaned_text = re.sub(r'\[citation:\d+\]', '', extracted_text)
        
        # Print each chunk
        for chunk in cleaned_text:
            print(chunk, end="", flush=True)
        print()  # Print a newline at the end
    else:
        print("Markers not found in the response text.")
else:
    print(f"Request failed with status code {response.status_code}")