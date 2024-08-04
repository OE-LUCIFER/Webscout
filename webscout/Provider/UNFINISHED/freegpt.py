import requests
import json

# Define the URL
url = "https://free.netfly.top/api/openai/v1/chat/completions"

# Define the headers
headers = {
    "accept": "application/json, text/event-stream",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-type": "application/json",
    "cookie": "cfzs_google-analytics_v4=%7B%22lmQM_pageviewCounter%22%3A%7B%22v%22%3A%221%22%7D%7D; cf_clearance=evGDCEoN2yxvfr3f6O099i7ZThMQsizM7ukBKUbFf2g-1722578161-1.0.1.1-Fl3OI7x2kIom63UmZQeQ_CQGIMB4aOvelqcYbAS1j1pFm_pHFooNvf7IUyGN3MuT_Y5slle.LmHlAaW7NhHsug; cfz_google-analytics_v4=%7B%22lmQM_engagementDuration%22%3A%7B%22v%22%3A%220%22%2C%22e%22%3A1754114160411%7D%2C%22lmQM_engagementStart%22%3A%7B%22v%22%3A1722578176597%2C%22e%22%3A1754114178768%7D%2C%22lmQM_counter%22%3A%7B%22v%22%3A%221%22%2C%22e%22%3A1754114160411%7D%2C%22lmQM_ga4sid%22%3A%7B%22v%22%3A%221040692052%22%2C%22e%22%3A1722579960411%7D%2C%22lmQM_session_counter%22%3A%7B%22v%22%3A%221%22%2C%22e%22%3A1754114160411%7D%2C%22lmQM_ga4%22%3A%7B%22v%22%3A%2249a583bf-b4c3-4098-81fb-018b3740fc9a%22%2C%22e%22%3A1754114160411%7D%2C%22lmQM__z_ga_audiences%22%3A%7B%22v%22%3A%2249a583bf-b4c3-4098-81fb-018b3740fc9a%22%2C%22e%22%3A1754114160411%7D%2C%22lmQM_let%22%3A%7B%22v%22%3A%221722578160411%22%2C%22e%22%3A1754114160411%7D%7D",
    "dnt": "1",
    "origin": "https://free.netfly.top",
    "referer": "https://free.netfly.top/",
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
            "role": "system",
            "content": "\nYou are ChatGPT, a large language model trained by OpenAI.\nKnowledge cutoff: 2021-09\nCurrent model: gpt-3.5-turbo\nCurrent time: Fri Aug 02 2024 11:26:32 GMT+0530 (India Standard Time)\nLatex inline: \\(x^2\\) \nLatex block: $$e=mc^2$$\n\n"
        },
        {
            "role": "user",
            "content": input(">>> ")
        },
    ],
    "stream": True,
    "model": "gpt-3.5-turbo",
    "temperature": 0.5,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "top_p": 1
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload, stream=True)

# Process the streaming response
if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                json_data = decoded_line[6:]
                if json_data == "[DONE]":
                    break
                try:
                    data = json.loads(json_data)
                    content = data["choices"][0]["delta"].get("content", "")
                    print(content, end="", flush=True)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {json_data}")
else:
    print(f"Request failed with status code: {response.status_code}")