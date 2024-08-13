import uuid
import requests

# Define the URL
url = "https://www.xdash.ai/api/query"

# Define the headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
    "content-type": "application/json",
    "cookie": "cf_clearance=73aup_8JU0LU.tRr7D4qd4Kt7gapKFi3RVW8jLzQoP0-1723549451-1.0.1.1-HTRrjMvM5GRLsfCTB0v3N_UxQzQMfA1fvOSf0dsZJ73HR6.IUTH8BH.G1dpx3s_IxVHCBCHMXOCt0K7vyIwMgw",
    "dnt": "1",
    "origin": "https://www.xdash.ai",
    "priority": "u=1, i",
    "referer": "https://www.xdash.ai/search",
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
    "query": input('>>> '),
    "search_uuid": uuid.uuid4().hex,
    "visitor_uuid": uuid.uuid4().hex,
    "token": uuid.uuid4().hex
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

# Extract the LLM response
llm_response = response.text.split("__LLM_RESPONSE__")[1].split("__RELATED_QUESTIONS__")[0]

print("=" * 80)
print(llm_response.strip())
print("=" * 80)
