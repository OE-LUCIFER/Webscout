import json
from webscout import WEBS
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

class DeepInfra:
    def __init__(
        self,
        model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct",
        max_tokens: int = 8000,
        timeout: int = 120,
        system_prompt: str = "You are a helpful AI assistant.",
        proxies: dict = {}
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.system_prompt = system_prompt
        self.chat_endpoint = "https://api.deepinfra.com/v1/openai/chat/completions"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://deepinfra.com',
            'Pragma': 'no-cache',
            'Referer': 'https://deepinfra.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'X-Deepinfra-Source': 'web-embed',
            'accept': 'text/event-stream',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        self.client = httpx.Client(proxies=proxies, headers=self.headers)

    def ask(self, prompt: str, system_prompt: str = None) -> str:
        payload = {
            'model': self.model,
            'messages': [
                {"role": "system", "content": system_prompt or self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            'temperature': 0.7,
            'max_tokens': self.max_tokens,
            'stop': []
        }

        response = self.client.post(self.chat_endpoint, json=payload, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(f"Failed to generate response - ({response.status_code}, {response.reason_phrase}) - {response.text}")

        resp = response.json()
        return resp["choices"][0]["message"]["content"]

class WebSearchAgent:

    def __init__(self, model="Qwen/Qwen2-72B-Instruct"):
        self.webs = WEBS()
        self.deepinfra = DeepInfra(model=model)

    def generate_search_query(self, information):
        prompt = f"""
        Instructions:
        You are a smart online searcher for a large language model.
        Given information, you must create a search query to search the internet for relevant information.
        Your search query must be in the form of a json response.
        Exact json response format must be as follows:
        
        {{
            "search_query": "your search query"
        }}
        - You must only provide ONE search query
        - You must provide the BEST search query for the given information
        - The search query must be normal text.

        Information: {information}
        """

        response = self.deepinfra.ask(prompt)
        return json.loads(response)["search_query"]

    def search(self, information, region='wt-wt', safesearch='off', timelimit='y', max_results=5):
        search_query = self.generate_search_query(information)
        
        results = []
        with self.webs as webs:
            for result in webs.text(search_query, region=region, safesearch=safesearch, timelimit=timelimit, max_results=max_results):
                results.append(result)
        
        return results

    def extract_urls(self, results):
        urls = []
        for result in results:
            url = result.get('href')
            if url:
                urls.append(url)
        return list(set(urls))  # Remove duplicates

    def fetch_webpage(self, url: str) -> str:
        try:
            response = httpx.get(url, timeout=120)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract text from <p> tags
                paragraphs = soup.find_all('p')
                text = ' '.join([p.get_text() for p in paragraphs])
                
                # Limit the text to around 4000 words
                words = text.split()
                if len(words) > 4000:
                    text = ' '.join(words[:4000]) + '...'
                
                return text
            else:
                return f"Failed to fetch {url}: HTTP {response.status}"
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"

    def fetch_all_webpages(self, urls: List[str]) -> List[Dict[str, str]]:
        contents = []
        for url in urls:
            content = self.fetch_webpage(url)
            contents.append({"url": url, "content": content})
        return contents

class OnlineSearcher:
    def __init__(self, model="meta-llama/Meta-Llama-3.1-405B-Instruct"):
        self.agent = WebSearchAgent(model)
        self.deepinfra = DeepInfra(model="model")

    def answer_question(self, question: str) -> str:
        # Perform web search
        search_results = self.agent.search(question)

        # Extract URLs
        urls = self.agent.extract_urls(search_results)

        # Fetch webpage contents
        webpage_contents = self.agent.fetch_all_webpages(urls)

        # Prepare context for AI
        context = "Based on the following search results and webpage contents:\n\n"
        for i, result in enumerate(search_results, 1):
            context += f"{i}. Title: {result['title']}\n   URL: {result['href']}\n   Snippet: {result['body']}\n\n"

        context += "Extracted webpage contents:\n"
        for i, webpage in enumerate(webpage_contents):
            context += f"{i}. URL: {webpage['url']}\n   Content: {webpage['content'][:4000]}...\n\n"

        # Generate answer using AI
        prompt = f"{context}\n\nQuestion: {question}\n\nPlease provide a comprehensive answer to the question based on the search results and webpage contents above. Include relevant webpage URLs in your answer when appropriate. If the search results and webpage contents don't contain relevant information, please state that and provide the best answer you can based on your general knowledge. [YOUR RESPONSE WITH SOURCE LINKS ([➊](URL))"

        answer = self.deepinfra.ask(prompt)
        return answer

# Usage example
if __name__ == "__main__":
    assistant = OnlineSearcher()
    while True:
        question = input(">>> ")
        if question.lower() == 'quit':
            break
        answer = assistant.answer_question(question)
        print(answer)
        print("\n" + "-"*50 + "\n")
