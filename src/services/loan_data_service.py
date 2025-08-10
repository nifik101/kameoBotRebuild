"""
Loan Data Service - Centralized loan data operations.

This service handles all loan data fetching and processing operations,
eliminating duplication between loan_collector and bidding_service.
"""

import logging
from typing import Any, Dict, List, Optional

from src.config import KameoConfig
from src.services.http_client import get_http_client
from src.utils.loan_validator import LoanValidator
from src.utils.constants import (
    LOAN_LISTINGS_ENDPOINT, LOAN_DETAILS_ENDPOINT, BIDDING_LOAD_ENDPOINT,
    DEFAULT_LOAN_LIMIT, DEFAULT_MAX_PAGES, DEFAULT_BIDDING_MAX_PAGES,
    SWEDEN_CODE, NORWAY_CODE, DENMARK_CODE,
    DEFAULT_API_HEADERS, BIDDING_HEADERS,
    REQUIRED_LOAN_FIELDS, MIN_LOAN_AMOUNT
)

logger = logging.getLogger(__name__)


class LoanDataService:
    """
    Service for handling all loan data operations.
    
    This service centralizes loan data fetching and processing,
    eliminating duplication between different services.
    """
    
    def __init__(self, config: KameoConfig):
        """
        Initialize the loan data service.
        
        Args:
            config: Kameo configuration object
        """
        self.config = config
        self.http_client = get_http_client(config)
        
        logger.info("LoanDataService initialized successfully")
    
    def fetch_loan_listings(
        self, 
        limit: int = DEFAULT_LOAN_LIMIT, 
        page: int = 1,
        sweden: bool = True,
        norway: bool = False,
        denmark: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch loan listings from Kameo's API.
        
        Args:
            limit: Number of loans to fetch
            page: Page number
            sweden: Include Swedish loans
            norway: Include Norwegian loans
            denmark: Include Danish loans
            
        Returns:
            JSON response with loan data or None on error
        """
        params = {
            "subscription_origin_sweden": SWEDEN_CODE if sweden else NORWAY_CODE,
            "subscription_origin_norway": SWEDEN_CODE if norway else NORWAY_CODE,
            "subscription_origin_denmark": DENMARK_CODE if denmark else NORWAY_CODE,
            "limit": str(limit),
            "page": str(page)
        }
        
        try:
            response = self.http_client.get(LOAN_LISTINGS_ENDPOINT, params=params, headers=DEFAULT_API_HEADERS)
            data = response.json()
            
            # Extract investment options
            investment_options_raw = data.get('data', [])
            
            if isinstance(investment_options_raw, list):
                investment_options = investment_options_raw
            elif isinstance(investment_options_raw, dict):
                investment_options = investment_options_raw.get('investment_options', [])
            else:
                investment_options = []
            
            logger.info(f"Fetched {len(investment_options)} loans from page {page}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching loan listings: {e}")
            return None
    
    def fetch_loan_details(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific loan.
        
        Args:
            loan_id: ID of the loan to fetch details for
            
        Returns:
            Loan details dictionary or None on error
        """
        api_url = f"{LOAN_DETAILS_ENDPOINT}/{loan_id}"
        
        try:
            response = self.http_client.get(api_url)
            data = response.json()
            
            logger.info(f"Successfully fetched details for loan {loan_id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch details for loan {loan_id}: {e}")
            return None
    
    def fetch_bidding_data(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """
        Load bidding data for a specific loan.
        
        Args:
            loan_id: ID of the loan
            
        Returns:
            Bidding data or None on error
        """
        api_url = f"{BIDDING_LOAD_ENDPOINT}/{loan_id}/load"
        
        try:
            response = self.http_client.get(api_url, headers=BIDDING_HEADERS)
            data = response.json()
            
            logger.info(f"Loaded bidding data for loan {loan_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading bidding data for loan {loan_id}: {e}")
            return None
    
    def get_all_loans(self, max_pages: int = DEFAULT_MAX_PAGES) -> List[Dict[str, Any]]:
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
                data = self.fetch_loan_listings(page=page)
                if not data:
                    logger.info(f"No more loans found on page {page}")
                    break
                
                # Extract loans from response
                investment_options_raw = data.get('data', [])
                if isinstance(investment_options_raw, list):
                    loans = investment_options_raw
                elif isinstance(investment_options_raw, dict):
                    loans = investment_options_raw.get('investment_options', [])
                else:
                    loans = []
                
                if not loans:
                    logger.info(f"No loans found on page {page}")
                    break
                
                all_loans.extend(loans)
                logger.info(f"Fetched {len(loans)} loans from page {page}")
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Total loans fetched: {len(all_loans)}")
        return all_loans
    
    def validate_loan_data(self, raw_loan: Dict[str, Any]) -> bool:
        """
        Validate raw loan data using centralized validator.
        
        Args:
            raw_loan: Raw loan dictionary from API
            
        Returns:
            True if loan data is valid, False otherwise
        """
        return LoanValidator.validate_raw_loan(raw_loan)
