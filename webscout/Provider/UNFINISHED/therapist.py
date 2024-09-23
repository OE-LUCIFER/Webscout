import requests
import json
import sys

def create_message():
    url = "https://www.therapist-online.org/api/createMessage"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "TherapistOnlineClient/1.0",
    }

    user_input = input(">>> ")

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
    }

    # Enable streaming by setting stream=True
    with requests.post(url, headers=headers, json=payload, stream=True) as response:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}", file=sys.stderr)
            return

        # Initialize an empty string to accumulate the response
        accumulated_response = ""

        # Iterate over the response line by line
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    # Parse each line as JSON
                    data = json.loads(line)
                    
                    # Check if the data contains the expected structure
                    if 'data' in data and 'choices' in data['data']:
                        for choice in data['data']['choices']:
                            content = choice['message']['content']
                            # Print the content without adding a new line
                            print(content, end='', flush=True)
                            accumulated_response += content
                    else:
                        print("Unexpected response structure:", file=sys.stderr)
                        print(json.dumps(data, indent=2), file=sys.stderr)
                except json.JSONDecodeError:
                    print("Received non-JSON data:", line, file=sys.stderr)

        print()  # Add a newline after streaming is complete

if __name__ == "__main__":
    create_message()