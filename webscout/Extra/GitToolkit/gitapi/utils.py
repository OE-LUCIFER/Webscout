from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
from typing import Optional, Dict, Any
from webscout import LitAgent

class GitError(Exception):
    """Base exception for GitHub API errors"""
    pass

class RateLimitError(GitError):
    """Raised when hitting GitHub API rate limits"""
    pass

class NotFoundError(GitError):
    """Raised when resource is not found"""
    pass

class RequestError(GitError):
    """Raised for general request errors"""
    pass

_USER_AGENT_GENERATOR = LitAgent()

def request(url: str, retry_attempts: int = 3) -> Dict[str, Any]:
    """
    Send a request to GitHub API with retry mechanism
    
    Args:
        url: GitHub API endpoint URL
        retry_attempts: Number of retry attempts
        
    Returns:
        Parsed JSON response
        
    Raises:
        NotFoundError: If resource not found
        RateLimitError: If rate limited
        RequestError: For other request errors
    """
    headers = {
        "User-Agent": _USER_AGENT_GENERATOR.random(),
        "Accept": "application/vnd.github+json"
    }
    
    for attempt in range(retry_attempts):
        try:
            req = Request(url, headers=headers)
            response = urlopen(req)
            return json.loads(response.read().decode('utf-8'))
            
        except HTTPError as e:
            if e.code == 404:
                raise NotFoundError(f"Resource not found: {url}")
            if e.code == 429:
                raise RateLimitError(f"Rate limited on attempt {attempt + 1}")
            if attempt == retry_attempts - 1:
                raise RequestError(f"HTTP Error {e.code}: {e.reason}")
            
        except Exception as e:
            if attempt == retry_attempts - 1:
                raise RequestError(f"Request failed: {str(e)}")