import requests
import json

def make_realtime_request():
    # Define the URL
    url = "https://chat.typegpt.net/api/openai/v1/chat/completions"
    
    # Define headers
    headers = {
        'authority': 'chat.typegpt.net',
        'accept': 'application/json, text/event-stream',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://chat.typegpt.net',
        'referer': 'https://chat.typegpt.net/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    # Define payload
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "hi"}
        ],
        "stream": True,
        "model": "gpt-4o",
        "temperature": 0.5,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "top_p": 1,
        "max_tokens": 4000
    }
    
    try:
        # Make the POST request with streaming enabled
        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            
            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    # Remove 'data: ' prefix if present
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                    
                    # Skip [DONE] message
                    if line.strip() == '[DONE]':
                        break
                    
                    try:
                        # Parse the JSON data
                        data = json.loads(line)
                        
                        # Extract and print content if available
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                print(delta['content'], end='', flush=True)
                    except json.JSONDecodeError:
                        continue
            
            print()  # New line at the end
                    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Starting request...")
    make_realtime_request()