"""Kameo client for website interaction, login handling, and account number retrieval."""

import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv

# Import configuration and authenticator from src package
from src.auth import KameoAuthenticator
from src.config import KameoConfig
from pydantic import ValidationError

# Load environment variables from .env file.
# Pydantic-settings also loads, but this ensures they exist *before* Pydantic instantiation
# and that they override existing variables if override=True.
load_dotenv(override=True)

# Configure logging globally
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'  # Added filename/line number
)

logger = logging.getLogger(__name__)


class KameoClient:
    """Client for interacting with Kameo website, handling login and retrieving account number."""
    
    def __init__(self, config: KameoConfig) -> None:
        """
        Initialize the client with configuration and a session.

        Args:
            config: A KameoConfig object with necessary settings.
        """
        self.config = config
        self.session = requests.Session()
        self.authenticator: Optional[KameoAuthenticator] = None
        if config.totp_secret:
            self.authenticator = KameoAuthenticator(config.totp_secret)
        
        # Set User-Agent and Accept headers for the session
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        })
        
        # Set maximum number of redirects for the session
        self.session.max_redirects = config.max_redirects
        logger.info(f"KameoClient initialized for {config.email} on {config.base_url}")

    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Internal helper method for making HTTP requests with the session.
        Handles URL construction, timeouts and basic error handling.

        Args:
            method: HTTP method (e.g. 'GET', 'POST').
            path: Relative path for the request (e.g. '/user/login').
            **kwargs: Additional arguments to pass to requests.Session.request.

        Returns:
            A requests.Response object.

        Raises:
            requests.exceptions.RequestException: If the request fails for any reason.
        """
        full_url = self.config.get_full_url(path)
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        logger.debug(f"Making request: {method} {full_url}")  # Use debug level for detailed info
        try:
            response = self.session.request(
                method=method,
                url=full_url,
                timeout=timeout,
                allow_redirects=True,  # Default for session, but clarify
                **kwargs
            )
            # Raise exception for HTTP errors (status code 4xx or 5xx)
            response.raise_for_status() 
            logger.debug(f"Received response: {response.status_code} from {response.url}")
            return response
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout on request to {full_url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {full_url} failed: {e}")
            # Log response if available, can provide more info for e.g. 4xx/5xx errors
            if e.response is not None:
                logger.error(f"Error response status: {e.response.status_code}, content: {e.response.text[:500]}...")  # Log beginning of response
            raise

    def login(self) -> bool:
        """
        Perform the initial login step with username and password.

        Returns:
            True if login succeeded (led to 2FA page or dashboard), otherwise False.
        """
        login_path = '/user/login'
        logger.info(f"Starting login for {self.config.email}...")
        try:
            # Step 1: Get login page to get cookies and any CSRF token
            # Use _make_request which handles basic errors
            login_get_response = self._make_request('GET', login_path)
            
            # Try to extract CSRF token (even if it doesn't seem to be used in this flow, good to keep)
            soup = BeautifulSoup(login_get_response.text, 'html.parser')
            csrf_token: Optional[str] = None
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if isinstance(csrf_meta, Tag) and csrf_meta.has_attr('content'):
                token_value = csrf_meta.get('content')
                if isinstance(token_value, str):
                    csrf_token = token_value
                    logger.info(f"Found CSRF token: {csrf_token[:5]}...")  # Log only beginning
                
            # Step 2: Send login credentials
            payload = {
                'Login': self.config.email,
                'Password': self.config.password,
                'LoginButton': '',  # Name of submit button
                'RedirectURI': ''   # Doesn't seem to be used but sent along
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.config.get_full_url(login_path),
                'Origin': self.config.base_url  # Important header according to Postman analysis
            }
            
            # Add CSRF token to header if found (for future use?)
            if csrf_token:
                headers['X-CSRF-Token'] = csrf_token
            
            logger.info("Sending login credentials...")
            # Use session.request directly here since _make_request always follows redirects,
            # but we need to analyze the *immediate* response after POST.
            # We still need timeouts though.
            response = self.session.request(
                method='POST',
                url=self.config.get_full_url(login_path),
                data=payload,
                headers=headers,
                timeout=(self.config.connect_timeout, self.config.read_timeout),
                allow_redirects=True  # Follow redirects as normal after POST
            )
            response.raise_for_status()  # Check for HTTP errors
            
            logger.info(f"Response after login POST: Status={response.status_code}, URL={response.url}")
            
            # Check if we ended up on 2FA page or directly on dashboard
            if '/auth/2fa' in response.url:
                logger.info("Login succeeded, redirected to 2FA page.")
                return True
            elif '/investor/dashboard' in response.url:
                logger.info("Login succeeded, redirected directly to dashboard (2FA maybe not active?).")
                return True
            else:
                # Unexpected result, log and fail
                logger.error(f"Unexpected URL after login: {response.url}")
                logger.error(f"Response text (start): {response.text[:500]}...")
                return False
            
        except requests.exceptions.RequestException as e:
            # Errors are already logged in _make_request or in POST call above
            logger.error(f"Login process failed: {e}")
            return False

    def handle_2fa(self) -> bool:
        """
        Handle 2FA authentication with TOTP code according to the working Postman flow.
        Gets 2FA page, extracts token, and sends the code.

        Returns:
            True if 2FA authentication succeeded, otherwise False.
        """
        auth_path = '/auth/2fa'
        logger.info("Starting 2FA handling...")
        try:
            # Step 1: Get 2FA page to get a fresh ezxform_token
            logger.info(f"Getting {auth_path} to get 2FA form/token...")
            get_response = self._make_request('GET', auth_path)

            # Step 2: Extract ezxform_token from the form
            soup = BeautifulSoup(get_response.text, 'html.parser')
            form = soup.find('form', {'action': auth_path})
            if not isinstance(form, Tag):
                logger.error(f"Could not find 2FA form with action='{auth_path}' on page {get_response.url}")
                logger.debug(f"Page content (start): {get_response.text[:500]}...")
                return False

            token_input = form.find('input', {'name': 'ezxform_token'})
            ezxform_token: Optional[str] = None
            if isinstance(token_input, Tag) and token_input.has_attr('value'):
                token_value = token_input.get('value')
                if isinstance(token_value, str) and token_value:
                    ezxform_token = token_value
                    logger.info(f"Found ezxform_token: {ezxform_token}")
                else:
                    logger.warning("Found ezxform_token input but value is missing or not a string.")
            
            if not ezxform_token:
                logger.error("Could not extract a valid 'ezxform_token' from the 2FA form.")
                return False

            # Step 3: Generate standard TOTP code
            if not self.authenticator:
                logger.error("No authenticator available. Check TOTP secret in configuration.")
                return False
            code = self.authenticator.get_2fa_code()
            if not code:
                logger.error("Could not generate 2FA code. Check TOTP secret in configuration.")
                return False

            # Step 4: Send 2FA code and token
            payload = {
                'ezxform_token': ezxform_token,
                'code': code,
                'submit_code': ''  # Name of submit button ("Continue")
            }
            
            logger.info(f"Sending 2FA code ({code})...")
            response = self._make_request(
                method='POST',
                path=auth_path,
                data=payload,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': get_response.url,  # Referer from GET request
                    'Origin': self.config.base_url  # Important header
                }
            )
            
            logger.info(f"Response after 2FA POST: Status={response.status_code}, URL={response.url}")

            # Step 5: Check if authentication succeeded (if we're not still on 2FA page)
            if auth_path not in response.url:
                logger.info(f"2FA authentication succeeded with code {code}.")
                return True
            else:
                logger.error(f"2FA authentication failed with code {code}. Still on URL: {response.url}")
                # Try to find and log error message from page
                error_soup = BeautifulSoup(response.text, 'html.parser')
                # Look for common error message divs
                alert_danger = error_soup.find('div', class_='alert-danger') 
                if alert_danger and isinstance(alert_danger, Tag):
                    error_text = alert_danger.text.strip()
                    logger.error(f"Error message found on page: {error_text}")
                else:
                    logger.warning("No specific error message (alert-danger) found on 2FA page after failed attempt.")
                    logger.debug(f"Page content (start): {response.text[:500]}...")  # Log beginning for manual inspection
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"2FA handling failed: {e}")
            return False

    def get_account_number(self) -> Optional[str]:
        """
        Get the user's account number by first trying the API call,
        and falling back to HTML parsing if it fails.

        Returns:
            Account number as a string if found, otherwise None.
        """
        # Try first with API call
        api_account_number = self.get_account_number_from_api()
        if api_account_number:
            return api_account_number
        
        # If API fails, fall back to HTML parsing
        logger.warning("API call for account number failed, trying HTML parsing...")
        return self.get_account_number_from_html()

    def get_account_number_from_api(self) -> Optional[str]:
        """
        Get account number via Kameo's JSON API (primary method).

        Returns:
            Account number as a string if found, otherwise None.
        """
        api_path = '/ezjscore/call/kameo_transfer::init'
        logger.info("Trying to get account number via API...")
        try:
            response = self._make_request('GET', api_path)
            
            # Try to parse JSON response
            try:
                data = response.json()
                logger.debug(f"API response: {data}")
                
                # Navigate through JSON structure to find account number
                # Based on observed structure: content -> account_number
                if isinstance(data, dict) and 'content' in data:
                    content = data['content']
                    if isinstance(content, dict) and 'account_number' in content:
                        account_number = content['account_number']
                        if isinstance(account_number, str) and account_number.strip():
                            logger.info(f"Account number retrieved via API: {account_number}")
                            return account_number.strip()
                
                # If structure doesn't match expectation
                logger.warning("API response doesn't have expected structure for account number")
                logger.debug(f"Complete API response: {data}")
                return None
                
            except ValueError as e:
                logger.error(f"Could not parse API response as JSON: {e}")
                logger.debug(f"Raw API response: {response.text[:500]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API call for account number failed: {e}")
            return None

    def get_account_number_from_html(self) -> Optional[str]:
        """
        Get account number by parsing HTML from dashboard (fallback method).

        Returns:
            Account number as a string if found, otherwise None.
        """
        dashboard_path = '/investor/dashboard'
        logger.info("Trying to get account number via HTML parsing...")
        try:
            response = self._make_request('GET', dashboard_path)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find account number with CSS selector
            account_div = soup.select_one('.account-number')
            if account_div and isinstance(account_div, Tag):
                account_text = account_div.text.strip()
                if account_text:
                    logger.info(f"Account number retrieved via HTML: {account_text}")
                    return account_text
            
            # If CSS selector doesn't work, try with regex
            logger.warning("CSS selector for account number failed, trying regex...")
            account_match = re.search(r'kontonummer[:\s]*(\d+)', response.text, re.IGNORECASE)
            if account_match:
                account_number = account_match.group(1)
                logger.info(f"Account number retrieved via regex: {account_number}")
                return account_number
            
            logger.error("Could not find account number on dashboard page")
            # Save HTML for manual inspection (commented to avoid large logs)
            # with open('dashboard_debug.html', 'w', encoding='utf-8') as f:
            #     f.write(response.text)
            # logger.info("Dashboard HTML saved as 'dashboard_debug.html' for manual inspection")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Could not get dashboard for account number: {e}")
            return None


def load_configuration() -> Optional[KameoConfig]:
    """
    Load configuration from environment variables with error handling.

    Returns:
        A KameoConfig object if configuration is valid, otherwise None.
    """
    try:
        # KameoConfig requires email and password from environment variables
        # These should be set in .env file or environment
        config = KameoConfig()
        logger.info("Configuration loaded successfully.")
        return config
    except ValidationError as e:
        logger.error(f"Configuration error: {e}")
        # Show specific errors for each field
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            logger.error(f"  {field}: {message}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during configuration loading: {e}")
        return None


def main() -> None:
    """Main function to demonstrate KameoClient usage."""
    logger.info("Starting Kameo client...")
    
    # Load configuration
    config = load_configuration()
    if not config:
        logger.error("Could not load configuration. Aborting.")
        return

    # Create client and try to log in
    client = KameoClient(config)
    
    try:
        # Step 1: Log in
        if not client.login():
            logger.error("Login failed. Aborting.")
            return

        # Step 2: Handle 2FA (if necessary)
        # Check if we're on 2FA page
        current_response = client._make_request('GET', '/investor/dashboard')
        if '/user/login' in current_response.url or '/auth/2fa' in current_response.url:
            logger.info("2FA required...")
            if not client.handle_2fa():
                logger.error("2FA authentication failed. Aborting.")
                return

        # Step 3: Get account number
        account_number = client.get_account_number()
        if account_number:
            print(f"Account number: {account_number}")
            logger.info(f"Successfully retrieved account number: {account_number}")
        else:
            logger.error("Could not retrieve account number.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    
    logger.info("Kameo client finished.")


if __name__ == "__main__":
    main() 