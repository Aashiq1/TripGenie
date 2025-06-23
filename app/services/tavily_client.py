# app/services/tavily_client.py
"""Low-level Tavily API client for all search operations."""

import os
import requests
from typing import Dict, List, Optional

class TavilyClient:
    """Base client for Tavily API calls."""
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        self.base_url = "https://api.tavily.com/search"
    
    def search(self, 
               query: str, 
               max_results: int = 10,
               search_depth: str = "advanced",
               include_images: bool = False,
               include_answer: bool = True,
               include_domains: Optional[List[str]] = None,
               exclude_domains: Optional[List[str]] = None) -> Dict:
        """
        Execute a search query on Tavily.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced"
            include_images: Whether to include images
            include_answer: Whether to include AI-generated answer
            include_domains: List of domains to search within
            exclude_domains: List of domains to exclude
            
        Returns:
            Dict containing search results
            
        Raises:
            requests.RequestException: If API call fails
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_images": include_images,
            "include_answer": include_answer
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        try:
            response = requests.post(
                self.base_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception("Tavily API request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Tavily API error: {str(e)}")
    
    def search_with_retry(self, query: str, **kwargs) -> Optional[Dict]:
        """
        Search with automatic retry on failure.
        
        Args:
            query: Search query
            **kwargs: Additional arguments for search()
            
        Returns:
            Search results or None if all retries fail
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.search(query, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"All Tavily search attempts failed: {e}")
                    return None
                print(f"Tavily search attempt {attempt + 1} failed, retrying...")
        
        return None