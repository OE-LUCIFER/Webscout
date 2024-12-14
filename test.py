import cloudscraper
import json
import time

def make_chat_request():
    # Create a cloudscraper instance with additional options
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=10  # Add delay between requests
    )
    
    url = "https://ap-northeast-2.apistage.ai/v1/web/demo/chat/completions"
    
    # Updated headers with additional security measures
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://console.upstage.ai",
        "referer": "https://console.upstage.ai/",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        # You'll need to get a fresh token
        "x-csrf-token": None  # Get this from the website's console or network tab
    }
    
    data = {
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "Detail the making of traditional French baguettes, including key steps and ingredients."
            }
        ],
        "model": "solar-pro"
    }

    try:
        # Add retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            response = scraper.post(url, headers=headers, json=data, stream=True)
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        if line.startswith(b'data: '):
                            line = line[6:]
                        
                        if line == b'[DONE]':
                            break
                            
                        try:
                            chunk = json.loads(line)
                            if 'choices' in chunk and chunk['choices']:
                                if 'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                                    content = chunk['choices'][0]['delta']['content']
                                    print(content, end='', flush=True)
                        except json.JSONDecodeError as e:
                            print(f"JSON parsing error: {e}")
                break
            elif response.status_code == 403:
                print(f"Attempt {attempt + 1} failed with 403 Forbidden")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retrying
                continue
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response content: {response.text}")
                break
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    make_chat_request()