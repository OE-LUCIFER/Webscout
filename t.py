import os
import re
import sys
import time
import shutil
import logging
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from webscout import WEBS
import requests
from bs4 import BeautifulSoup
import backoff
import openai
from rich.console import Console
from rich.logging import RichHandler

# -----------------------------------------------------------------------------
# Configuration class for better settings management
@dataclass
class Config:
    NUM_SEARCH: int = 10  # Number of links to parse from Google
    SEARCH_TIME_LIMIT: int = 3  # Max seconds to request website sources
    TOTAL_TIMEOUT: int = 15  # Overall timeout for all operations
    MAX_CONTENT: int = 500  # Number of words per search result
    MAX_TOKENS: int = 1000  # Maximum tokens for LLM response
    LLM_MODEL: str = 'gpt-4o-mini'

    USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Global configuration instance
config = Config()

# Set up rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("webscout")


class WebScoutError(Exception):
    """Base exception class for WebScout errors"""
    pass

class FetchError(WebScoutError):
    """Raised when fetching webpage content fails"""
    pass

class SearchError(WebScoutError):
    """Raised when search operation fails"""
    pass

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing special characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        A sanitized filename string
    """
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename)

def get_cache_key(query: str) -> str:
    """
    Generate a safe cache key from the query.
    
    Args:
        query: The search query
        
    Returns:
        MD5 hash of the query as cache key
    """
    return hashlib.md5(query.encode()).hexdigest()

def trace_function_factory(start_time):
    """Factory function to create a trace function for timeout."""
    def trace_function(frame, event, arg):
        if time.time() - start_time > config.TOTAL_TIMEOUT:
            raise TimeoutError("Operation timed out")
        return trace_function
    return trace_function

class WebPageFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
    
    def fetch_webpage(self, url: str, timeout: int) -> tuple[str, Optional[str]]:
        """
        Fetch and parse webpage content with improved error handling.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (url, content_text)
        """
        start = time.time()
        sys.settrace(trace_function_factory(start))
        try:
            logger.info(f"🌐 Fetching: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            # Get text from main content elements
            text_elements = []
            for tag in ['p', 'h1', 'h2', 'h3', 'h4', 'article', 'section', 'main']:
                elements = soup.find_all(tag)
                text_elements.extend([elem.get_text(strip=True) for elem in elements])
            
            # Clean and join text
            page_text = ' '.join(filter(None, text_elements))
            page_text = re.sub(r'\s+', ' ', page_text).strip()
            
            logger.info(f"✅ Successfully parsed: {url}")
            return url, page_text
            
        except requests.RequestException as e:
            logger.error(f"❌ Request error for {url}: {str(e)}")
            raise FetchError(f"Failed to fetch {url}: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error for {url}: {str(e)}")
            raise FetchError(f"Error processing {url}: {str(e)}")
        finally:
            sys.settrace(None)

class SearchManager:
    def __init__(self):
        self.webs = WEBS()
        self.fetcher = WebPageFetcher()
        
    def search(self, query: str, num_search: int = config.NUM_SEARCH) -> Dict[str, Any]:
        """
        Perform web search and fetch webpage contents.
        
        Args:
            query: Search query
            num_search: Number of results to fetch
            
        Returns:
            Dictionary of search results with parsed content
        """
        try:
            logger.info(f"🔍 Searching for: {query}")
            cache_key = get_cache_key(query)
            
            search_results = self.webs.text(
                query,
                max_results=num_search
            )
            
            if not search_results:
                logger.warning("⚠️ No search results found")
                return {}

            results = {}
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as executor:
                future_to_url = {
                    executor.submit(
                        self.fetcher.fetch_webpage,
                        result['href'],
                        config.SEARCH_TIME_LIMIT
                    ): result
                    for result in search_results
                    if 'href' in result
                }
                
                for future in as_completed(future_to_url):
                    result = future_to_url[future]
                    try:
                        url, page_text = future.result()
                        if page_text:
                            results[url] = {
                                'title': result.get('title', ''),
                                'abstract': result.get('body', ''),
                                'content': page_text
                            }
                    except FetchError as e:
                        logger.error(str(e))
                    except Exception as e:
                        logger.error(f"Unexpected error processing result: {str(e)}")

            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}")
            raise SearchError(f"Search failed: {str(e)}")

class LLMManager:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key="dummy",
            base_url="https://chatcfapi.r12.top/v1"
        )
        
    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError),
        max_tries=3
    )
    def check_search_needed(
        self,
        query: str,
        file_path: str,
        msg_history: Optional[List[Dict]] = None
    ) -> Optional[Dict]:
        """Check if query requires search and execute if needed."""
        prompt = """Decide if a user's query requires a Google search. You should use Google search for most queries to find the most accurate and updated information. Follow these conditions:

- If the query does not require Google search, you must output "ns", short for no search.
- If the query requires Google search, you must respond with a reformulated user query for Google search.
- User query may sometimes refer to previous messages. Make sure your Google search considers the entire message history.

User Query:
{query}
"""
        msg_history = msg_history or []
        new_msg_history = msg_history + [{"role": "user", "content": prompt.format(query=query)}]
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant whose primary goal is to decide if a user's query requires a Google search."},
                    *new_msg_history
                ],
                max_tokens=30
            )
            
            cleaned_response = response.choices[0].message.content.lower().strip()
            
            if re.fullmatch(r"\bns\b", cleaned_response):
                logger.info("No Google search required.")
                return None
                
            logger.info(f"Performing Google search: {cleaned_response}")
            search_manager = SearchManager()
            search_dic = search_manager.search(cleaned_response)
            
            # Format search results in markdown
            search_result_md = "\n".join(
                f"{number+1}. {link}"
                for number, link in enumerate(search_dic.keys())
            )
            
            with open(file_path, 'a') as file:
                file.write(f"## Sources\n{search_result_md}\n\n")
                
            return search_dic
            
        except Exception as e:
            logger.error(f"Error in search check: {str(e)}")
            return None

    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError),
        max_tries=3
    )
    def generate_response(
        self,
        query: str,
        file_path: str,
        msg_history: Optional[List[Dict]] = None,
        search_dic: Optional[Dict] = None,
    ) -> List[Dict]:
        """Generate response using the language model."""
        try:
            if search_dic:
                context_block = "\n".join([
                    f"[{i+1}]({url}): {content['content'][:config.MAX_CONTENT]}"
                    for i, (url, content) in enumerate(search_dic.items())
                ])
                prompt = """Provide a relevant, informative response to the user's query using the given context (search results with [citation number](website link) and brief descriptions).

- Answer directly without referring the user to any external links.
- Use an unbiased, journalistic tone and avoid repeating text.
- Format your response in markdown with bullet points for clarity.
- Cite all information using [citation number](website link) notation, matching each part of your answer to its source.

Context Block:
{context_block}

User Query:
{query}
"""
            else:
                prompt = """Please provide a helpful response to the following query:

User Query:
{query}
"""

            system_prompt = """You are a helpful assistant who is expert at answering user's queries"""

            msg_history = msg_history or []
            new_msg_history = msg_history + [{
                "role": "user",
                "content": prompt.format(
                    context_block=context_block,
                    query=query
                ) if search_dic else prompt.format(query=query)
            }]

            console.rule("[bold blue]LLM Response")
            
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *new_msg_history
                ],
                max_tokens=config.MAX_TOKENS,
                stream=True
            )

            content = []
            with open(file_path, 'a') as file:
                file.write(f"## Answer\n")
                
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    chunk_content = chunk.choices[0].delta.content
                    if chunk_content:
                        content.append(chunk_content)
                        console.print(chunk_content, end="")
                        with open(file_path, 'a') as file:
                            file.write(chunk_content)

            console.rule("[bold blue]End of Response")
            
            with open(file_path, 'a') as file:
                file.write("\n\n")
            
            full_content = ''.join(content)
            if not full_content.strip():
                error_msg = "⚠️ Warning: Empty response from LLM"
                logger.warning(error_msg)
                full_content = "I apologize, but I couldn't generate a response at this time. Please try again."
                with open(file_path, 'a') as file:
                    file.write(full_content + "\n\n")
            
            return new_msg_history + [{"role": "assistant", "content": full_content}]

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return msg_history

def main():
    """Main function with improved UI and error handling."""
    msg_history = None
    file_path = "playground.md"
    save_path = None
    
    # Initialize empty file
    Path(file_path).write_text("")
    
    llm_manager = LLMManager()
    
    console.print("[bold green]Welcome to WebScout![/bold green]")
    console.print("Enter your questions, or use commands:\n[bold]s[/bold] to save, [bold]q[/bold] to quit\n")

    while True:
        try:
            query = console.input("[bold blue]Enter your question: [/bold blue]")
            
            if query.lower() == "q":
                break
                
            if query.lower() == "s":
                if save_path:
                    shutil.copy(file_path, save_path)
                    console.print(f"[green]✓ Response saved to {save_path}[/green]")
                    save_path = None
                    Path(file_path).write_text("")
                else:
                    console.print("[yellow]! No content to save[/yellow]")
                continue
                
            with open(file_path, 'a') as file:
                file.write(f"# {query}\n\n")
                
            search_dic = llm_manager.check_search_needed(query, file_path, msg_history)
            msg_history = llm_manager.generate_response(query, file_path, msg_history, search_dic)
            
            save_path = save_path or f"{sanitize_filename(query)}.md"
            console.print(f"[green]✓ Response recorded in {file_path}[/green]")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            console.print("[red]An error occurred. Please try again.[/red]")
            
        console.rule()
        console.print("Enter your next question, or use [bold]s[/bold] to save, [bold]q[/bold] to quit")

if __name__ == "__main__":
    main()