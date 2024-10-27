import requests
import json

def make_api_request():
    # Original and new user_id
    original_user_id = "7374bcc2f9aa4bdabe374d2c70ca554a"  
    
    # API endpoint
    url = 'https://gpt4omini.app/api/chat/generateTextStream'
    
    # Complete headers from original request
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
        'content-type': 'text/plain;charset=UTF-8',
        'dnt': '1',
        'origin': 'https://gpt4omini.app',
        'referer': 'https://gpt4omini.app/?via=topaitools',
        'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
        'priority': 'u=1, i'
    }
    
    # Complete payload from original request
    payload = {
        "textStr": "hi",
        "user_id": original_user_id,  
        "model": "GPT-4o Mini" # GPT-4o, GPT-4o Mini
    }
    
    try:
        # Make POST request
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        # Print only response content
        print(response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    make_api_request()