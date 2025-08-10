"""
Service Factory - Centralized service creation and dependency injection.

This module provides factory functions for creating properly configured services
with their dependencies injected, following the dependency injection pattern
outlined in python-service-architecture.mdc.
"""

import logging
from typing import Optional

from src.config import KameoConfig
from src.services.bidding_service import BiddingService
from src.services.loan_collector import LoanCollectorService
from src.services.loan_repository import LoanRepository
from src.services.loan_operations_service import LoanOperationsService
from src.services.loan_data_service import LoanDataService
from src.services.http_client import get_http_client

logger = logging.getLogger(__name__)

# Global service instances for singleton pattern
_loan_operations_service: Optional[LoanOperationsService] = None
_config: Optional[KameoConfig] = None


def get_config() -> KameoConfig:
    """
    Get or create the global configuration instance.
    
    Returns:
        KameoConfig instance
    """
    global _config
    if _config is None:
        _config = KameoConfig()
        logger.info("Created global KameoConfig instance")
    return _config


def create_bidding_service(config: Optional[KameoConfig] = None, loan_data_service=None) -> BiddingService:
    """
    Create a BiddingService with proper configuration.
    
    Args:
        config: Optional KameoConfig instance, uses global if not provided
        loan_data_service: Optional LoanDataService instance
        
    Returns:
        Configured BiddingService instance
    """
    if config is None:
        config = get_config()
    
    return BiddingService(config, loan_data_service)


def create_loan_collector_service(
    config: Optional[KameoConfig] = None, 
    save_raw_data: bool = False,
    loan_data_service=None
) -> LoanCollectorService:
    """
    Create a LoanCollectorService with proper configuration.
    
    Args:
        config: Optional KameoConfig instance, uses global if not provided
        save_raw_data: Whether to save raw API responses for debugging
        loan_data_service: Optional LoanDataService instance
        
    Returns:
        Configured LoanCollectorService instance
    """
    if config is None:
        config = get_config()
    
    return LoanCollectorService(config, save_raw_data, loan_data_service)


def create_loan_repository() -> LoanRepository:
    """
    Create a LoanRepository instance.
    
    Returns:
        LoanRepository instance
    """
    return LoanRepository()


def create_loan_operations_service(
    config: Optional[KameoConfig] = None,
    save_raw_data: bool = False
) -> LoanOperationsService:
    """
    Create a LoanOperationsService with all dependencies properly injected.
    
    Args:
        config: Optional KameoConfig instance, uses global if not provided
        save_raw_data: Whether to save raw API responses for debugging
        
    Returns:
        Configured LoanOperationsService with injected dependencies
    """
    if config is None:
        config = get_config()
    
    # Create shared loan data service
    loan_data_service = LoanDataService(config)
    
    # Create all dependencies with shared loan_data_service
    bidding_service = create_bidding_service(config, loan_data_service)
    loan_service = create_loan_collector_service(config, save_raw_data, loan_data_service)
    loan_repository = create_loan_repository()
    
    # Inject dependencies into the service
    return LoanOperationsService(
        bidding_service=bidding_service,
        loan_service=loan_service,
        loan_repository=loan_repository
    )


def get_loan_operations_service(
    config: Optional[KameoConfig] = None,
    save_raw_data: bool = False,
    force_recreate: bool = False
) -> LoanOperationsService:
    """
    Get or create the global LoanOperationsService instance (singleton pattern).
    
    Args:
        config: Optional KameoConfig instance, uses global if not provided
        save_raw_data: Whether to save raw API responses for debugging
        force_recreate: Whether to force recreation of the service
        
    Returns:
        LoanOperationsService instance
    """
    global _loan_operations_service
    
    if _loan_operations_service is None or force_recreate:
        _loan_operations_service = create_loan_operations_service(config, save_raw_data)
        logger.info("Created global LoanOperationsService instance")
    
    return _loan_operations_service


def reset_services() -> None:
    """
    Reset all global service instances (useful for testing).
    """
    global _loan_operations_service, _config
    _loan_operations_service = None
    _config = None
    logger.info("Reset all global service instances") 