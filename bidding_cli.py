#!/usr/bin/env python3
"""
Bidding CLI - Command-line interface for Kameo loan bidding operations.

This script provides a command-line interface for:
- Viewing available loans
- Analyzing loans for bidding potential
- Placing bids on loans
- Managing bidding strategies

Based on HAR analysis of actual bidding operations.

Usage:
    python bidding_cli.py list                    # List available loans
    python bidding_cli.py analyze <loan_id>       # Analyze a specific loan
    python bidding_cli.py bid <loan_id> <amount>  # Place a bid
    python bidding_cli.py strategy <loan_id>      # Execute bidding strategy
    python bidding_cli.py --help                  # Show help
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bidding.log', mode='a')
    ]
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


class BiddingCLI:
    """
    Command-line interface for bidding operations.
    
    This class provides a user-friendly interface for all bidding operations
    based on the HAR analysis of actual Kameo bidding workflows.
    """
    
    def __init__(self):
        """Initialize the bidding CLI."""
        self.config = self._load_config()
        if not self.config:
            raise RuntimeError("Failed to load configuration")
        
        self.bidding_service = BiddingService(self.config)
        logger.info("BiddingCLI initialized successfully")
    
    def _load_config(self) -> Optional[KameoConfig]:
        """Load Kameo configuration from environment variables."""
        try:
            # KameoConfig requires email and password from environment variables
            config = KameoConfig()
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.error("Please ensure KAMEO_EMAIL and KAMEO_PASSWORD are set in .env file")
            return None
    
    def list_loans(self, max_pages: int = 3) -> None:
        """
        List available loans.
        
        Args:
            max_pages: Maximum number of pages to fetch
        """
        logger.info("Fetching available loans...")
        
        try:
            loans = self.bidding_service.get_available_loans(max_pages=max_pages)
            
            if not loans:
                click.echo("No loans found.")
                return
            
            click.echo(f"\n📋 Available Loans ({len(loans)} total):")
            click.echo("=" * 80)
            
            for i, loan in enumerate(loans, 1):
                loan_id = loan.get('id', 'N/A')
                title = loan.get('title', 'No title')
                amount = loan.get('amount', 0)
                interest_rate = loan.get('interest_rate', 0)
                duration = loan.get('duration', 0)
                
                click.echo(f"{i:2d}. ID: {loan_id}")
                click.echo(f"    Title: {title}")
                click.echo(f"    Amount: {amount:,} SEK")
                click.echo(f"    Interest: {interest_rate}%")
                click.echo(f"    Duration: {duration} months")
                click.echo("-" * 40)
            
        except Exception as e:
            logger.error(f"Error listing loans: {e}")
            click.echo(f"❌ Error: {e}")
    
    def analyze_loan(self, loan_id: int) -> None:
        """
        Analyze a specific loan for bidding potential.
        
        Args:
            loan_id: ID of the loan to analyze
        """
        logger.info(f"Analyzing loan {loan_id}...")
        
        try:
            analysis = self.bidding_service.analyze_loan_for_bidding(loan_id)
            
            if not analysis:
                click.echo(f"❌ Could not analyze loan {loan_id}")
                return
            
            click.echo(f"\n🔍 Loan Analysis for ID {loan_id}:")
            click.echo("=" * 50)
            
            # Loan details
            loan_details = analysis.get('loan_details', {})
            if loan_details:
                click.echo("📋 Loan Details:")
                click.echo(f"   Title: {loan_details.get('title', 'N/A')}")
                click.echo(f"   Amount: {loan_details.get('amount', 0):,} SEK")
                click.echo(f"   Interest Rate: {loan_details.get('interest_rate', 0)}%")
                click.echo(f"   Duration: {loan_details.get('duration', 0)} months")
                click.echo()
            
            # Bidding analysis
            bidding_analysis = analysis.get('analysis', {})
            if bidding_analysis:
                click.echo("🎯 Bidding Analysis:")
                click.echo(f"   Viable for bidding: {'✅ Yes' if bidding_analysis.get('bidding_viable') else '❌ No'}")
                click.echo(f"   Risk Level: {bidding_analysis.get('risk_level', 'unknown').upper()}")
                click.echo(f"   Recommended Amount: {bidding_analysis.get('recommended_bid_amount', 'N/A')} SEK")
                
                notes = bidding_analysis.get('notes', [])
                if notes:
                    click.echo("   Notes:")
                    for note in notes:
                        click.echo(f"     • {note}")
            
        except Exception as e:
            logger.error(f"Error analyzing loan {loan_id}: {e}")
            click.echo(f"❌ Error: {e}")
    
    def place_bid(self, loan_id: int, amount: int, payment_option: str = "ip") -> None:
        """
        Place a bid on a loan.
        
        Args:
            loan_id: ID of the loan
            amount: Bid amount in SEK
            payment_option: "ip" (interest payment) or "dp" (down payment)
        """
        logger.info(f"Placing bid of {amount} SEK on loan {loan_id}...")
        
        try:
            # Create bidding request
            request = BiddingRequest(
                loan_id=loan_id,
                amount=amount,
                payment_option=payment_option
            )
            
            # Place the bid
            response = self.bidding_service.place_bid(request)
            
            if response.success:
                click.echo(f"✅ Bid placed successfully!")
                click.echo(f"   Amount: {amount:,} SEK")
                click.echo(f"   Payment Option: {payment_option.upper()}")
                if response.sequence_hash:
                    click.echo(f"   Sequence Hash: {response.sequence_hash}")
                if response.rate_limit_remaining is not None:
                    click.echo(f"   Rate Limit Remaining: {response.rate_limit_remaining}")
            else:
                click.echo(f"❌ Bid failed: {response.error_message}")
                if response.rate_limit_remaining == 0:
                    click.echo("   Rate limit exceeded - please wait before trying again")
            
        except Exception as e:
            logger.error(f"Error placing bid: {e}")
            click.echo(f"❌ Error: {e}")
    
    def execute_strategy(self, loan_id: int, strategy_name: str = "default") -> None:
        """
        Execute a bidding strategy for a loan.
        
        Args:
            loan_id: ID of the loan
            strategy_name: Name of the strategy to execute
        """
        logger.info(f"Executing {strategy_name} strategy for loan {loan_id}...")
        
        # Define strategies
        strategies = {
            "default": {
                "amount": 1000,
                "payment_option": "ip"
            },
            "aggressive": {
                "amount": 3000,
                "payment_option": "ip"
            },
            "conservative": {
                "amount": 500,
                "payment_option": "ip"
            }
        }
        
        strategy = strategies.get(strategy_name, strategies["default"])
        
        try:
            response = self.bidding_service.execute_bidding_strategy(loan_id, strategy)
            
            if response.success:
                click.echo(f"✅ Strategy '{strategy_name}' executed successfully!")
                click.echo(f"   Amount: {strategy['amount']:,} SEK")
                click.echo(f"   Payment Option: {strategy['payment_option'].upper()}")
            else:
                click.echo(f"❌ Strategy execution failed: {response.error_message}")
            
        except Exception as e:
            logger.error(f"Error executing strategy: {e}")
            click.echo(f"❌ Error: {e}")


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """Kameo Bidding CLI - Manage loan bidding operations."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.obj = BiddingCLI()


@cli.command()
@click.option('--max-pages', default=3, help='Maximum number of pages to fetch')
@click.pass_context
def list(ctx, max_pages):
    """List available loans."""
    ctx.obj.list_loans(max_pages=max_pages)


@cli.command()
@click.argument('loan_id', type=int)
@click.pass_context
def analyze(ctx, loan_id):
    """Analyze a specific loan for bidding potential."""
    ctx.obj.analyze_loan(loan_id)


@cli.command()
@click.argument('loan_id', type=int)
@click.argument('amount', type=int)
@click.option('--payment-option', default='ip', type=click.Choice(['ip', 'dp']), 
              help='Payment option: ip (interest payment) or dp (down payment)')
@click.pass_context
def bid(ctx, loan_id, amount, payment_option):
    """Place a bid on a loan."""
    ctx.obj.place_bid(loan_id, amount, payment_option)


@cli.command()
@click.argument('loan_id', type=int)
@click.option('--strategy', default='default', 
              type=click.Choice(['default', 'aggressive', 'conservative']),
              help='Bidding strategy to execute')
@click.pass_context
def strategy(ctx, loan_id, strategy):
    """Execute a bidding strategy for a loan."""
    ctx.obj.execute_strategy(loan_id, strategy)


if __name__ == '__main__':
    cli() 