import json
import colorlog
from webscout import WEBS
from webscout import DeepInfra
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

class WebSearchAgent:
    def __init__(self):
        self.webs = WEBS()
        self.ai = DeepInfra(is_conversation=False)

    def generate_search_queries(self, information, num_queries=3):
        prompt = f"""
        Task: Generate {num_queries} optimal search queries based on the given information.

        Instructions:
        1. Analyze the provided information carefully.
        2. Identify key concepts, entities, and relationships.
        3. Formulate {num_queries} concise and specific search queries that will yield relevant results.
        4. Each query should focus on a different aspect or angle of the information.
        5. The queries should be in natural language, not in the form of keywords.
        6. Avoid unnecessary words or phrases that might limit the search results.

        Your response must be in the following JSON format:
        {{
            "search_queries": [
                "Your first search query here",
                "Your second search query here",
                "Your third search query here"
            ]
        }}

        Ensure that:
        - You provide exactly {num_queries} search queries.
        - Each query is unique and focuses on a different aspect of the information.
        - The queries are in plain text, suitable for a web search engine.

        Information to base the search queries on:
        {information}

        Now, generate the optimal search queries:
        """

        response = ""
        for chunk in self.ai.chat(prompt):
            response += chunk

        try:
            json_response = json.loads(response)
            return json_response["search_queries"]
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON. Raw response: {response}")
            # Fallback: try to extract queries manually
            queries = []
            for line in response.split('\n'):
                if line.strip().startswith('"') and line.strip().endswith('"'):
                    queries.append(line.strip(' "'))
            if queries:
                return queries[:num_queries]
            else:
                print(f"Warning: Using original information as search query.")
                return [information]

    def search(self, information, region='wt-wt', safesearch='off', timelimit='y', max_results=5):
        search_queries = self.generate_search_queries(information)
        all_results = []
        
        for query in search_queries:
            results = []
            with self.webs as webs:
                for result in webs.text(query, region=region, safesearch=safesearch, timelimit=timelimit, max_results=max_results):
                    results.append(result)
            all_results.extend(results)
        
        return all_results

    def extract_urls(self, results):
        urls = []
        for result in results:
            url = result.get('href')
            if url:
                urls.append(url)
        return list(set(urls))

    def fetch_webpage(self, url: str) -> str:
        try:
            response = httpx.get(url, timeout=120)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                paragraphs = soup.find_all('p')
                text = ' '.join([p.get_text() for p in paragraphs])
                words = text.split()
                if len(words) > 600:
                    text = ' '.join(words[:600]) + '...'
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
    def __init__(self):
        self.agent = WebSearchAgent()
        self.ai = DeepInfra(is_conversation=False)

    def answer_question(self, question: str):
        search_results = self.agent.search(question)
        urls = self.agent.extract_urls(search_results)
        webpage_contents = self.agent.fetch_all_webpages(urls)

        context = "Web search results and extracted content:\n\n"
        for i, result in enumerate(search_results, 1):
            context += f"{i}. Title: {result['title']}\n   URL: {result['href']}\n   Snippet: {result['body']}\n\n"

        context += "Extracted webpage contents:\n"
        for i, webpage in enumerate(webpage_contents):
            context += f"{i}. URL: {webpage['url']}\n   Content: {webpage['content'][:600]}...\n\n"

        prompt = f"""
        Task: Provide a comprehensive and accurate answer to the given question based on the provided web search results and your general knowledge.

        Question: {question}

        Context:
        {context}

        Instructions:
        1. Carefully analyze the provided web search results and extracted content.
        2. Synthesize the information to form a coherent and comprehensive answer.
        3. If the search results contain relevant information, incorporate it into your answer.
        4. Don't provide irrelevant information, and don't say "according to web page".
        5. If the search results don't contain sufficient information, clearly state this and provide the best answer based on your general knowledge.
        6. Ensure your answer is well-structured, factual, and directly addresses the question.
        7. If appropriate, provide additional context or related information that might be helpful.

        Your response should be informative, accurate, and properly sourced when possible. Begin your answer now:
        """

        return self.ai.chat(prompt)

# Usage example
if __name__ == "__main__":
    assistant = OnlineSearcher()
    while True:
        question = input(">>> ")
        if question.lower() == 'quit':
            break
        print("\n" + "="*50)
        for chunk in assistant.answer_question(question):
            print(chunk, end="", flush=True)
        print("\n" + "="*50)