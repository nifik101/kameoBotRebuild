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
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.auth import KameoAuthenticator
from src.config import KameoConfig
from ..models.loan import LoanCreate, LoanStatus

logger = logging.getLogger(__name__)


class LoanCollectorService:
    """
    Service for collecting loan data from Kameo's API.
    
    This service handles the complete flow of authentication, API calls,
    and data processing to collect loan information from Kameo.
    """
    
    def __init__(self, config: KameoConfig, save_raw_data: bool = False) -> None:
        """
        Initialize the loan collector service.
        
        Args:
            config: Kameo configuration object
            save_raw_data: Whether to save raw API responses for debugging
        """
        self.config = config
        self.save_raw_data = save_raw_data
        self.session = requests.Session()
        self.authenticator = KameoAuthenticator(config.totp_secret) if config.totp_secret else None
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
            return []
    
    def fetch_all_loans(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch all available loans across multiple pages.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all loan data dictionaries
        """
        all_loans = []
        
        for page in range(1, max_pages + 1):
            try:
                loans = self.fetch_loans(page=page)
                if not loans:
                    logger.info(f"No more loans found on page {page}")
                    break
                
                all_loans.extend(loans)
                logger.info(f"Fetched {len(loans)} loans from page {page}")
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Total loans fetched: {len(all_loans)}")
        return all_loans
    
    def fetch_loan_details(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific loan.
        
        Args:
            loan_id: ID of the loan to fetch details for
            
        Returns:
            Loan details dictionary or None on error
        """
        if not self.is_authenticated:
            logger.warning("Not authenticated. Attempting to authenticate...")
            if not self.authenticate():
                return None
        
        api_url = f"https://api.kameo.se/v1/loans/{loan_id}"
        
        try:
            response = self._make_request('GET', api_url)
            data = response.json()
            
            # Save raw data if requested
            if self.save_raw_data:
                self._save_raw_data('loan_details', data, loan_id)
            
            logger.info(f"Successfully fetched details for loan {loan_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch details for loan {loan_id}: {e}")
            return None
    
    def convert_to_loan_objects(self, raw_loans: List[Dict[str, Any]]) -> List[LoanCreate]:
        """
        Convert raw loan data to LoanCreate objects.
        
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
                logger.error(f"Error converting loan {raw_loan.get('id', 'unknown')}: {e}")
        
        logger.info(f"Converted {len(loan_objects)} out of {len(raw_loans)} raw loans")
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
            # Extract basic fields
            loan_id = str(raw_loan.get('id', ''))
            title = raw_loan.get('title', '')
            amount_str = raw_loan.get('amount', '0')
            interest_rate_str = raw_loan.get('interest_rate', '0')
            
            # Convert amount to Decimal
            try:
                amount = Decimal(str(amount_str))
            except (ValueError, TypeError):
                amount = Decimal('0')
            
            # Convert interest rate to Decimal
            try:
                interest_rate = Decimal(str(interest_rate_str))
            except (ValueError, TypeError):
                interest_rate = None
            
            # Parse dates
            open_date = self._parse_date(raw_loan.get('open_date'))
            close_date = self._parse_date(raw_loan.get('close_date'))
            
            # Determine status
            status = self._determine_loan_status(raw_loan)
            
            # Extract additional fields
            funding_progress = raw_loan.get('funding_progress')
            if funding_progress is not None:
                try:
                    funding_progress = Decimal(str(funding_progress))
                except (ValueError, TypeError):
                    funding_progress = None
            
            funded_amount = raw_loan.get('funded_amount')
            if funded_amount is not None:
                try:
                    funded_amount = Decimal(str(funded_amount))
                except (ValueError, TypeError):
                    funded_amount = None
            
            # Create LoanCreate object
            loan_obj = LoanCreate(
                loan_id=loan_id,
                title=title,
                amount=amount,
                interest_rate=interest_rate,
                status=status,
                open_date=open_date,
                close_date=close_date,
                funding_progress=funding_progress,
                funded_amount=funded_amount,
                url=raw_loan.get('url'),
                description=raw_loan.get('description'),
                raw_data=raw_loan if self.save_raw_data else None,
                borrower_type=raw_loan.get('borrower_type'),
                loan_type=raw_loan.get('loan_type'),
                risk_grade=raw_loan.get('risk_grade'),
                duration_months=raw_loan.get('duration_months')
            )
            
            return loan_obj
            
        except Exception as e:
            logger.error(f"Error converting loan {raw_loan.get('id', 'unknown')}: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        # Try various date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _determine_loan_status(self, raw_loan: Dict[str, Any]) -> LoanStatus:
        """
        Determine loan status from raw data.
        
        Args:
            raw_loan: Raw loan dictionary
            
        Returns:
            LoanStatus enum value
        """
        status_str = raw_loan.get('status', '').lower()
        
        status_mapping = {
            'open': LoanStatus.OPEN,
            'closed': LoanStatus.CLOSED,
            'funded': LoanStatus.FUNDED,
            'active': LoanStatus.ACTIVE,
            'completed': LoanStatus.COMPLETED,
            'canceled': LoanStatus.CANCELED,
            'cancelled': LoanStatus.CANCELED
        }
        
        return status_mapping.get(status_str, LoanStatus.UNKNOWN)
    
    def _save_raw_data(self, data_type: str, data: Any, identifier: Any = None) -> None:
        """
        Save raw API data to file for debugging.
        Args:
            data_type: Type of data being saved
            data: Data to save
            identifier: Optional identifier for the data
        """
        try:
            import os
            cwd = str(Path.cwd())
            # Spara testdata i logs/debug om vi kör test, annars i data/raw
            if 'pytest' in cwd or 'test' in cwd:
                data_dir = Path('logs/debug')
            else:
                data_dir = Path('data/raw')
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if identifier:
                filename = f"{data_type}_{identifier}_{timestamp}.json"
            else:
                filename = f"{data_type}_{timestamp}.json"

            filepath = data_dir / filename

            # Save data as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.debug(f"Saved raw data to {filepath}")

        except Exception as e:
            logger.error(f"Error saving raw data: {e}")
    
    def collect_and_save_all_fields(self) -> Dict[str, Any]:
        """
        Collect and save all available fields from the API for analysis.
        
        Returns:
            Dictionary with field analysis results
        """
        logger.info("Starting field analysis...")
        
        try:
            # Fetch a few loans to analyze fields
            loans = self.fetch_loans(limit=5)
            
            if not loans:
                return {'error': 'No loans found for analysis'}
            
            # Analyze fields from all loans
            all_fields: set[str] = set()
            field_types: Dict[str, set[str]] = {}
            field_values: Dict[str, List[str]] = {}
            
            for loan in loans:
                for key, value in loan.items():
                    all_fields.add(key)
                    
                    # Track value types
                    value_type = type(value).__name__
                    if key not in field_types:
                        field_types[key] = set()
                    field_types[key].add(value_type)
                    
                    # Track sample values
                    if key not in field_values:
                        field_values[key] = []
                    if len(field_values[key]) < 3:  # Keep up to 3 sample values
                        field_values[key].append(str(value)[:100])  # Truncate long values
            
            # Save analysis results
            analysis: Dict[str, Any] = {
                'total_loans_analyzed': len(loans),
                'total_fields_found': len(all_fields),
                'fields': {}
            }
            
            for field in sorted(all_fields):
                analysis['fields'][field] = {
                    'types': list(field_types.get(field, [])),
                    'sample_values': field_values.get(field, [])
                }
            
            # Save analysis to file
            if self.save_raw_data:
                self._save_raw_data('field_analysis', analysis)
            
            logger.info(f"Field analysis complete: {len(all_fields)} fields found")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in field analysis: {e}")
            return {'error': str(e)}
    
    def close(self) -> None:
        """Close the service and clean up resources."""
        if self.session:
            self.session.close()
        logger.info("LoanCollectorService closed") 