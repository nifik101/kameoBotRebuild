"""
Loan repository for database operations.

This module provides a repository pattern for loan data persistence,
handling all database operations for loans including CRUD operations
and duplicate detection.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database.connection import db_session_scope
from ..models.loan import Loan, LoanCreate, LoanResponse, LoanStatus

logger = logging.getLogger(__name__)


class LoanRepository:
    """
    Repository for loan data operations.
    
    Provides methods for saving, retrieving, and managing loan data
    in the database with proper error handling and duplicate detection.
    """
    
    def validate_loan_for_save(self, loan_data: LoanCreate) -> bool:
        """
        Validate loan data before saving to database.
        
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
            logger.error(f"Error validating loan data: {e}")
            return False

    def save_loan(self, loan_data: LoanCreate) -> Optional[LoanResponse]:
        """
        Save a single loan to the database.
        
        Args:
            loan_data: LoanCreate object with loan information
            
        Returns:
            LoanResponse object if successful, None otherwise
        """
        try:
            # Validate loan data before saving
            if not self.validate_loan_for_save(loan_data):
                logger.error(f"Loan data validation failed for {loan_data.loan_id}")
                return None
                
            with db_session_scope() as session:
                # Check if loan already exists
                existing_loan = session.query(Loan).filter(
                    Loan.loan_id == loan_data.loan_id
                ).first()
                
                if existing_loan:
                    # Update existing loan
                    return self._update_existing_loan(session, existing_loan, loan_data)
                else:
                    # Create new loan
                    return self._create_new_loan(session, loan_data)
                    
        except Exception as e:
            logger.error(f"Failed to save loan {loan_data.loan_id}: {e}")
            return None
    
    def save_loans(self, loans_data: List[LoanCreate]) -> Dict[str, Any]:
        """
        Save multiple loans to the database.
        
        Args:
            loans_data: List of LoanCreate objects
            
        Returns:
            Dictionary with save results and statistics
        """
        results: Dict[str, Any] = {
            'total_loans': len(loans_data),
            'saved_loans': 0,
            'updated_loans': 0,
            'failed_loans': 0,
            'errors': []
        }
        
        for loan_data in loans_data:
            try:
                result = self.save_loan(loan_data)
                if result:
                    # Check if this was an update or new loan
                    if result.created_at == result.updated_at:
                        results['saved_loans'] += 1
                    else:
                        results['updated_loans'] += 1
                else:
                    results['failed_loans'] += 1
                    
            except Exception as e:
                results['failed_loans'] += 1
                results['errors'].append(f"Failed to save loan {loan_data.loan_id}: {e}")
                logger.error(f"Failed to save loan {loan_data.loan_id}: {e}")
        
        logger.info(f"Batch save complete: {results['saved_loans']} saved, "
                   f"{results['updated_loans']} updated, {results['failed_loans']} failed")
        
        return results
    
    def get_loan_by_id(self, loan_id: str) -> Optional[LoanResponse]:
        """
        Retrieve a loan by its ID.
        
        Args:
            loan_id: The loan ID to search for
            
        Returns:
            LoanResponse object if found, None otherwise
        """
        try:
            with db_session_scope() as session:
                loan = session.query(Loan).filter(
                    Loan.loan_id == loan_id
                ).first()
                
                if loan:
                    return LoanResponse.from_orm(loan)
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve loan {loan_id}: {e}")
            return None
    
    def get_loans_by_status(self, status: LoanStatus) -> List[LoanResponse]:
        """
        Retrieve all loans with a specific status.
        
        Args:
            status: LoanStatus to filter by
            
        Returns:
            List of LoanResponse objects
        """
        try:
            with db_session_scope() as session:
                loans = session.query(Loan).filter(
                    Loan.status == status.value
                ).order_by(desc(Loan.created_at)).all()
                
                return [LoanResponse.from_orm(loan) for loan in loans]
                
        except Exception as e:
            logger.error(f"Failed to retrieve loans by status {status}: {e}")
            return []
    
    def get_recent_loans(self, limit: int = 50) -> List[LoanResponse]:
        """
        Retrieve the most recently added loans.
        
        Args:
            limit: Maximum number of loans to return
            
        Returns:
            List of LoanResponse objects
        """
        try:
            with db_session_scope() as session:
                loans = session.query(Loan).order_by(
                    desc(Loan.created_at)
                ).limit(limit).all()
                
                return [LoanResponse.from_orm(loan) for loan in loans]
                
        except Exception as e:
            logger.error(f"Failed to retrieve recent loans: {e}")
            return []
    
    def get_loans_by_amount_range(
        self, 
        min_amount: float, 
        max_amount: float
    ) -> List[LoanResponse]:
        """
        Retrieve loans within a specific amount range.
        
        Args:
            min_amount: Minimum loan amount
            max_amount: Maximum loan amount
            
        Returns:
            List of LoanResponse objects
        """
        try:
            with db_session_scope() as session:
                loans = session.query(Loan).filter(
                    and_(
                        Loan.amount >= min_amount,
                        Loan.amount <= max_amount
                    )
                ).order_by(desc(Loan.created_at)).all()
                
                return [LoanResponse.from_orm(loan) for loan in loans]
                
        except Exception as e:
            logger.error(f"Failed to retrieve loans by amount range: {e}")
            return []
    
    def search_loans(self, search_term: str) -> List[LoanResponse]:
        """
        Search loans by title or description.
        
        Args:
            search_term: Search term to look for
            
        Returns:
            List of LoanResponse objects matching the search
        """
        try:
            with db_session_scope() as session:
                search_pattern = f"%{search_term}%"
                loans = session.query(Loan).filter(
                    or_(
                        Loan.title.ilike(search_pattern),
                        Loan.description.ilike(search_pattern)
                    )
                ).order_by(desc(Loan.created_at)).all()
                
                return [LoanResponse.from_orm(loan) for loan in loans]
                
        except Exception as e:
            logger.error(f"Failed to search loans: {e}")
            return []
    
    def get_loan_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about loans in the database.
        
        Returns:
            Dictionary with various loan statistics
        """
        try:
            with db_session_scope() as session:
                # Basic counts
                total_loans = session.query(func.count(Loan.id)).scalar()
                open_loans = session.query(func.count(Loan.id)).filter(
                    Loan.status == LoanStatus.OPEN.value
                ).scalar()
                closed_loans = session.query(func.count(Loan.id)).filter(
                    Loan.status == LoanStatus.CLOSED.value
                ).scalar()
                funded_loans = session.query(func.count(Loan.id)).filter(
                    Loan.status == LoanStatus.FUNDED.value
                ).scalar()
                
                # Amount statistics
                total_amount = session.query(func.sum(Loan.amount)).scalar() or 0
                avg_amount = session.query(func.avg(Loan.amount)).scalar() or 0
                min_amount = session.query(func.min(Loan.amount)).scalar() or 0
                max_amount = session.query(func.max(Loan.amount)).scalar() or 0
                
                # Date statistics
                oldest_loan = session.query(Loan).order_by(Loan.created_at).first()
                newest_loan = session.query(Loan).order_by(desc(Loan.created_at)).first()
                
                # Interest rate statistics
                avg_interest_rate = session.query(func.avg(Loan.interest_rate)).scalar() or 0
                
                stats = {
                    'total_loans': total_loans,
                    'open_loans': open_loans,
                    'closed_loans': closed_loans,
                    'funded_loans': funded_loans,
                    'total_amount': float(total_amount),
                    'average_amount': float(avg_amount),
                    'min_amount': float(min_amount),
                    'max_amount': float(max_amount),
                    'average_interest_rate': float(avg_interest_rate),
                    'oldest_loan_date': oldest_loan.created_at if oldest_loan else None,
                    'newest_loan_date': newest_loan.created_at if newest_loan else None,
                    'last_updated': datetime.now().isoformat()
                }
                
                logger.info(f"Retrieved statistics: {total_loans} total loans")
                return stats
                
        except Exception as e:
            logger.error(f"Failed to retrieve loan statistics: {e}")
            return {'error': str(e)}
    
    def delete_loan(self, loan_id: str) -> bool:
        """
        Delete a loan from the database.
        
        Args:
            loan_id: ID of the loan to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            with db_session_scope() as session:
                loan = session.query(Loan).filter(
                    Loan.loan_id == loan_id
                ).first()
                
                if loan:
                    session.delete(loan)
                    logger.info(f"Deleted loan {loan_id}")
                    return True
                else:
                    logger.warning(f"Loan {loan_id} not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete loan {loan_id}: {e}")
            return False
    
    def cleanup_old_loans(self, days_old: int = 30) -> int:
        """
        Remove loans older than specified number of days.
        
        Args:
            days_old: Minimum age in days for loans to be removed
            
        Returns:
            Number of loans removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with db_session_scope() as session:
                old_loans = session.query(Loan).filter(
                    Loan.created_at < cutoff_date
                ).all()
                
                count = len(old_loans)
                for loan in old_loans:
                    session.delete(loan)
                
                logger.info(f"Cleaned up {count} loans older than {days_old} days")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old loans: {e}")
            return 0
    
    def _create_new_loan(self, session: Session, loan_data: LoanCreate) -> LoanResponse:
        """
        Create a new loan in the database.
        
        Args:
            session: Database session
            loan_data: Loan data to create
            
        Returns:
            LoanResponse object for the created loan
        """
        try:
            # Convert LoanCreate to Loan model
            loan = Loan(
                loan_id=loan_data.loan_id,
                title=loan_data.title,
                status=loan_data.status.value,
                amount=loan_data.amount,
                interest_rate=loan_data.interest_rate,
                open_date=loan_data.open_date,
                close_date=loan_data.close_date,
                funding_progress=loan_data.funding_progress,
                funded_amount=loan_data.funded_amount,
                url=loan_data.url,
                description=loan_data.description,
                raw_data=loan_data.raw_data,
                borrower_type=loan_data.borrower_type,
                loan_type=loan_data.loan_type,
                risk_grade=loan_data.risk_grade,
                duration_months=loan_data.duration_months
            )
            
            session.add(loan)
            session.flush()  # Get the ID
            
            logger.info(f"Created new loan {loan_data.loan_id}")
            return LoanResponse.from_orm(loan)
            
        except IntegrityError as e:
            logger.error(f"Integrity error creating loan {loan_data.loan_id}: {e}")
            session.rollback()
            raise
        except Exception as e:
            logger.error(f"Error creating loan {loan_data.loan_id}: {e}")
            session.rollback()
            raise
    
    def _update_existing_loan(
        self, 
        session: Session, 
        existing_loan: Loan, 
        loan_data: LoanCreate
    ) -> LoanResponse:
        """
        Update an existing loan in the database.
        
        Args:
            session: Database session
            existing_loan: Existing loan object
            loan_data: New loan data
            
        Returns:
            LoanResponse object for the updated loan
        """
        try:
            # Update fields
            existing_loan.title = loan_data.title
            existing_loan.status = loan_data.status.value
            existing_loan.amount = loan_data.amount
            existing_loan.interest_rate = loan_data.interest_rate
            existing_loan.open_date = loan_data.open_date
            existing_loan.close_date = loan_data.close_date
            existing_loan.funding_progress = loan_data.funding_progress
            existing_loan.funded_amount = loan_data.funded_amount
            existing_loan.url = loan_data.url
            existing_loan.description = loan_data.description
            existing_loan.raw_data = loan_data.raw_data
            existing_loan.borrower_type = loan_data.borrower_type
            existing_loan.loan_type = loan_data.loan_type
            existing_loan.risk_grade = loan_data.risk_grade
            existing_loan.duration_months = loan_data.duration_months
            existing_loan.updated_at = datetime.now()
            
            logger.info(f"Updated existing loan {loan_data.loan_id}")
            return LoanResponse.from_orm(existing_loan)
            
        except Exception as e:
            logger.error(f"Error updating loan {loan_data.loan_id}: {e}")
            session.rollback()
            raise 