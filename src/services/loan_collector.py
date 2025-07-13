"""
Loan collector service that fetches loans from Kameo's API.

This service uses the actual API endpoints discovered from HAR analysis to
fetch loan data from Kameo's investment options API.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.loan import LoanCreate, LoanStatus
from src.config import KameoConfig
from src.auth import KameoAuthenticator
from src.kameo_client import KameoClient

logger = logging.getLogger(__name__)


class LoanCollectorService:
    """
    Service for collecting loan data from Kameo's API.
    
    This service handles the complete flow of authentication, API calls,
    and data processing to collect loan information from Kameo.
    """
    
    def __init__(self, config: KameoConfig, save_raw_data: bool = False):
        """
        Initialize the loan collector service.
        
        Args:
            config: Kameo configuration object
            save_raw_data: Whether to save raw API responses for debugging
        """
        self.config = config
        self.save_raw_data = save_raw_data
        self.session = requests.Session()
        self.authenticator = KameoAuthenticator(config.totp_secret)
        self.is_authenticated = False
        
        # Setup session with retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'sv',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
        })
        
        logger.info(f"LoanCollectorService initialized for {config.email}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with proper error handling and logging.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            logger.debug(f"Request successful: {method} {url} -> {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} -> {e}")
            raise
    
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
            
            self.is_authenticated = True
            logger.info("Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def fetch_loans(
        self,
        limit: int = 12,
        page: int = 1,
        sweden: bool = True,
        norway: bool = False,
        denmark: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch loans from Kameo's investment options API.
        
        Args:
            limit: Maximum number of loans to fetch per page
            page: Page number to fetch
            sweden: Include Swedish loans
            norway: Include Norwegian loans  
            denmark: Include Danish loans
            
        Returns:
            List of loan data dictionaries
        """
        if not self.is_authenticated:
            logger.warning("Not authenticated. Attempting to authenticate...")
            if not self.authenticate():
                raise RuntimeError("Authentication failed")
        
        # Build API URL and parameters based on HAR analysis
        api_url = "https://api.kameo.se/v1/loans/listing/investment-options"
        params = {
            'subscription_origin_sweden': '1' if sweden else '0',
            'subscription_origin_norway': '1' if norway else '0',
            'subscription_origin_denmark': '1' if denmark else '0',
            'limit': str(limit),
            'page': str(page)
        }
        
        logger.info(f"Fetching loans: limit={limit}, page={page}, sweden={sweden}, norway={norway}, denmark={denmark}")
        
        try:
            response = self._make_request('GET', api_url, params=params)
            data = response.json()
            
            # Save raw data if requested
            if self.save_raw_data:
                self._save_raw_data('loans_listing', data, page)
            
            # Extract investment options. The API historically returned one of two shapes:
            # 1. {"data": {"investment_options": [ ... ]}}
            # 2. {"data": [ ... ]}
            # The unit-tests use the latter for simplicity, so we handle both cases here.

            investment_options_raw = data.get('data', [])

            if isinstance(investment_options_raw, list):
                investment_options = investment_options_raw
            elif isinstance(investment_options_raw, dict):
                investment_options = investment_options_raw.get('investment_options', [])
            else:
                investment_options = []

            logger.info(f"Successfully fetched {len(investment_options)} loans")
            return investment_options
            
        except Exception as e:
            logger.error(f"Failed to fetch loans: {e}")
            raise
    
    def fetch_all_loans(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch all available loans by paginating through the API.
        
        Args:
            max_pages: Maximum number of pages to fetch (safety limit)
            
        Returns:
            List of all loan data dictionaries
        """
        all_loans = []
        page = 1
        
        while page <= max_pages:
            loans = self.fetch_loans(page=page)
            
            if not loans:
                logger.info(f"No more loans found at page {page}")
                break
                
            all_loans.extend(loans)
            logger.info(f"Fetched {len(loans)} loans from page {page}, total: {len(all_loans)}")
            page += 1
        
        logger.info(f"Total loans fetched: {len(all_loans)}")
        return all_loans
    
    def fetch_loan_details(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information about a specific loan.
        
        Args:
            loan_id: The loan ID to fetch details for
            
        Returns:
            Loan details dictionary or None if not found
        """
        if not self.is_authenticated:
            logger.warning("Not authenticated. Attempting to authenticate...")
            if not self.authenticate():
                raise RuntimeError("Authentication failed")
        
        # URLs based on HAR analysis
        urls_to_try = [
            f"https://api.kameo.se/v1/q-a?loan_application_id={loan_id}",
            f"https://api.kameo.se/v1/bidding/{loan_id}/load",
        ]
        
        details = {}
        
        for url in urls_to_try:
            try:
                response = self._make_request('GET', url)
                data = response.json()
                
                # Extract endpoint name from URL for logging
                endpoint_name = url.split('/')[-1].split('?')[0]
                details[endpoint_name] = data
                
                logger.debug(f"Fetched {endpoint_name} data for loan {loan_id}")
                
            except Exception as e:
                logger.warning(f"Failed to fetch data from {url}: {e}")
                continue
        
        if self.save_raw_data:
            self._save_raw_data('loan_details', details, loan_id)
        
        return details if details else None
    
    def convert_to_loan_objects(self, raw_loans: List[Dict[str, Any]]) -> List[LoanCreate]:
        """
        Convert raw API loan data to LoanCreate objects.
        
        Args:
            raw_loans: List of raw loan dictionaries from API
            
        Returns:
            List of LoanCreate objects
        """
        loan_objects = []
        
        for raw_loan in raw_loans:
            try:
                loan_obj = self._convert_single_loan(raw_loan)
                if loan_obj:
                    loan_objects.append(loan_obj)
            except Exception as e:
                logger.error(f"Failed to convert loan {raw_loan.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully converted {len(loan_objects)} loans")
        return loan_objects
    
    def _convert_single_loan(self, raw_loan: Dict[str, Any]) -> Optional[LoanCreate]:
        """
        Convert a single raw loan dictionary to a LoanCreate object.
        
        Args:
            raw_loan: Raw loan dictionary from API
            
        Returns:
            LoanCreate object or None if conversion fails
        """
        try:
            # Extract basic loan information. Prefer new keys, but fall back to the
            # simplified keys that are used in the unit-tests.
            loan_id = str(
                raw_loan.get('loan_application_id')
                or raw_loan.get('id')
                or ''
            )
            title = raw_loan.get('title', '').strip()
            
            # Parse amount - use application_amount from API
            amount_str = (
                raw_loan.get('application_amount')
                or raw_loan.get('amount')
                or '0'
            )
            amount = Decimal(str(amount_str).replace(',', '.').replace(' ', ''))
            
            # Parse interest rate - use annual_interest_rate from API
            interest_rate = None
            if 'annual_interest_rate' in raw_loan or 'interest_rate' in raw_loan:
                interest_rate_raw = raw_loan.get('annual_interest_rate', raw_loan.get('interest_rate'))
                interest_rate = Decimal(str(interest_rate_raw).replace(',', '.').replace('%', ''))
            
            # Parse dates - map to actual API date fields
            open_date = self._parse_date(raw_loan.get('subscription_starts_at'))
            close_date = self._parse_date(raw_loan.get('subscription_ends_at'))
            
            # Parse funding progress - calculate from subscribed vs application amount
            funding_progress = None
            subscribed_amount = (
                raw_loan.get('subscribed_amount')
                or raw_loan.get('funded_amount')
                or 0
            )
            if amount > 0 and subscribed_amount > 0:
                funding_progress = Decimal((subscribed_amount / float(amount)) * 100)
            
            # Parse funded amount - use subscribed_amount from API
            funded_amount = None
            if 'subscribed_amount' in raw_loan or 'funded_amount' in raw_loan:
                funded_amount_raw = raw_loan.get('subscribed_amount', raw_loan.get('funded_amount'))
                funded_amount = Decimal(str(funded_amount_raw).replace(',', '.').replace(' ', ''))
            
            # Determine status
            status = self._determine_loan_status(raw_loan)
            
            # Build URL
            url = raw_loan.get('url') or f"https://www.kameo.se/listing/investment-option/{loan_id}"
            
            # Build and validate the Pydantic model. Any validation errors are
            # captured by the surrounding try/except so that they don't abort
            # the entire fetch cycle.
            return LoanCreate(
                loan_id=loan_id,
                title=title,
                status=status,
                amount=amount,
                interest_rate=interest_rate,
                open_date=open_date,
                close_date=close_date,
                funding_progress=funding_progress,
                funded_amount=funded_amount,
                url=url,
                description=raw_loan.get('description', ''),
                raw_data=raw_loan,
                borrower_type=raw_loan.get('borrower_type'),
                loan_type=raw_loan.get('loan_type'),
                risk_grade=raw_loan.get('risk_grade'),
                duration_months=raw_loan.get('duration_months')
            )
            
        except Exception as e:
            logger.error(f"Failed to convert loan data: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            logger.warning(f"Failed to parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None
    
    def _determine_loan_status(self, raw_loan: Dict[str, Any]) -> LoanStatus:
        """Determine loan status from raw data."""
        status_str = raw_loan.get('status', '').lower()
        
        status_mapping = {
            'open': LoanStatus.OPEN,
            'closed': LoanStatus.CLOSED,
            'funded': LoanStatus.FUNDED,
            'active': LoanStatus.ACTIVE,
            'completed': LoanStatus.COMPLETED,
            'canceled': LoanStatus.CANCELED,
            'cancelled': LoanStatus.CANCELED,
        }
        
        return status_mapping.get(status_str, LoanStatus.UNKNOWN)
    
    def _save_raw_data(self, data_type: str, data: Any, identifier: Any = None) -> None:
        """Save raw API data to file for debugging."""
        try:
            logs_dir = Path('logs/debug')
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{data_type}_{identifier}_{timestamp}.json" if identifier else f"{data_type}_{timestamp}.json"
            filepath = logs_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Saved raw data to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
    
    def collect_and_save_all_fields(self) -> Dict[str, Any]:
        """
        Collect all available loan data fields for testing and debugging.
        
        This method fetches loan data and analyzes all available fields
        to help understand the API response structure.
        
        Returns:
            Dictionary containing analysis of all fields found
        """
        logger.info("Collecting all loan data fields for analysis...")
        
        # Fetch loans
        loans = self.fetch_all_loans(max_pages=3)  # Limit for testing
        
        # Analyze all fields
        all_fields = set()
        field_examples = {}
        field_types = {}
        
        for loan in loans:
            for key, value in loan.items():
                all_fields.add(key)
                
                # Store example values
                if key not in field_examples:
                    field_examples[key] = value
                
                # Track field types
                field_type = type(value).__name__
                if key not in field_types:
                    field_types[key] = set()
                field_types[key].add(field_type)
        
        analysis = {
            'total_loans': len(loans),
            'all_fields': sorted(all_fields),
            'field_examples': field_examples,
            'field_types': {k: list(v) for k, v in field_types.items()},
            'sample_loans': loans[:3] if loans else []
        }
        
        # Save analysis
        if self.save_raw_data:
            self._save_raw_data('field_analysis', analysis)
        
        logger.info(f"Found {len(all_fields)} unique fields across {len(loans)} loans")
        return analysis
    
    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()
        logger.info("LoanCollectorService closed") 