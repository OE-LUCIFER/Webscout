import requests

url = "https://api.magickpen.com/chat/free"

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "access-control-allow-origin": "*",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://magickpen.com",
    "priority": "u=1, i",
    "referer": "https://magickpen.com/",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
}

payload = {
    "history": [
        {
            "role": "user",
            "content": "hi"
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)

print("Status Code:", response.status_code)
print("Response Body:", response.content)