from uuid import uuid4
import cloudscraper
import json

# Create a Cloudscraper session
scraper = cloudscraper.create_scraper()

# URL of the protected resource
url = 'https://chat.hix.ai/api/hix/chat'

# Headers
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'DNT': '1',
    'Origin': 'https://chat.hix.ai',
    'Referer': 'https://chat.hix.ai/',
    'Sec-CH-UA': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    'Sec-CH-UA-Mobile': '?0',
    'Sec-CH-UA-Platform': '"Windows"',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
}

# Cookies
cookies = {
    '__Secure-next-auth.session-token': 'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..hBFETmhPJTRS3fPD.5tBDgvRuok9Osh5fGFREINinejDO7U2l5Xlfc23gZnpliuuYlvmf8Uct5BY9tORXPcM7D5jr6flh43pTgWD0Nn3dDC3ut80NmmXpD2hiBoP3OW0S5-_YZwNMmz3xqvGcLgNryXFB5jqbrwC1UM-7aLlQ5zOC7yhc9u9fYEN0ypA3_RKmzuiRMTzbzoRRD-wD0QglXemzH3OqTCs_X1XCOkdaiTOgGWLkZWqPCrY-_8ce-QtXyDNoX7_f1rpeof98658BW1otk4_2l-PWqlmS1SPXWXmd5nZ1lY8NELIbbftKJ-CP8gKJoYWIPZNy6g4t-U2ixopLX-stj2c65RoCGpoWw6MHphm7Kcs69GOQdy61Ow0Isl-ez1kGDtpw39qLF4BfHT-Al8s-8g-LayrkQzO0RJqhq8-BtQ.3e40DRZwUjHf3IkPtzMGCg',
    'device-id': uuid4().hex,
}

# Data to be sent in the POST request
data = {
    'chatId': 'clzs7lada0024n5wyfoxbvsid', 
    'question': 'hi',
    'fileUrl': ''
}

# Make the POST request
response = scraper.post(url, headers=headers, cookies=cookies, json=data)

# Check the response
if response.status_code == 200:
    print("Response:")
    print(response.text)
else:
    print(f"Error: {response.status_code} - {response.text}")