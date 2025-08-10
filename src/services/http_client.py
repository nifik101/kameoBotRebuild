"""
Enhanced HTTP Client for Kameo API communication.

This module provides a centralized HTTP client that handles all communication
with Kameo's API, eliminating code duplication between services.
"""

import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import KameoConfig

logger = logging.getLogger(__name__)


class KameoHttpClient:
    """
    Enhanced centralized HTTP client for Kameo API communication.
    
    This client handles all HTTP requests to Kameo's API with proper
    error handling, retry logic, session management, and authentication.
    """
    
    def __init__(self, config: KameoConfig):
        """
        Initialize the HTTP client.
        
        Args:
            config: Kameo configuration object
        """
        self.config = config
        self.session = requests.Session()
        self._setup_session()
        
        logger.info("KameoHttpClient initialized successfully")
    
    def _setup_session(self) -> None:
        """Setup the session with proper headers, retry logic, and timeouts."""
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers for API requests
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'sv',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://www.kameo.se',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Sec-GPC': '1'
        })
        
        # Add authentication if available
        if hasattr(self.config, 'auth_token') and self.config.auth_token:
            self.session.headers['Authorization'] = f'Bearer {self.config.auth_token}'
    
    def authenticate(self) -> bool:
        """
        Authenticate with Kameo using the existing KameoClient logic.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from src.kameo_client import KameoClient
            
            # Create a temporary client for authentication
            client = KameoClient(self.config)
            
            # Perform login
            if not client.login():
                logger.error("Initial login failed")
                return False
            
            # Handle 2FA if needed
            if self.config.totp_secret:
                if not client.handle_2fa():
                    logger.error("2FA authentication failed")
                    return False
            
            # Copy session cookies and headers
            self.session.cookies.update(client.session.cookies)
            self.session.headers.update(client.session.headers)
            
            logger.info("Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        Make a GET request to the Kameo API.
        
        Args:
            url: URL to request
            params: Query parameters
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        try:
            response = self.session.get(url, params=params, timeout=timeout, **kwargs)
            response.raise_for_status()
            logger.debug(f"GET request successful: {url} -> {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {url} -> {e}")
            raise
    
    def post(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        Make a POST request to the Kameo API.
        
        Args:
            url: URL to request
            json: JSON data to send
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        try:
            response = self.session.post(url, json=json, timeout=timeout, **kwargs)
            response.raise_for_status()
            logger.debug(f"POST request successful: {url} -> {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {url} -> {e}")
            raise
    
    def update_headers(self, headers: Dict[str, str]) -> None:
        """
        Update session headers.
        
        Args:
            headers: Headers to add/update
        """
        self.session.headers.update(headers)
        logger.debug(f"Updated headers: {headers}")
    
    def update_cookies(self, cookies: Dict[str, str]) -> None:
        """
        Update session cookies.
        
        Args:
            cookies: Cookies to add/update
        """
        self.session.cookies.update(cookies)
        logger.debug(f"Updated cookies: {cookies}")
    
    def close(self) -> None:
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
        logger.info("KameoHttpClient closed")


# Global client instance for singleton pattern
_http_client: Optional[KameoHttpClient] = None


def get_http_client(config: KameoConfig) -> KameoHttpClient:
    """
    Get or create the global HTTP client instance.
    
    Args:
        config: Kameo configuration object
        
    Returns:
        KameoHttpClient instance
    """
    global _http_client
    if _http_client is None:
        _http_client = KameoHttpClient(config)
    return _http_client


def reset_http_client() -> None:
    """Reset the global HTTP client instance (useful for testing)."""
    global _http_client
    if _http_client:
        _http_client.close()
    _http_client = None
    logger.info("Reset global HTTP client instance")
