"""Data models for the loan collector system."""

from .loan import Loan, LoanStatus
from .base import Base

__all__ = ["Loan", "LoanStatus", "Base"] 