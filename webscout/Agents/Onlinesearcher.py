import json
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
from webscout import GoogleS, GEMINIAPI
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


class WebSearchAgent:
    def __init__(self):
        self.webs = GoogleS()
        self.ai = GEMINIAPI(is_conversation=False, api_key='AIzaSyAYlT5-V0MXZwaLYpXCF1Z-Yvy_tx1jylA')

    def generate_search_queries(self, information: str, num_queries: int = 10) -> List[str]:
        prompt = f""" Task: Generate exactly {num_queries} optimal search queries based on the given information.  
Instructions: 
1. Analyze the provided information thoroughly. 
2. Identify key concepts, entities, and relationships. 
3. Formulate {num_queries} concise and specific search queries that will yield relevant and diverse results. 
4. Each query should focus on a different aspect or angle of the information. 
5. The queries should be in natural language, not in the form of keywords. 
6. Avoid unnecessary words or phrases that might limit the search results. 
7. **Important**: Return the response **ONLY** in JSON format without any additional text or code blocks.  
Your response must be in the following JSON format: {{
    "search_queries": [
        "Your first search query here",
        "Your second search query here",
        "...",
        "Your last search query here"
    ]
}}  
Ensure that: 
- You provide exactly {num_queries} search queries. 
- Each query is unique and focuses on a different aspect of the information. 
- The queries are in plain text, suitable for a web search engine.  

Information to base the search queries on: 
{information}  

Now, generate the optimal search queries: """

        response = ""
        for chunk in self.ai.chat(prompt):
            response += chunk

        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                json_response = json.loads(json_str)
                print(json_response['search_queries'])
                return json_response["search_queries"]
            except json.JSONDecodeError:
                pass

        queries = re.findall(r'"([^"]+)"', response)
        if len(queries) >= num_queries:
            return queries[:num_queries]
        elif queries:
            return queries
        else:
            return [information]

    def search(self, information: str, region: str = 'wt-wt', safe: str = 'off',
               max_results: int = 10) -> List[Dict]:
        search_queries = self.generate_search_queries(information, num_queries=10)
        all_results = []

        for query in search_queries:
            results = []
            with self.webs as webs:
                for result in webs.search(query, region=region, safe=safe,
                                       max_results=max_results):
                    results.append(result)
            all_results.extend(results)

        return all_results

    def extract_urls(self, results: List[Dict]) -> List[str]:
        urls = [result.get('href') for result in results if result.get('href')]
        unique_urls = list(set(urls))
        return unique_urls

    def fetch_webpage(self, url: str) -> Dict[str, str]:
        try:
            with httpx.Client(timeout=120) as client:
                response = client.get(url)
                if response.status_code == 200:
                    html = response.text
                    soup = BeautifulSoup(html, 'html.parser')
                    paragraphs = soup.find_all('p')
                    text = ' '.join([p.get_text() for p in paragraphs])
                    words = text.split()
                    if len(words) > 600:
                        text = ' '.join(words[:600]) + '...'
                    return {"url": url, "content": text}
                else:
                    return {"url": url, "content": f"Failed to fetch {url}: HTTP {response.status_code}"}
        except Exception as e:
            return {"url": url, "content": f"Error fetching {url}: {str(e)}"}

    def fetch_all_webpages(self, urls: List[str], max_workers: int = 10) -> List[Dict[str, str]]:
        contents = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.fetch_webpage, url): url for url in urls}
            for future in as_completed(future_to_url):
                result = future.result()
                contents.append(result)
        return contents


class OnlineSearcher:
    def __init__(self):
        self.agent = WebSearchAgent()
        self.ai = GEMINIAPI(is_conversation=False, api_key='GOOGLE GEMINI API')

    def answer_question(self, question: str) -> None:
        search_results = self.agent.search(question, max_results=10)
        urls = self.agent.extract_urls(search_results)
        webpage_contents = self.agent.fetch_all_webpages(urls)

        context = "Web search results and extracted content:\n\n"
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'No Title')
            href = result.get('href', 'No URL')
            snippet = result.get('body', 'No Snippet')
            context += f"{i}. **Title:** {title}\n   **URL:** {href}\n   **Snippet:** {snippet}\n\n"

        context += "Extracted webpage contents:\n"
        for i, webpage in enumerate(webpage_contents, 1):
            content = webpage['content']
            content_preview = content[:600] + '...' if len(content) > 600 else content
            context += f"{i}. **URL:** {webpage['url']}\n   **Content:** {content_preview}\n\n"

        prompt = f""" Task: Provide a comprehensive, insightful, and well-structured answer to the given question based on the provided web search results and your general knowledge.  
Question: {question}  
Context: {context}  
Instructions:  
1. Carefully analyze the provided web search results and extracted content.  
2. Synthesize the information to form a coherent and comprehensive answer.  
3. If the search results contain relevant information, incorporate it into your answer seamlessly.  
4. Avoid providing irrelevant information, and do not reference "according to web page".  
5. If the search results don't contain sufficient information, clearly state this and provide the best answer based on your general knowledge.  
6. Ensure your answer is well-structured, factual, and directly addresses the question.  
7. Use clear headings, bullet points, or other formatting tools to enhance readability where appropriate.  
8. Strive for a tone and style similar to that of professional, authoritative sources like Perplexity, ensuring clarity and depth in your response.  
Your response should be informative, accurate, and properly sourced when possible. Begin your answer now: """

        for chunk in self.ai.chat(prompt, stream=True):
            print(chunk, end='', flush=True)



# Usage example
if __name__ == "__main__":
    assistant = OnlineSearcher()
    while True:
        try:
            question = input(">>> ")
            if question.lower() == 'quit':
                break
            print("=" * 50)
            assistant.answer_question(question) 
            print("=" * 50)
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

"""
def format_prompt(messages: Messages, add_special_tokens=False) -> str:

    if not add_special_tokens and len(messages) <= 1:
        return messages[0]["content"]
    formatted = "\n".join([
        f'{message["role"].capitalize()}: {message["content"]}'
        for message in messages
    ])
    return f"{formatted}\nAssistant:
"""