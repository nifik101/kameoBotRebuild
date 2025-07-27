#!/usr/bin/env python3
"""
Kameo Bot CLI - Command-line interface for Kameo operations.

Usage:
    python -m src.cli loans fetch          # Fetch and save loans
    python -m src.cli loans analyze        # Analyze loan fields
    python -m src.cli loans stats          # Show database statistics
    python -m src.cli bidding list         # List available loans
    python -m src.cli bidding analyze <id> # Analyze a specific loan
    python -m src.cli bidding bid <id> <amount> # Place a bid
    python -m src.cli demo                 # Run demo functionality
"""

import logging
import sys
from typing import Optional, Dict, Any, List

import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project modules
try:
    from src.config import KameoConfig
    from src.database.config import DatabaseConfig
    from src.database.connection import init_database
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/kameo_bot.log', mode='a')
        ]
    )


class KameoBotCLI:
    """Main CLI class that orchestrates all operations."""
    
    def __init__(self, debug: bool = False, save_raw_data: bool = False):
        """Initialize the CLI with configuration and services."""
        setup_logging(debug)
        self.logger = logging.getLogger(__name__)
        self.save_raw_data = save_raw_data
        
        # Load configurations
        self.kameo_config = self._load_kameo_config()
        self.db_config = self._load_database_config()
        
        if not self.kameo_config:
            raise RuntimeError("Failed to load Kameo configuration")
        
        # Initialize database
        self.db_manager = init_database(self.db_config)
        
        # Initialize unified service
        from src.services.loan_operations_service import LoanOperationsService
        self.loan_operations = LoanOperationsService(self.kameo_config, save_raw_data)
        
        self.logger.info("KameoBotCLI initialized successfully")
    
    def _load_kameo_config(self) -> Optional[KameoConfig]:
        """Load Kameo configuration from environment variables."""
        try:
            config = KameoConfig()
            self.logger.info("Kameo configuration loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load Kameo configuration: {e}")
            return None
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        try:
            config = DatabaseConfig()
            self.logger.info(f"Database configuration loaded: {config.db_url}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load database configuration: {e}")
            return DatabaseConfig()
    
    # Loan operations
    def fetch_loans(self, max_pages: int = 10) -> Dict[str, Any]:
        """Fetch loans from Kameo and save them to the database."""
        return self.loan_operations.fetch_and_save_loans(max_pages)
    
    def analyze_loan_fields(self) -> Dict[str, Any]:
        """Analyze all available fields from the API for debugging."""
        return self.loan_operations.analyze_loan_fields()
    
    def get_loan_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.loan_operations.get_loan_statistics()
    
    # Bidding operations
    def list_available_loans(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """List available loans for bidding."""
        return self.loan_operations.list_available_loans(max_pages)
    
    def analyze_loan_for_bidding(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """Analyze a specific loan for bidding potential."""
        return self.loan_operations.analyze_loan_for_bidding(loan_id)
    
    def place_bid(self, loan_id: int, amount: int, payment_option: str = "ip") -> Dict[str, Any]:
        """Place a bid on a loan."""
        return self.loan_operations.place_bid(loan_id, amount, payment_option)
    
    def run_demo(self) -> None:
        """Run a demonstration of the bidding functionality."""
        result = self.loan_operations.run_demo()
        
        print("🚀 Kameo Bidding Bot - Demo")
        print("=" * 50)
        
        if result.get('demo_completed'):
            print(f"✅ Demo completed successfully!")
            print(f"   Loans found: {result.get('loans_found', 0)}")
            if result.get('loan_analysis'):
                print(f"   Loan analysis: Available")
        else:
            print(f"❌ Demo failed: {result.get('error', 'Unknown error')}")


# CLI Commands
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--save-raw-data', is_flag=True, help='Save raw API responses for debugging')
@click.pass_context
def cli(ctx, debug, save_raw_data):
    """Kameo Bot CLI - Unified interface for Kameo operations."""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['save_raw_data'] = save_raw_data


@cli.group()
@click.pass_context
def loans(ctx):
    """Loan collection and analysis commands."""
    pass


@loans.command()
@click.option('--max-pages', default=10, help='Maximum number of pages to fetch')
@click.pass_context
def fetch(ctx, max_pages):
    """Fetch loans from Kameo and save to database."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        result = cli_instance.fetch_loans(max_pages)
        
        if result['status'] == 'success':
            click.echo(f"✅ Successfully fetched {result['converted_loans_count']} loans")
            click.echo(f"   Raw loans: {result['raw_loans_count']}")
            click.echo(f"   Save results: {result['save_results']}")
        else:
            click.echo(f"❌ Failed: {result['message']}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@loans.command()
@click.pass_context
def analyze(ctx):
    """Analyze all available loan fields."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        result = cli_instance.analyze_loan_fields()
        
        if result.get('status') != 'error':
            click.echo("✅ Field analysis completed successfully")
            click.echo(f"   Results saved to: {result.get('output_file', 'N/A')}")
        else:
            click.echo(f"❌ Failed: {result['message']}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@loans.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        stats = cli_instance.get_loan_statistics()
        
        if stats.get('status') != 'error':
            click.echo("📊 Database Statistics:")
            click.echo(f"   Total loans: {stats.get('total_loans', 0)}")
            click.echo(f"   Active loans: {stats.get('active_loans', 0)}")
            click.echo(f"   Total amount: {stats.get('total_amount', 0):,} SEK")
            click.echo(f"   Average interest rate: {stats.get('avg_interest_rate', 0):.2f}%")
        else:
            click.echo(f"❌ Failed: {stats['message']}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
@click.pass_context
def bidding(ctx):
    """Bidding operations commands."""
    pass


@bidding.command()
@click.option('--max-pages', default=3, help='Maximum number of pages to fetch')
@click.pass_context
def list(ctx, max_pages):
    """List available loans for bidding."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        loans = cli_instance.list_available_loans(max_pages)
        
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
        click.echo(f"❌ Error: {e}")


@bidding.command()
@click.argument('loan_id', type=int)
@click.pass_context
def analyze_loan(ctx, loan_id):
    """Analyze a specific loan for bidding potential."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        analysis = cli_instance.analyze_loan_for_bidding(loan_id)
        
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
        click.echo(f"❌ Error: {e}")


@bidding.command()
@click.argument('loan_id', type=int)
@click.argument('amount', type=int)
@click.option('--payment-option', default='ip', type=click.Choice(['ip', 'dp']), 
              help='Payment option: ip (interest payment) or dp (down payment)')
@click.pass_context
def bid(ctx, loan_id, amount, payment_option):
    """Place a bid on a loan."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        result = cli_instance.place_bid(loan_id, amount, payment_option)
        
        if result['success']:
            click.echo("✅ Bid placed successfully!")
            click.echo(f"   Amount: {amount:,} SEK")
            click.echo(f"   Payment Option: {payment_option.upper()}")
            if result.get('sequence_hash'):
                click.echo(f"   Sequence Hash: {result['sequence_hash']}")
            if result.get('rate_limit_remaining') is not None:
                click.echo(f"   Rate Limit Remaining: {result['rate_limit_remaining']}")
        else:
            click.echo(f"❌ Bid failed: {result['error_message']}")
            if result.get('rate_limit_remaining') == 0:
                click.echo("   Rate limit exceeded - please wait before trying again")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.pass_context
def demo(ctx):
    """Run a demonstration of the bidding functionality."""
    try:
        cli_instance = KameoBotCLI(ctx.obj['debug'], ctx.obj['save_raw_data'])
        cli_instance.run_demo()
    except Exception as e:
        click.echo(f"❌ Error: {e}")


if __name__ == '__main__':
    cli() 