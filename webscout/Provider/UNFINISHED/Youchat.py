from re import findall
import cloudscraper
from uuid import uuid4
from requests.exceptions import RequestException
import json

class YouChatAPI:
    """
    This class provides methods for interacting with the You.com chat API.
    """

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()  # Create a Cloudscraper session

    def create_request(self, query):
        try:
            # Prepare the request parameters
            response = self.scraper.get(
                "https://you.com/api/streamingSearch",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
                    "Accept": "text/event-stream",
                    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
                    "Referer": "https://you.com/search?q=hi&fromSearchBar=true&tbm=youchat",
                    "Connection": "keep-alive",
                    "DNT": "1",
                },
                cookies={
                    "uuid_guest_backup": uuid4().hex,
                    "youchat_personalization": "true",
                    "youchat_smart_learn": "true",
                    "youpro_subscription": "false",
                    "ydc_stytch_session": uuid4().hex,
                    "ydc_stytch_session_jwt": uuid4().hex,
                    "__cf_bm": uuid4().hex,
                },
                params={
                    "q": query,
                    "page": 1,
                    "count": 10,
                    "safeSearch": "Moderate",
                    "mkt": "en-IN",
                    "domain": "youchat",
                    "use_personalization_extraction": "true",
                    "queryTraceId": str(uuid4()),
                    "chatId": str(uuid4()),
                    "conversationTurnId": str(uuid4()),
                    "pastChatLength": 0,
                    "isSmallMediumDevice": "true",
                    "selectedChatMode": "default",
                    "traceId": str(uuid4()),
                    "chat": "[]"
                },
            )

            # Check for successful response
            if response.status_code != 200:
                raise RequestException(f"Request failed with status code {response.status_code}")

            if "youChatToken" not in response.text:
                raise RequestException("Unable to fetch the response.")

            # Extract the youChatToken value
            return response.text

        except RequestException as e:
            print(f"An error occurred: {e}")
            raise

    def extract_youchat_tokens(self, response_text):

        tokens = []
        for line in response_text.split('\n'):
            if line.startswith('data: ') and 'youChatToken' in line:
                data = json.loads(line[6:])  # Skip 'data: ' prefix
                token = data.get('youChatToken', '')
                if token:
                    tokens.append(token)
        return ''.join(tokens)

# Example usage
if __name__ == "__main__":
    from rich import print
    completion = YouChatAPI()
    prompt = "tell me avout india"
    try:
        result = completion.create_request(prompt)
        tokens = completion.extract_youchat_tokens(result)
        for t in tokens:
            print(t, end="", flush=True)
    except Exception as e:
        print("Error:", str(e))