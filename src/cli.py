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
    from src.services.bidding_service import BiddingService, BiddingRequest
    from src.services.loan_collector import LoanCollectorService
    from src.services.loan_repository import LoanRepository
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
        
        # Initialize services
        self.bidding_service = BiddingService(self.kameo_config)
        self.loan_service = LoanCollectorService(self.kameo_config, save_raw_data)
        self.loan_repository = LoanRepository()
        
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
        self.logger.info("Starting loan collection process...")
        
        try:
            raw_loans = self.loan_service.fetch_all_loans(max_pages=max_pages)
            
            if not raw_loans:
                self.logger.warning("No loans fetched from API")
                return {'status': 'no_loans', 'message': 'No loans found'}
            
            loan_objects = self.loan_service.convert_to_loan_objects(raw_loans)
            
            if not loan_objects:
                self.logger.warning("No valid loan objects created")
                return {'status': 'conversion_failed', 'message': 'Failed to convert loans'}
            
            save_results = self.loan_repository.save_loans(loan_objects)
            
            self.logger.info(f"Loan collection completed: {save_results}")
            
            return {
                'status': 'success',
                'raw_loans_count': len(raw_loans),
                'converted_loans_count': len(loan_objects),
                'save_results': save_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in loan collection process: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_loan_fields(self) -> Dict[str, Any]:
        """Analyze all available fields from the API for debugging."""
        self.logger.info("Starting field analysis...")
        
        try:
            analysis = self.loan_service.collect_and_save_all_fields()
            self.logger.info("Field analysis completed successfully")
            return analysis
        except Exception as e:
            self.logger.error(f"Error in field analysis: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_loan_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        self.logger.info("Retrieving database statistics...")
        
        try:
            stats = self.loan_repository.get_loan_statistics()
            self.logger.info("Statistics retrieved successfully")
            return stats
        except Exception as e:
            self.logger.error(f"Error retrieving statistics: {e}")
            return {'status': 'error', 'message': str(e)}
    
    # Bidding operations
    def list_available_loans(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """List available loans for bidding."""
        self.logger.info("Fetching available loans...")
        
        try:
            loans = self.bidding_service.get_available_loans(max_pages=max_pages)
            self.logger.info(f"Found {len(loans)} loans")
            return loans
        except Exception as e:
            self.logger.error(f"Error listing loans: {e}")
            return []
    
    def analyze_loan_for_bidding(self, loan_id: int) -> Optional[Dict[str, Any]]:
        """Analyze a specific loan for bidding potential."""
        self.logger.info(f"Analyzing loan {loan_id}...")
        
        try:
            analysis = self.bidding_service.analyze_loan_for_bidding(loan_id)
            self.logger.info(f"Analysis completed for loan {loan_id}")
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing loan {loan_id}: {e}")
            return None
    
    def place_bid(self, loan_id: int, amount: int, payment_option: str = "ip") -> Dict[str, Any]:
        """Place a bid on a loan."""
        self.logger.info(f"Placing bid of {amount} SEK on loan {loan_id}...")
        
        try:
            request = BiddingRequest(
                loan_id=loan_id,
                amount=amount,
                payment_option=payment_option
            )
            
            response = self.bidding_service.place_bid(request)
            
            if response.success:
                self.logger.info(f"Bid placed successfully on loan {loan_id}")
            else:
                self.logger.error(f"Bid failed on loan {loan_id}: {response.error_message}")
            
            return {
                'success': response.success,
                'error_message': response.error_message,
                'sequence_hash': response.sequence_hash,
                'rate_limit_remaining': response.rate_limit_remaining
            }
            
        except Exception as e:
            self.logger.error(f"Error placing bid on loan {loan_id}: {e}")
            return {'success': False, 'error_message': str(e)}
    
    def run_demo(self) -> None:
        """Run a demonstration of the bidding functionality."""
        print("🚀 Kameo Bidding Bot - Demo")
        print("=" * 50)
        
        # Demo 1: List available loans
        print("\n📋 Demo 1: Listing Available Loans")
        print("-" * 30)
        
        loans = self.list_available_loans(max_pages=1)
        
        if not loans:
            print("No loans found.")
        else:
            print(f"Found {len(loans)} loans:")
            for i, loan in enumerate(loans[:3], 1):
                loan_id = loan.get('id', 'N/A')
                title = loan.get('title', 'No title')[:50] + "..." if len(loan.get('title', '')) > 50 else loan.get('title', 'No title')
                amount = loan.get('amount', 0)
                
                print(f"  {i}. ID: {loan_id} | {title} | {amount:,} SEK")
        
        # Demo 2: Analyze a specific loan
        print("\n🔍 Demo 2: Analyzing a Loan")
        print("-" * 30)
        
        if loans:
            loan_id = loans[0].get('id')
            print(f"Analyzing loan ID: {loan_id}")
            
            analysis = self.analyze_loan_for_bidding(loan_id)
            
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
        
        print("\n✅ Demo completed successfully!")


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
            click.echo(f"✅ Bid placed successfully!")
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