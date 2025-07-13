"""Loan model for storing loan data from Kameo API."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, JSON, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .base import Base


class LoanStatus(str, Enum):
    """Enum for loan status values."""
    OPEN = "open"
    CLOSED = "closed"
    FUNDED = "funded"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"
    UNKNOWN = "unknown"


class Loan(Base):
    """
    SQLAlchemy model for storing loan data.
    
    Represents a loan from Kameo with all relevant fields for investment decisions.
    """
    __tablename__ = "loans"

    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Loan identification
    loan_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    
    # Loan details
    status = Column(String(20), nullable=False, default=LoanStatus.UNKNOWN.value)
    amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=True)
    
    # Dates
    open_date = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    
    # Progress and funding
    funding_progress = Column(Numeric(5, 2), nullable=True)  # Percentage
    funded_amount = Column(Numeric(15, 2), nullable=True)
    
    # URL and metadata
    url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Raw data storage for debugging
    raw_data = Column(JSON, nullable=True)
    
    # Tracking fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Additional fields that might be useful
    borrower_type = Column(String(100), nullable=True)
    loan_type = Column(String(100), nullable=True)
    risk_grade = Column(String(10), nullable=True)
    duration_months = Column(Integer, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Loan(id={self.loan_id}, title='{self.title}', status={self.status}, amount={self.amount})>"


class LoanCreate(BaseModel):
    """Pydantic model for creating new loans."""
    
    loan_id: str = Field(..., description="Unique identifier for the loan")
    title: str = Field(..., description="Title of the loan")
    status: LoanStatus = Field(default=LoanStatus.UNKNOWN, description="Current status of the loan")
    amount: Decimal = Field(..., description="Loan amount")
    interest_rate: Optional[Decimal] = Field(None, description="Annual interest rate")
    open_date: Optional[datetime] = Field(None, description="Date when loan opens for investment")
    close_date: Optional[datetime] = Field(None, description="Date when loan closes")
    funding_progress: Optional[Decimal] = Field(None, description="Funding progress percentage")
    funded_amount: Optional[Decimal] = Field(None, description="Amount already funded")
    url: Optional[str] = Field(None, description="URL to the loan page")
    description: Optional[str] = Field(None, description="Loan description")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw API response data")
    borrower_type: Optional[str] = Field(None, description="Type of borrower")
    loan_type: Optional[str] = Field(None, description="Type of loan")
    risk_grade: Optional[str] = Field(None, description="Risk grade or rating")
    duration_months: Optional[int] = Field(None, description="Loan duration in months")
    
    @field_validator('loan_id')
    @classmethod
    def validate_loan_id(cls, v: str) -> str:
        """Validate loan ID format."""
        if not v or not v.strip():
            raise ValueError("Loan ID cannot be empty")
        return v.strip()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate loan title."""
        if not v or not v.strip():
            raise ValueError("Loan title cannot be empty")
        return v.strip()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate loan amount."""
        if v <= 0:
            raise ValueError("Loan amount must be positive")
        return v
    
    @field_validator('interest_rate')
    @classmethod
    def validate_interest_rate(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate interest rate."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Interest rate must be between 0 and 100")
        return v
    
    @field_validator('funding_progress')
    @classmethod
    def validate_funding_progress(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate funding progress percentage."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Funding progress must be between 0 and 100")
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        from_attributes=True
    )


class LoanResponse(LoanCreate):
    """Pydantic model for loan responses including database fields."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        from_attributes=True
    ) 