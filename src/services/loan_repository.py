"""
Loan repository for database operations.

This module provides a repository pattern for loan data persistence,
handling all database operations for loans including CRUD operations
and duplicate detection.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.loan import Loan, LoanCreate, LoanResponse, LoanStatus
from ..database.connection import db_session_scope

logger = logging.getLogger(__name__)


class LoanRepository:
    """
    Repository for loan data operations.
    
    Provides methods for saving, retrieving, and managing loan data
    in the database with proper error handling and duplicate detection.
    """
    
    def save_loan(self, loan_data: LoanCreate) -> Optional[LoanResponse]:
        """
        Save a single loan to the database.
        
        Args:
            loan_data: LoanCreate object with loan information
            
        Returns:
            LoanResponse object if successful, None otherwise
        """
        try:
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
        results = {
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
            search_term: Term to search for
            
        Returns:
            List of LoanResponse objects
        """
        try:
            with db_session_scope() as session:
                loans = session.query(Loan).filter(
                    or_(
                        Loan.title.ilike(f'%{search_term}%'),
                        Loan.description.ilike(f'%{search_term}%')
                    )
                ).order_by(desc(Loan.created_at)).all()
                
                return [LoanResponse.from_orm(loan) for loan in loans]
                
        except Exception as e:
            logger.error(f"Failed to search loans: {e}")
            return []
    
    def get_loan_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loans in the database.
        
        Returns:
            Dictionary with various statistics
        """
        try:
            with db_session_scope() as session:
                stats = {}
                
                # Total loans
                stats['total_loans'] = session.query(Loan).count()
                
                # Loans by status
                status_counts = session.query(
                    Loan.status, func.count(Loan.id)
                ).group_by(Loan.status).all()
                
                stats['by_status'] = {status: count for status, count in status_counts}
                
                # Amount statistics
                amount_stats = session.query(
                    func.min(Loan.amount),
                    func.max(Loan.amount),
                    func.avg(Loan.amount),
                    func.sum(Loan.amount)
                ).first()
                
                if amount_stats[0] is not None:
                    stats['amount_stats'] = {
                        'min_amount': float(amount_stats[0]),
                        'max_amount': float(amount_stats[1]),
                        'avg_amount': float(amount_stats[2]),
                        'total_amount': float(amount_stats[3])
                    }
                
                # Recent activity
                recent_loans = session.query(Loan).order_by(
                    desc(Loan.created_at)
                ).limit(5).all()
                
                stats['recent_loans'] = [
                    {
                        'loan_id': loan.loan_id,
                        'title': loan.title,
                        'amount': float(loan.amount),
                        'status': loan.status,
                        'created_at': loan.created_at.isoformat()
                    }
                    for loan in recent_loans
                ]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get loan statistics: {e}")
            return {}
    
    def delete_loan(self, loan_id: str) -> bool:
        """
        Delete a loan from the database.
        
        Args:
            loan_id: The loan ID to delete
            
        Returns:
            True if successful, False otherwise
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
        Clean up old loans from the database.
        
        Args:
            days_old: Number of days to keep loans (older will be deleted)
            
        Returns:
            Number of loans deleted
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
                
                logger.info(f"Cleaned up {count} old loans")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old loans: {e}")
            return 0
    
    def _create_new_loan(self, session: Session, loan_data: LoanCreate) -> LoanResponse:
        """Create a new loan in the database."""
        try:
            # Handle status - could be enum or string
            status_value = loan_data.status.value if hasattr(loan_data.status, 'value') else str(loan_data.status)
            
            loan = Loan(
                loan_id=loan_data.loan_id,
                title=loan_data.title,
                status=status_value,
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
            session.flush()  # To get the ID
            
            logger.debug(f"Created new loan: {loan.loan_id}")
            return LoanResponse.from_orm(loan)
            
        except IntegrityError as e:
            logger.error(f"Integrity error creating loan {loan_data.loan_id}: {e}")
            session.rollback()
            raise
    
    def _update_existing_loan(
        self, 
        session: Session, 
        existing_loan: Loan, 
        loan_data: LoanCreate
    ) -> LoanResponse:
        """Update an existing loan in the database."""
        try:
            # Update fields
            existing_loan.title = loan_data.title
            # Handle status - could be enum or string
            existing_loan.status = loan_data.status.value if hasattr(loan_data.status, 'value') else str(loan_data.status)
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
            
            session.flush()
            
            logger.debug(f"Updated existing loan: {existing_loan.loan_id}")
            return LoanResponse.from_orm(existing_loan)
            
        except Exception as e:
            logger.error(f"Error updating loan {loan_data.loan_id}: {e}")
            session.rollback()
            raise 