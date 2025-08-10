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

from src.auth import KameoAuthenticator
from src.config import KameoConfig
from src.utils.loan_validator import LoanValidator
from src.utils.constants import DEFAULT_MAX_PAGES
from ..models.loan import LoanCreate, LoanStatus

logger = logging.getLogger(__name__)


class LoanCollectorService:
    """
    Service for collecting loan data from Kameo's API.
    
    This service handles the complete flow of authentication, API calls,
    and data processing to collect loan information from Kameo.
    """
    
    def __init__(self, config: KameoConfig, save_raw_data: bool = False, loan_data_service=None) -> None:
        """
        Initialize the loan collector service.
        
        Args:
            config: Kameo configuration object
            save_raw_data: Whether to save raw API responses for debugging
            loan_data_service: Optional LoanDataService for API operations
        """
        self.config = config
        self.save_raw_data = save_raw_data
        self.authenticator = KameoAuthenticator(config.totp_secret) if config.totp_secret else None
        self.is_authenticated = False
        
        # Use provided loan data service or create one
        if loan_data_service:
            self.loan_data_service = loan_data_service
        else:
            from .loan_data_service import LoanDataService
            self.loan_data_service = LoanDataService(config)
        
        logger.info(f"LoanCollectorService initialized for {config.email}")
    
    def _make_request(self, method: str, url: str, **kwargs):
        """
        Make HTTP request using loan_data_service.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            Exception: If request fails
        """
        # This method is kept for compatibility but delegates to loan_data_service
        # In practice, we should use loan_data_service methods directly
        logger.warning("_make_request is deprecated, use loan_data_service methods directly")
        raise NotImplementedError("Use loan_data_service methods directly")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Kameo using the loan_data_service.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Use loan_data_service for authentication
            self.is_authenticated = self.loan_data_service.http_client.authenticate()
            if self.is_authenticated:
                logger.info("Authentication successful")
            return self.is_authenticated
            
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
        Fetch loans from Kameo's investment options API using loan_data_service.
        
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
        
        logger.info(f"Fetching loans: limit={limit}, page={page}, sweden={sweden}, norway={norway}, denmark={denmark}")
        
        try:
            data = self.loan_data_service.fetch_loan_listings(
                limit=limit, 
                page=page, 
                sweden=sweden, 
                norway=norway, 
                denmark=denmark
            )
            
            if not data:
                return []
            
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
    
    def fetch_all_loans(self, max_pages: int = DEFAULT_MAX_PAGES) -> List[Dict[str, Any]]:
        """
        Fetch all available loans across multiple pages using loan_data_service.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all loan data dictionaries
        """
        return self.loan_data_service.get_all_loans(max_pages=max_pages)
    
    def fetch_loan_details(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific loan using loan_data_service.
        
        Args:
            loan_id: ID of the loan to fetch details for
            
        Returns:
            Loan details dictionary or None on error
        """
        if not self.is_authenticated:
            logger.warning("Not authenticated. Attempting to authenticate...")
            if not self.authenticate():
                return None
        
        try:
            data = self.loan_data_service.fetch_loan_details(loan_id)
            
            # Save raw data if requested
            if self.save_raw_data and data:
                self._save_raw_data('loan_details', data, loan_id)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch details for loan {loan_id}: {e}")
            return None
    
    def validate_loan_data(self, raw_loan: Dict[str, Any]) -> bool:
        """
        Validate raw loan data before conversion using centralized validator.
        
        Args:
            raw_loan: Raw loan dictionary from API
            
        Returns:
            True if loan data is valid, False otherwise
        """
        return LoanValidator.validate_raw_loan(raw_loan)

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
                # Validate loan data before conversion
                if not self.validate_loan_data(raw_loan):
                    logger.warning(f"Skipping invalid loan data: {raw_loan.get('id', 'unknown')}")
                    continue
                    
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
        # Close loan_data_service if it has a close method
        if hasattr(self.loan_data_service, 'close'):
            self.loan_data_service.close()
        logger.info("LoanCollectorService closed") 