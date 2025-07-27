"""
Loan Operations Service - Unified service for loan and bidding operations.

This service consolidates all business logic that was previously scattered between
KameoBotCLI and various API endpoints. It provides a single point of access for
loan collection, analysis, and bidding operations.
"""

import logging
from typing import Dict, Any, List, Optional

from src.config import KameoConfig
from src.services.bidding_service import BiddingService, BiddingRequest
from src.services.loan_collector import LoanCollectorService
from src.services.loan_repository import LoanRepository

logger = logging.getLogger(__name__)


class LoanOperationsService:
    """
    Unified service for loan and bidding operations.
    
    This service consolidates all business logic that was previously scattered
    between KameoBotCLI and various API endpoints. It provides a single point
    of access for loan collection, analysis, and bidding operations.
    """
    
    def __init__(self, config: KameoConfig, save_raw_data: bool = False):
        """
        Initialize the loan operations service.
        
        Args:
            config: Kameo configuration object
            save_raw_data: Whether to save raw API responses for debugging
        """
        self.config = config
        self.save_raw_data = save_raw_data
        
        # Initialize underlying services
        self.bidding_service = BiddingService(config)
        self.loan_service = LoanCollectorService(config, save_raw_data)
        self.loan_repository = LoanRepository()
        
        logger.info("LoanOperationsService initialized successfully")
    
    # Loan Collection Operations
    
    def fetch_and_save_loans(self, max_pages: int = 10) -> Dict[str, Any]:
        """
        Fetch loans from Kameo and save them to the database.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            Dictionary with operation results and statistics
        """
        logger.info("Starting loan collection process...")
        
        try:
            raw_loans = self.loan_service.fetch_all_loans(max_pages=max_pages)
            
            if not raw_loans:
                logger.warning("No loans fetched from API")
                return {'status': 'no_loans', 'message': 'No loans found'}
            
            loan_objects = self.loan_service.convert_to_loan_objects(raw_loans)
            
            if not loan_objects:
                logger.warning("No valid loan objects created")
                return {'status': 'conversion_failed', 'message': 'Failed to convert loans'}
            
            save_results = self.loan_repository.save_loans(loan_objects)
            
            logger.info(f"Loan collection completed: {save_results}")
            
            return {
                'status': 'success',
                'raw_loans_count': len(raw_loans),
                'converted_loans_count': len(loan_objects),
                'save_results': save_results
            }
            
        except Exception as e:
            logger.error(f"Error in loan collection process: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_loan_fields(self) -> Dict[str, Any]:
        """
        Analyze all available fields from the API for debugging.
        
        Returns:
            Dictionary with field analysis results
        """
        logger.info("Starting field analysis...")
        
        try:
            analysis = self.loan_service.collect_and_save_all_fields()
            logger.info("Field analysis completed successfully")
            return analysis
        except Exception as e:
            logger.error(f"Error in field analysis: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_loan_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with loan statistics
        """
        logger.info("Retrieving database statistics...")
        
        try:
            stats = self.loan_repository.get_loan_statistics()
            logger.info("Statistics retrieved successfully")
            return stats
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {'status': 'error', 'message': str(e)}
    
    # Bidding Operations
    
    def list_available_loans(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        List available loans for bidding.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of available loans for bidding
        """
        logger.info("Fetching available loans...")
        
        try:
            loans = self.bidding_service.get_available_loans(max_pages=max_pages)
            logger.info(f"Found {len(loans)} loans")
            return loans
        except Exception as e:
            logger.error(f"Error listing loans: {e}")
            return []
    
    def analyze_loan_for_bidding(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a specific loan for bidding potential.
        
        Args:
            loan_id: ID of the loan to analyze
            
        Returns:
            Dictionary with loan analysis results, or None if analysis failed
        """
        logger.info(f"Analyzing loan {loan_id}...")
        
        try:
            analysis = self.bidding_service.analyze_loan_for_bidding(loan_id)
            logger.info(f"Analysis completed for loan {loan_id}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing loan {loan_id}: {e}")
            return None
    
    def place_bid(self, loan_id: int, amount: int, payment_option: str = "ip") -> Dict[str, Any]:
        """
        Place a bid on a loan.
        
        Args:
            loan_id: ID of the loan to bid on
            amount: Bid amount in SEK
            payment_option: Payment option ('ip' for interest payment, 'dp' for down payment)
            
        Returns:
            Dictionary with bid operation results
        """
        logger.info(f"Placing bid of {amount} SEK on loan {loan_id}...")
        
        try:
            request = BiddingRequest(
                loan_id=loan_id,
                amount=amount,
                payment_option=payment_option
            )
            
            response = self.bidding_service.place_bid(request)
            
            if response.success:
                logger.info(f"Bid placed successfully on loan {loan_id}")
            else:
                logger.error(f"Bid failed on loan {loan_id}: {response.error_message}")
            
            return {
                'success': response.success,
                'error_message': response.error_message,
                'sequence_hash': response.sequence_hash,
                'rate_limit_remaining': response.rate_limit_remaining
            }
            
        except Exception as e:
            logger.error(f"Error placing bid on loan {loan_id}: {e}")
            return {'success': False, 'error_message': str(e)}
    
    # Database Operations
    
    def get_loans_from_database(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get loans from database with pagination.
        
        Args:
            page: Page number (1-based)
            limit: Number of loans per page
            
        Returns:
            Dictionary with paginated loan data
        """
        try:
            # Get all loans using get_recent_loans with high limit
            all_loans = self.loan_repository.get_recent_loans(limit=10000)
            
            # Convert to dict format for JSON serialization
            loans_data = []
            for loan in all_loans:
                loan_dict = {
                    'id': loan.id,
                    'title': loan.title,
                    'amount': float(loan.amount) if loan.amount else None,
                    'interest_rate': float(loan.interest_rate) if loan.interest_rate else None,
                    'duration': loan.duration_months,
                    'risk_grade': loan.risk_grade,
                    'purpose': getattr(loan, 'purpose', None),
                    'borrower_name': getattr(loan, 'borrower_name', None),
                    'funded_percentage': float(loan.funding_progress) if loan.funding_progress else None,
                    'created_at': loan.created_at.isoformat() if loan.created_at else None,
                    'updated_at': loan.updated_at.isoformat() if loan.updated_at else None,
                }
                loans_data.append(loan_dict)
            
            # Apply pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_loans = loans_data[start_idx:end_idx]
            
            return {
                "loans": paginated_loans, 
                "total": len(loans_data), 
                "page": page, 
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting loans from database: {e}")
            return {"loans": [], "total": 0, "page": page, "limit": limit}
    
    # Demo Operations
    
    def run_demo(self) -> Dict[str, Any]:
        """
        Run a demonstration of the bidding functionality.
        
        Returns:
            Dictionary with demo results
        """
        logger.info("Starting demo...")
        
        demo_results: Dict[str, Any] = {
            'loans_found': 0,
            'loan_analysis': None,
            'demo_completed': True
        }
        
        try:
            # Demo 1: List available loans
            loans = self.list_available_loans(max_pages=1)
            demo_results['loans_found'] = len(loans)
            
            # Demo 2: Analyze a specific loan
            if loans:
                loan_id = loans[0].get('id')
                if loan_id is not None:
                    analysis = self.analyze_loan_for_bidding(loan_id)
                    demo_results['loan_analysis'] = analysis
            
            logger.info("Demo completed successfully")
            return demo_results
            
        except Exception as e:
            logger.error(f"Error running demo: {e}")
            demo_results['demo_completed'] = False
            demo_results['error'] = str(e)
            return demo_results 