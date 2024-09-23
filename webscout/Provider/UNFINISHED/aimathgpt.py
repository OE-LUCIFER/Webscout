import requests
import json

def send_post_request():
    url = "https://aimathgpt.forit.ai/api/ai"

    headers = {
        "authority": "aimathgpt.forit.ai",
        "method": "POST",
        "path": "/api/ai",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "content-length": "397",
        "content-type": "application/json",
        "cookie": (
            "NEXT_LOCALE=en; _ga=GA1.1.1515823701.1726936796; "
            "_ga_1F3ZVN96B1=GS1.1.1726936795.1.1.1726936833.0.0.0"
        ),
        "dnt": "1",
        "origin": "https://aimathgpt.forit.ai",
        "priority": "u=1, i",
        "referer": "https://aimathgpt.forit.ai/?ref=taaft&utm_source=taaft&utm_medium=referral",
        "sec-ch-ua": (
            "\"Microsoft Edge\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\""
        ),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
        )
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert math tutor. For each question, provide: "
                    "1) A clear, step-by-step problem-solving approach. "
                    "2) A concise explanation of the underlying concepts. "
                    "3) One follow-up question to deepen understanding. "
                    "4) A helpful tip or common pitfall to watch out for. "
                    "Keep your responses clear and concise."
                )
            },
            {
                "role": "user",
                "content": input(">>> ")
            }
        ],
        "model": "llama3"
    }

    try:
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True) as response:
            response.raise_for_status()  # Raises HTTPError for bad responses
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        # Attempt to parse the line as JSON
                        data = json.loads(line)
                        # Extract and print the desired part of the response
                        if 'result' in data and 'response' in data['result']:
                            print(data['result']['response'], end='', flush=True)
                        else:
                            print(line, end='', flush=True)
                    except json.JSONDecodeError:
                        # If the line isn't valid JSON, print it as is
                        print(line, end='', flush=True)

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP error
    except Exception as err:
        print(f"An error occurred: {err}")  # Other errors

if __name__ == "__main__":
    send_post_request()