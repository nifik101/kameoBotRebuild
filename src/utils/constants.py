"""
Constants - Shared constants used across multiple services.

This module centralizes all constants that were previously duplicated
across different services.
"""

# API Endpoints
KAMEO_API_BASE = "https://api.kameo.se/v1"
LOAN_LISTINGS_ENDPOINT = f"{KAMEO_API_BASE}/loans/listing/investment-options"
LOAN_DETAILS_ENDPOINT = f"{KAMEO_API_BASE}/loans"
BIDDING_LOAD_ENDPOINT = f"{KAMEO_API_BASE}/bidding"

# Default API Parameters
DEFAULT_LOAN_LIMIT = 12
DEFAULT_MAX_PAGES = 10
DEFAULT_BIDDING_MAX_PAGES = 3

# Country Codes
SWEDEN_CODE = "1"
NORWAY_CODE = "0" 
DENMARK_CODE = "1"

# Payment Options
PAYMENT_OPTION_INTEREST = "ip"  # Interest payment
PAYMENT_OPTION_DOWN = "dp"      # Down payment

# HTTP Headers
DEFAULT_API_HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "sv",
    "origin": "https://www.kameo.se",
    "referer": "https://www.kameo.se/aktuella-lan"
}

BIDDING_HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://www.kameo.se",
    "referer": "https://www.kameo.se/"
}

# Validation Constants
MIN_LOAN_AMOUNT = 0
MAX_INTEREST_RATE = 100
MIN_INTEREST_RATE = 0
MIN_FUNDING_PROGRESS = 0
MAX_FUNDING_PROGRESS = 100

# Required Fields for Loan Validation
REQUIRED_LOAN_FIELDS = ['id', 'title', 'amount']

# Risk Levels
RISK_LEVEL_HIGH = "high"
RISK_LEVEL_MEDIUM = "medium" 
RISK_LEVEL_LOW = "low"
RISK_LEVEL_UNKNOWN = "unknown"

# Interest Rate Thresholds
HIGH_RISK_THRESHOLD = 8.0
MEDIUM_RISK_THRESHOLD = 6.0
