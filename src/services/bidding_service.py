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

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import requests

from ..config import KameoConfig

logger = logging.getLogger(__name__)


@dataclass
class BiddingRequest:
    """Data class for bidding request parameters."""
    loan_id: int
    amount: int
    payment_option: str = "ip"  # "ip" for interest payment, "dp" for down payment
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
    
    def __init__(self, config: KameoConfig):
        """
        Initialize the bidding service.
        
        Args:
            config: Kameo configuration object
        """
        self.config = config
        self.session = requests.Session()
        self._setup_session()
        
        logger.info("BiddingService initialized successfully")
    
    def _setup_session(self):
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
    
    def get_loan_listings(self, limit: int = 12, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Fetch available loans from Kameo's API.
        
        Args:
            limit: Number of loans to fetch (default: 12)
            page: Page number (default: 1)
            
        Returns:
            JSON response with loan data or None on error
        """
        api_url = "https://api.kameo.se/v1/loans/listing/investment-options"
        
        params = {
            "subscription_origin_sweden": "1",
            "subscription_origin_norway": "0",
            "subscription_origin_denmark": "1",
            "limit": str(limit),
            "page": str(page)
        }
        
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "sv",
            "origin": "https://www.kameo.se",
            "referer": "https://www.kameo.se/aktuella-lan"
        }
        
        try:
            response = self.session.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched {len(data.get('data', {}).get('loans', []))} loans from page {page}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching loan listings: {e}")
            return None
    
    def load_bidding_data(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """
        Load bidding data for a specific loan.
        
        Args:
            loan_id: ID of the loan
            
        Returns:
            Bidding data or None on error
        """
        api_url = f"https://api.kameo.se/v1/bidding/{loan_id}/load"
        
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://www.kameo.se",
            "referer": "https://www.kameo.se/"
        }
        
        try:
            response = self.session.get(api_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Loaded bidding data for loan {loan_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error loading bidding data for loan {loan_id}: {e}")
            return None
    
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
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limit exceeded
                logger.error(f"Rate limit exceeded for loan {request.loan_id}")
                return BiddingResponse(
                    success=False,
                    error_message="Rate limit exceeded",
                    rate_limit_remaining=0
                )
            else:
                logger.error(f"HTTP error placing bid on loan {request.loan_id}: {e}")
                return BiddingResponse(
                    success=False,
                    error_message=f"HTTP error: {e}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error placing bid on loan {request.loan_id}: {e}")
            return BiddingResponse(
                success=False,
                error_message=str(e)
            )
    
    def get_available_loans(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Get all available loans across multiple pages.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all available loans
        """
        all_loans = []
        
        for page in range(1, max_pages + 1):
            loans_data = self.get_loan_listings(page=page)
            if not loans_data:
                break
                
            loans = loans_data.get('data', {}).get('loans', [])
            if not loans:
                break
                
            all_loans.extend(loans)
            logger.info(f"Fetched {len(loans)} loans from page {page}")
        
        logger.info(f"Total loans fetched: {len(all_loans)}")
        return all_loans
    
    def analyze_loan_for_bidding(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a loan for bidding potential.
        
        Args:
            loan_id: ID of the loan to analyze
            
        Returns:
            Complete loan analysis or None on error
        """
        # Get loan details from listings
        loans = self.get_available_loans(max_pages=1)
        loan_details = next((loan for loan in loans if loan.get('id') == loan_id), None)
        
        if not loan_details:
            logger.warning(f"Loan {loan_id} not found in available loans")
            return None
        
        # Get bidding data
        bidding_data = self.load_bidding_data(loan_id)
        
        return {
            "loan_id": loan_id,
            "loan_details": loan_details,
            "bidding_data": bidding_data,
            "analysis": self._analyze_bidding_potential(loan_details, bidding_data)
        }
    
    def _analyze_bidding_potential(self, loan_details: Dict[str, Any], 
                                 bidding_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the bidding potential of a loan.
        
        Args:
            loan_details: Loan details from listing
            bidding_data: Bidding data from API
            
        Returns:
            Analysis results
        """
        analysis: Dict[str, Any] = {
            "recommended_bid_amount": None,
            "risk_level": "unknown",
            "bidding_viable": False,
            "notes": []
        }
        
        if not bidding_data:
            analysis["notes"].append("No bidding data available")
            return analysis
        
        # Extract key metrics
        try:
            current_amount = bidding_data.get('current_amount', 0)
            target_amount = bidding_data.get('target_amount', 0)
            min_bid = bidding_data.get('min_bid_amount', 0)
            max_bid = bidding_data.get('max_bid_amount', 0)
            
            # Calculate bidding potential
            if target_amount > current_amount and min_bid > 0:
                analysis["bidding_viable"] = True
                analysis["recommended_bid_amount"] = min_bid
                
                # Risk assessment
                if current_amount / target_amount > 0.8:
                    analysis["risk_level"] = "high"
                    analysis["notes"].append("Loan nearly funded - high competition")
                elif current_amount / target_amount > 0.5:
                    analysis["risk_level"] = "medium"
                    analysis["notes"].append("Moderate funding progress")
                else:
                    analysis["risk_level"] = "low"
                    analysis["notes"].append("Early stage loan - lower competition")
            
        except Exception as e:
            analysis["notes"].append(f"Error analyzing bidding data: {e}")
        
        return analysis
    
    def execute_bidding_strategy(self, loan_id: int, strategy: Dict[str, Any]) -> BiddingResponse:
        """
        Execute a bidding strategy for a loan.
        
        Args:
            loan_id: ID of the loan
            strategy: Bidding strategy configuration
            
        Returns:
            BiddingResponse with results
        """
        # Load initial bidding data
        bidding_data = self.load_bidding_data(loan_id)
        if not bidding_data:
            return BiddingResponse(
                success=False,
                error_message="Could not load bidding data"
            )
        
        # Create bidding request
        request = BiddingRequest(
            loan_id=loan_id,
            amount=strategy.get('amount', 1000),
            payment_option=strategy.get('payment_option', 'ip'),
            sequence_hash=bidding_data.get('sequence_hash', '')
        )
        
        # Place the bid
        return self.place_bid(request) 