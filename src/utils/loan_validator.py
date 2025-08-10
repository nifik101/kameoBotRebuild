"""
Loan Validator - Centralized validation utilities for loan data.

This module provides centralized validation logic that was previously
duplicated across multiple services.
"""

import logging
from typing import Dict, Any, Optional

from src.models.loan import LoanCreate

logger = logging.getLogger(__name__)


class LoanValidator:
    """
    Centralized validator for loan data.
    
    This class consolidates all loan validation logic that was previously
    duplicated across LoanCollectorService, LoanDataService, and LoanRepository.
    """
    
    @staticmethod
    def validate_raw_loan(raw_loan: Dict[str, Any]) -> bool:
        """
        Validate raw loan data from API before conversion.
        
        Args:
            raw_loan: Raw loan dictionary from API
            
        Returns:
            True if loan data is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['id', 'title', 'amount']
            for field in required_fields:
                if field not in raw_loan or not raw_loan[field]:
                    logger.warning(f"Missing required field '{field}' in loan data")
                    return False
            
            # Validate amount is numeric and positive
            try:
                amount = float(raw_loan['amount'])
                if amount <= 0:
                    logger.warning(f"Invalid amount {amount} for loan {raw_loan.get('id')}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Non-numeric amount {raw_loan['amount']} for loan {raw_loan.get('id')}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating raw loan data: {e}")
            return False
    
    @staticmethod
    def validate_loan_create(loan_data: LoanCreate) -> bool:
        """
        Validate LoanCreate object before saving to database.
        
        Args:
            loan_data: LoanCreate object to validate
            
        Returns:
            True if loan data is valid for saving, False otherwise
        """
        try:
            # Check required fields
            if not loan_data.loan_id or not str(loan_data.loan_id).strip():
                logger.warning("Loan ID is required")
                return False
            
            if not loan_data.title or not str(loan_data.title).strip():
                logger.warning("Loan title is required")
                return False
            
            if not loan_data.amount or float(loan_data.amount) <= 0:
                logger.warning("Loan amount must be positive")
                return False
            
            # Validate interest rate if provided
            if loan_data.interest_rate is not None:
                if float(loan_data.interest_rate) < 0 or float(loan_data.interest_rate) > 100:
                    logger.warning("Interest rate must be between 0 and 100")
                    return False
            
            # Validate funding progress if provided
            if loan_data.funding_progress is not None:
                if float(loan_data.funding_progress) < 0 or float(loan_data.funding_progress) > 100:
                    logger.warning("Funding progress must be between 0 and 100")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating LoanCreate data: {e}")
            return False
    
    @staticmethod
    def validate_bidding_request(loan_id: int, amount: int, payment_option: str) -> tuple[bool, Optional[str]]:
        """
        Validate bidding request parameters.
        
        Args:
            loan_id: ID of the loan to bid on
            amount: Bid amount in SEK
            payment_option: Payment option ('ip' or 'dp')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate loan ID
            if not loan_id or loan_id <= 0:
                return False, "Invalid loan ID"
            
            # Validate amount
            if not amount or amount <= 0:
                return False, "Bid amount must be positive"
            
            # Validate payment option
            if payment_option not in ['ip', 'dp']:
                return False, "Payment option must be 'ip' (interest payment) or 'dp' (down payment)"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating bidding request: {e}")
            return False, f"Validation error: {str(e)}"
