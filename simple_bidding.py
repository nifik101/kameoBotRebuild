#!/usr/bin/env python3
"""
Simple Bidding Script - Demonstrates Kameo loan bidding functionality.

This script shows how to use the bidding service to:
- List available loans
- Analyze loans for bidding potential
- Place bids on loans

Based on HAR analysis of actual bidding operations.

Usage:
    python simple_bidding.py
"""

import json
import logging
import sys
from typing import Optional

from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import project modules
try:
    from src.config import KameoConfig
    from src.services.bidding_service import BiddingService, BiddingRequest
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def main() -> None:
    """Main function demonstrating bidding functionality."""
    print("🚀 Kameo Bidding Bot - Simple Demo")
    print("=" * 50)
    
    # Initialize configuration
    try:
        config = KameoConfig()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        print("Please ensure KAMEO_EMAIL and KAMEO_PASSWORD are set in .env file")
        return
    
    # Initialize bidding service
    try:
        bidding_service = BiddingService(config)
        print("✅ Bidding service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize bidding service: {e}")
        return
    
    # Demo 1: List available loans
    print("\n📋 Demo 1: Listing Available Loans")
    print("-" * 30)
    
    try:
        loans = bidding_service.get_available_loans(max_pages=1)
        
        if not loans:
            print("No loans found.")
        else:
            print(f"Found {len(loans)} loans:")
            for i, loan in enumerate(loans[:3], 1):  # Show first 3 loans
                loan_id = loan.get('id', 'N/A')
                title = loan.get('title', 'No title')[:50] + "..." if len(loan.get('title', '')) > 50 else loan.get('title', 'No title')
                amount = loan.get('amount', 0)
                
                print(f"  {i}. ID: {loan_id} | {title} | {amount:,} SEK")
    except Exception as e:
        print(f"❌ Error listing loans: {e}")
    
    # Demo 2: Analyze a specific loan (if available)
    print("\n🔍 Demo 2: Analyzing a Loan")
    print("-" * 30)
    
    try:
        loans = bidding_service.get_available_loans(max_pages=1)
        if loans:
            loan_id = loans[0].get('id')
            print(f"Analyzing loan ID: {loan_id}")
            
            analysis = bidding_service.analyze_loan_for_bidding(loan_id)
            
            if analysis:
                loan_details = analysis.get('loan_details', {})
                bidding_analysis = analysis.get('analysis', {})
                
                print(f"  Title: {loan_details.get('title', 'N/A')}")
                print(f"  Amount: {loan_details.get('amount', 0):,} SEK")
                print(f"  Bidding Viable: {'Yes' if bidding_analysis.get('bidding_viable') else 'No'}")
                print(f"  Risk Level: {bidding_analysis.get('risk_level', 'unknown')}")
                print(f"  Recommended Amount: {bidding_analysis.get('recommended_bid_amount', 'N/A')} SEK")
            else:
                print("  Could not analyze loan")
        else:
            print("  No loans available for analysis")
    except Exception as e:
        print(f"❌ Error analyzing loan: {e}")
    
    # Demo 3: Show bidding request structure
    print("\n💡 Demo 3: Bidding Request Structure")
    print("-" * 30)
    
    print("Based on HAR analysis, here's the bidding request structure:")
    print("""
    POST https://api.kameo.se/v1/bidding/{loan_id}/load
    
    Headers:
    - accept: "*/*"
    - content-type: "application/json"
    - origin: "https://www.kameo.se"
    - referer: "https://www.kameo.se/"
    
    Payload:
    {
        "amount": "3000",
        "intention": "add",
        "sequence_hash": "3bb02cf2620d7c64c7da5e944af2f1a0",
        "payment_options": ["ip"]  // or ["dp"] for down payment
    }
    """)
    
    # Demo 4: Rate limiting info
    print("\n⚡ Demo 4: Rate Limiting Information")
    print("-" * 30)
    
    print("From HAR analysis:")
    print("  - Rate limit: 60 requests")
    print("  - Remaining: 51-55 requests")
    print("  - Headers: x-ratelimit-limit, x-ratelimit-remaining")
    print("  - Status 429 when exceeded")
    
    print("\n✅ Demo completed successfully!")
    print("\nTo use the full bidding functionality:")
    print("1. Ensure you're logged in to Kameo")
    print("2. Use the bidding_service.place_bid() method")
    print("3. Handle sequence hashes properly")
    print("4. Monitor rate limits")


if __name__ == '__main__':
    main() 