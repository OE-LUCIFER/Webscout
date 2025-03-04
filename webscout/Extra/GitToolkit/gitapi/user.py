from typing import List, Dict, Any
from .utils import request

class User:
    """Class for interacting with GitHub user data"""
    
    def __init__(self, username: str):
        """
        Initialize user client
        
        Args:
            username: GitHub username
        """
        self.username = username
        self.base_url = f"https://api.github.com/users/{username}"

    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        return request(self.base_url)

    def get_repositories(self, page: int = 1, per_page: int = 30, type: str = "all") -> List[Dict[str, Any]]:
        """
        Get user's public repositories
        
        Args:
            page: Page number
            per_page: Items per page
            type: Type of repositories (all/owner/member)
        """
        url = f"{self.base_url}/repos?page={page}&per_page={per_page}&type={type}"
        return request(url)

    def get_starred(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get repositories starred by user"""
        url = f"{self.base_url}/starred?page={page}&per_page={per_page}"
        return request(url)

    def get_followers(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's followers"""
        url = f"{self.base_url}/followers?page={page}&per_page={per_page}"
        return request(url)

    def get_following(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get users followed by this user"""
        url = f"{self.base_url}/following?page={page}&per_page={per_page}"
        return request(url)

    def get_gists(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's public gists"""
        url = f"{self.base_url}/gists?page={page}&per_page={per_page}"
        return request(url)

    def get_organizations(self) -> List[Dict[str, Any]]:
        """Get user's organizations"""
        url = f"{self.base_url}/orgs"
        return request(url)

    def get_received_events(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get events received by user"""
        url = f"{self.base_url}/received_events?page={page}&per_page={per_page}"
        return request(url)

    def get_public_events(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's public events"""
        url = f"{self.base_url}/events/public?page={page}&per_page={per_page}"
        return request(url)

    def get_starred_gists(self) -> List[Dict[str, Any]]:
        """Get gists starred by user"""
        url = f"{self.base_url}/starred_gists"
        return request(url)

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Get repositories user is watching"""
        url = f"{self.base_url}/subscriptions"
        return request(url)

    def get_hovercard(self) -> Dict[str, Any]:
        """Get user's hovercard information"""
        url = f"{self.base_url}/hovercard"
        return request(url)

    def get_installation(self) -> Dict[str, Any]:
        """Get user's GitHub App installations"""
        url = f"{self.base_url}/installation"
        return request(url)

    def get_keys(self) -> List[Dict[str, Any]]:
        """Get user's public SSH keys"""
        url = f"{self.base_url}/keys"
        return request(url)

    def get_gpg_keys(self) -> List[Dict[str, Any]]:
        """Get user's public GPG keys"""
        url = f"{self.base_url}/gpg_keys"
        return request(url)
