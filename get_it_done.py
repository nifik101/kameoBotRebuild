from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup, Tag
import logging
import time
from typing import Optional
from urllib.parse import urljoin
from config import KameoConfig
from auth import KameoAuthenticator
from pydantic import ValidationError
import os

# Load environment variables from .env file
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KameoClient:
    def __init__(self, config: KameoConfig):
        self.config = config
        self.session = requests.Session()
        self.authenticator = KameoAuthenticator(config.totp_secret)
        
        # Configure session
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        })
        
        # Configure max redirects
        self.session.max_redirects = config.max_redirects

    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make a request with proper timeout and redirect handling"""
        url = self.config.get_full_url(path)
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        # Remove logic specific to allow_redirects kwarg for this call
        # Always use session's redirect handling and raise for status

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=timeout,
                allow_redirects=True, # Ensure this is True (session default)
                **kwargs
            )
            response.raise_for_status() # Always raise for status
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            raise

    def login(self) -> bool:
        """
        Perform initial login to Kameo
        Returns: True if login successful, False otherwise
        """
        try:
            # First get the login page to obtain session cookies
            login_response = self._make_request('GET', '/user/login')
            
            # Extract CSRF token if present
            soup = BeautifulSoup(login_response.text, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            csrf_token = None
            if csrf_meta and hasattr(csrf_meta, 'get'):
                csrf_token_value = csrf_meta.get('content')
                if isinstance(csrf_token_value, str):
                    csrf_token = csrf_token_value
            
            if csrf_token:
                logging.info(f"Found CSRF token: {csrf_token}")
            
            # Prepare login payload
            payload = {
                'Login': self.config.email,
                'Password': self.config.password,
                'LoginButton': '',
                'RedirectURI': ''
            }
            
            # Add CSRF token to headers if found
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.config.get_full_url('/user/login'),
                'Origin': self.config.base_url  # Add Origin header
            }
            
            if csrf_token:
                headers['X-CSRF-Token'] = csrf_token
            
            logging.info("Sending login request with credentials")
            response = self.session.request(
                method='POST',
                url=self.config.get_full_url('/user/login'),
                data=payload,
                headers=headers,
                timeout=(self.config.connect_timeout, self.config.read_timeout),
                allow_redirects=True
            )
            
            logging.info(f"Login response status: {response.status_code}, URL: {response.url}")
            
            # Check if we've been redirected to 2FA page
            if '/auth/2fa' in response.url:
                logging.info("Login successful, redirected to 2FA page")
                return True
            elif '/investor/dashboard' in response.url:
                logging.info("Login successful, redirected directly to dashboard")
                return True
            else:
                logging.error(f"Unexpected redirect after login: {response.url}")
                return False
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def handle_2fa(self) -> bool:
        """
        Handle 2FA authentication using TOTP, mimicking Postman flow.
        Returns: True if authentication successful, False otherwise
        """
        try:
            # 1. Get the 2FA page to get a fresh token
            get_response = self.session.request(
                method='GET',
                url=self.config.get_full_url('/auth/2fa'),
                timeout=(self.config.connect_timeout, self.config.read_timeout),
                allow_redirects=True
            )
            get_response.raise_for_status() # Ensure GET was successful
            logging.info(f"GET /auth/2fa status: {get_response.status_code}, URL: {get_response.url}")

            # Save the 2FA page HTML for debugging if needed
            # with open("2fa_page_pre_submit.html", "w", encoding="utf-8") as f:
            #     f.write(get_response.text)

            soup = BeautifulSoup(get_response.text, 'html.parser')
            
            # 2. Extract the ezxform_token
            form = soup.find('form', {'action': '/auth/2fa'})
            if not isinstance(form, Tag):
                logging.error("Could not find 2FA form with action='/auth/2fa'")
                return False

            token_input = form.find('input', {'name': 'ezxform_token'})
            
            # Check if token_input is a Tag and has a value attribute
            if not isinstance(token_input, Tag) or not token_input.has_attr('value'):
                logging.error("Could not find 'ezxform_token' input tag or its value in the 2FA form.")
                return False
            
            ezxform_token_value = token_input.get('value')
            if not isinstance(ezxform_token_value, str) or not ezxform_token_value:
                 logging.error("ezxform_token value is empty or not a string.")
                 return False
                 
            ezxform_token = ezxform_token_value
            logging.info(f"Found ezxform_token: {ezxform_token}")

            # 3. Generate *only* the standard TOTP code
            code = self.authenticator.get_2fa_code()
            if not code:
                logging.error("Failed to generate 2FA code (check secret)")
                return False

            # 4. Prepare and submit the 2FA code *once*
            payload = {
                'ezxform_token': ezxform_token,
                'code': code,
                'submit_code': '' # Ensure the submit button name is included
            }
            
            logging.info(f"Attempting 2FA submission with code: {code}")

            response = self.session.request(
                method='POST',
                url=self.config.get_full_url('/auth/2fa'),
                data=payload,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': get_response.url,
                    'Origin': self.config.base_url # Add Origin header
                },
                timeout=(self.config.connect_timeout, self.config.read_timeout),
                allow_redirects=True
            )
            response.raise_for_status() # Check for HTTP errors

            logging.info(f"POST /auth/2fa response status: {response.status_code}, URL: {response.url}")

            # Save the response for debugging
            # with open("2fa_submit_response.html", "w", encoding="utf-8") as f:
            #    f.write(response.text)

            # 5. Check if authentication was successful
            if '/auth/2fa' not in response.url:
                logging.info(f"Successfully authenticated with code {code}")
                # Optional: Save successful response HTML
                # with open("2fa_success.html", "w", encoding="utf-8") as f:
                #    f.write(response.text)
                return True
            else:
                logging.error(f"2FA authentication failed with code {code}. Still on 2FA page.")
                # Check for specific error messages on the page
                error_soup = BeautifulSoup(response.text, 'html.parser')
                alert_danger = error_soup.find('div', class_='alert-danger')
                if alert_danger:
                    logging.error(f"Error message found: {alert_danger.text.strip()}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"2FA handling failed with exception: {str(e)}")
            return False

    def get_account_number(self) -> Optional[str]:
        """
        Retrieve account number from dashboard
        Returns: Account number if found, None otherwise
        """
        try:
            logging.info("Attempting to get account number from dashboard")
            dashboard_url = self.config.get_full_url('/investor/dashboard')
            response = self.session.request(
                method='GET',
                url=dashboard_url,
                timeout=(self.config.connect_timeout, self.config.read_timeout),
                allow_redirects=True # Follow potential redirects after successful 2FA
            )
            response.raise_for_status()
            logging.info(f"Dashboard request URL: {response.url}, Status: {response.status_code}")
            
            # Save dashboard HTML for inspection
            try:
                with open("dashboard_final.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                logging.info("Saved final dashboard HTML to dashboard_final.html")
            except Exception as e:
                logging.error(f"Failed to save dashboard_final.html: {e}")

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if we're on the dashboard or redirected to login/2FA
            if '/auth/2fa' in response.url or '/user/login' in response.url:
                logging.error("Not on dashboard page - authentication failed")
                return None
            
            # Try to find account number on dashboard with multiple selectors
            selectors = [
                '.account-number',
                '.account-details .account-number',
                'span.account-number',
                'div.account-number',
                '.account span',
                '.account-id'
            ]
            
            for selector in selectors:
                account_number_elem = soup.select_one(selector)
                if account_number_elem:
                    account_number = account_number_elem.text.strip()
                    logging.info(f"Found account number on dashboard using selector '{selector}': {account_number}")
                    return account_number
            
            # If no selector worked, try to find patterns that look like account numbers
            logging.info("Trying to find account number patterns in page text")
            
            # Look for account number patterns (digits with possible formatting)
            account_patterns = [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 16 digits in groups of 4
                r'\b\d{7,10}\b',  # 7-10 digit number (common for account numbers)
                r'\b\d{4}[-\s]?\d{7,14}\b',  # Format with clearing number + account
            ]
            
            import re
            for pattern in account_patterns:
                for text in soup.stripped_strings:
                    match = re.search(pattern, text)
                    if match:
                        account_text = match.group(0)
                        logging.info(f"Found potential account number with pattern '{pattern}': {account_text}")
                        return account_text
            
            logging.error("Could not find account number on dashboard")
            return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get account number: {str(e)}")
            return None

def main():
    # Logging is configured globally above

    try:
        # Manually fetch required env vars after load_dotenv
        email = os.getenv("KAMEO_EMAIL")
        password = os.getenv("KAMEO_PASSWORD")
        totp_secret = os.getenv("KAMEO_TOTP_SECRET") # Optional
        base_url = os.getenv("KAMEO_BASE_URL") # Optional
        # ... fetch others if needed, or rely on defaults ...

        if not email or not password:
            logging.error("Missing required environment variables: KAMEO_EMAIL and KAMEO_PASSWORD")
            return
            
        # Pass required values directly, let Pydantic handle optionals/defaults
        config_data = {
            "email": email,
            "password": password,
        }
        if totp_secret:
             config_data["totp_secret"] = totp_secret
        if base_url:
             config_data["base_url"] = base_url
        # Add other optional vars if needed

        config = KameoConfig(**config_data)
        logging.info("Configuration loaded successfully.")

    except ValidationError as e:
        logging.error(f"Configuration error during manual loading: {e}")
        return
    except Exception as e: # Catch other potential errors
        logging.error(f"An unexpected error occurred during setup: {e}")
        return

    client = KameoClient(config)
    
    if not client.login():
        logging.error("Initial login step failed.")
        return
    
    # Attempt 2FA - Now crucial for proceeding
    if not client.handle_2fa():
        logging.error("2FA authentication failed.")
        return
    
    # Small delay might still be helpful after redirects
    time.sleep(1) 
    
    account_number = client.get_account_number()
    if account_number:
        print(f"Successfully retrieved account number: {account_number}")
    else:
        print("Failed to retrieve account number after successful login and 2FA.")

if __name__ == "__main__":
    main()