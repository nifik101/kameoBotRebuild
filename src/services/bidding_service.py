#!/usr/bin/env python3
"""
Bidding Service - Handles all bidding operations for Kameo loans.

This service provides functionality to:
- Load bidding data for specific loans
- Place bids on loans
- Handle sequence hashes and payment options
- Manage rate limiting

Based on HAR analysis of actual bidding operations.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from ..config import KameoConfig
from ..utils.loan_validator import LoanValidator
from ..utils.constants import (
    LOAN_LISTINGS_ENDPOINT, BIDDING_LOAD_ENDPOINT,
    DEFAULT_LOAN_LIMIT, DEFAULT_BIDDING_MAX_PAGES,
    SWEDEN_CODE, NORWAY_CODE, DENMARK_CODE,
    DEFAULT_API_HEADERS, BIDDING_HEADERS,
    PAYMENT_OPTION_INTEREST, PAYMENT_OPTION_DOWN,
    HIGH_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD,
    RISK_LEVEL_HIGH, RISK_LEVEL_MEDIUM, RISK_LEVEL_LOW, RISK_LEVEL_UNKNOWN
)

logger = logging.getLogger(__name__)


@dataclass
class BiddingRequest:
    """Data class for bidding request parameters."""
    loan_id: int
    amount: int
    payment_option: str = PAYMENT_OPTION_INTEREST  # "ip" for interest payment, "dp" for down payment
    sequence_hash: str = ""


@dataclass
class BiddingResponse:
    """Data class for bidding response data."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    sequence_hash: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    error_message: Optional[str] = None


class BiddingService:
    """
    Service for handling all bidding operations on Kameo loans.
    
    This service is based on HAR analysis of actual bidding operations
    and handles the complete bidding workflow including sequence hashes.
    """
    
    def __init__(self, config: KameoConfig, loan_data_service=None) -> None:
        """
        Initialize the bidding service.
        
        Args:
            config: Kameo configuration object
            loan_data_service: Optional LoanDataService for loan data operations
        """
        self.config = config
        self.session = requests.Session()
        self._setup_session()
        
        # Use provided loan data service or create one
        if loan_data_service:
            self.loan_data_service = loan_data_service
        else:
            from .loan_data_service import LoanDataService
            self.loan_data_service = LoanDataService(config)
        
        logger.info("BiddingService initialized successfully")
    
    def _setup_session(self) -> None:
        """Setup the session with proper headers and authentication."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
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
    
    def get_loan_listings(self, limit: int = DEFAULT_LOAN_LIMIT, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Fetch available loans from Kameo's API using LoanDataService.
        
        Args:
            limit: Number of loans to fetch (default: 12)
            page: Page number (default: 1)
            
        Returns:
            JSON response with loan data or None on error
        """
        return self.loan_data_service.fetch_loan_listings(limit=limit, page=page)
    
    def load_bidding_data(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """
        Load bidding data for a specific loan using LoanDataService.
        
        Args:
            loan_id: ID of the loan
            
        Returns:
            Bidding data or None on error
        """
        return self.loan_data_service.fetch_bidding_data(loan_id)
    
    def place_bid(self, request: BiddingRequest) -> BiddingResponse:
        """
        Place a bid on a loan.
        
        Args:
            request: BiddingRequest object with bid parameters
            
        Returns:
            BiddingResponse with operation results
        """
        api_url = f"https://api.kameo.se/v1/bidding/{request.loan_id}/load"
        
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://www.kameo.se",
            "referer": "https://www.kameo.se/"
        }
        
        payload = {
            "amount": str(request.amount),
            "intention": "add",
            "sequence_hash": request.sequence_hash,
            "payment_options": [request.payment_option]
        }
        
        try:
            response = self.session.post(api_url, json=payload, headers=headers)
            
            # Check rate limiting
            rate_limit_remaining = response.headers.get('x-ratelimit-remaining')
            if rate_limit_remaining:
                logger.info(f"Rate limit remaining: {rate_limit_remaining}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract sequence hash from response if available
            sequence_hash = data.get('sequence_hash', '')
            
            logger.info(f"Successfully placed bid of {request.amount} SEK on loan {request.loan_id}")
            
            return BiddingResponse(
                success=True,
                data=data,
                sequence_hash=sequence_hash,
                rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing bid on loan {request.loan_id}: {e}")
            return BiddingResponse(
                success=False,
                error_message=str(e)
            )
    
    def get_available_loans(self, max_pages: int = DEFAULT_BIDDING_MAX_PAGES) -> List[Dict[str, Any]]:
        """
        Get all available loans for bidding using LoanDataService.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of loan dictionaries
        """
        return self.loan_data_service.get_all_loans(max_pages=max_pages)
    
    def analyze_loan_for_bidding(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a specific loan for bidding potential.
        
        Args:
            loan_id: ID of the loan to analyze
            
        Returns:
            Analysis results or None on error
        """
        try:
            # Get loan details
            loan_details = self.get_loan_listings(limit=100)
            if not loan_details:
                return None
            
            # Find the specific loan
            loans = loan_details.get('data', {}).get('loans', [])
            target_loan = None
            for loan in loans:
                if loan.get('id') == loan_id:
                    target_loan = loan
                    break
            
            if not target_loan:
                logger.error(f"Loan {loan_id} not found in available loans")
                return None
            
            # Load bidding data
            bidding_data = self.load_bidding_data(loan_id)
            
            # Perform analysis
            analysis = self._analyze_bidding_potential(target_loan, bidding_data)
            
            return {
                'loan_details': target_loan,
                'bidding_data': bidding_data,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing loan {loan_id}: {e}")
            return None
    
    def _analyze_bidding_potential(
        self, 
        loan_details: Dict[str, Any], 
        bidding_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze bidding potential for a loan.
        
        Args:
            loan_details: Loan information
            bidding_data: Bidding-specific data
            
        Returns:
            Analysis results
        """
        analysis: Dict[str, Any] = {
            'bidding_viable': False,
            'risk_level': RISK_LEVEL_UNKNOWN,
            'recommended_bid_amount': None,
            'notes': []
        }
        
        try:
            # Basic loan analysis
            amount = loan_details.get('amount', 0)
            interest_rate = loan_details.get('interest_rate', 0)
            status = loan_details.get('status', 'unknown')
            
            # Determine if bidding is viable
            if status.lower() in ['open', 'active'] and amount > 0:
                analysis['bidding_viable'] = True
            
            # Risk assessment using constants
            if interest_rate >= HIGH_RISK_THRESHOLD:
                analysis['risk_level'] = RISK_LEVEL_HIGH
            elif interest_rate >= MEDIUM_RISK_THRESHOLD:
                analysis['risk_level'] = RISK_LEVEL_MEDIUM
            elif interest_rate > 0:
                analysis['risk_level'] = RISK_LEVEL_LOW
            
            # Recommended bid amount (simple logic)
            if analysis['bidding_viable']:
                # Recommend 10% of loan amount, minimum 1000 SEK
                recommended = max(1000, int(amount * 0.1))
                analysis['recommended_bid_amount'] = recommended
            
            # Add notes
            if interest_rate > 0:
                analysis['notes'].append(f"Interest rate: {interest_rate}%")
            if amount > 0:
                analysis['notes'].append(f"Loan amount: {amount:,} SEK")
            
        except Exception as e:
            logger.error(f"Error in bidding analysis: {e}")
            analysis['notes'].append(f"Analysis error: {e}")
        
        return analysis
    
    def execute_bidding_strategy(self, loan_id: int, strategy: Dict[str, Any]) -> BiddingResponse:
        """
        Execute a bidding strategy for a loan.
        
        Args:
            loan_id: ID of the loan
            strategy: Bidding strategy parameters
            
        Returns:
            BiddingResponse with results
        """
        try:
            amount = strategy.get('amount', 0)
            payment_option = strategy.get('payment_option', PAYMENT_OPTION_INTEREST)
            
            # Validate bidding request using centralized validator
            is_valid, error_message = LoanValidator.validate_bidding_request(loan_id, amount, payment_option)
            if not is_valid:
                return BiddingResponse(
                    success=False,
                    error_message=error_message
                )
            
            request = BiddingRequest(
                loan_id=loan_id,
                amount=amount,
                payment_option=payment_option
            )
            
            return self.place_bid(request)
            
        except Exception as e:
            logger.error(f"Error executing bidding strategy: {e}")
            return BiddingResponse(
                success=False,
                error_message=str(e)
            ) 