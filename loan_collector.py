#!/usr/bin/env python3
"""
Loan Collector CLI - Main entry point for the loan collection system.

This script provides a command-line interface for fetching loans from Kameo's API,
saving them to a database, and performing various operations on loan data.

Usage:
    python loan_collector.py fetch            # Fetch and save loans
    python loan_collector.py analyze          # Analyze all available fields
    python loan_collector.py stats            # Show database statistics
    python loan_collector.py --help           # Show help

The module can also be imported and used programmatically:
    from loan_collector import LoanCollector
    collector = LoanCollector()
    loans = collector.fetch_and_save_loans()
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/loan_collector.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import project modules
try:
    from src.config import KameoConfig
    from src.database.config import DatabaseConfig
    from src.database.connection import init_database
    from src.services.loan_collector import LoanCollectorService
    from src.services.loan_repository import LoanRepository
    from src.models.loan import LoanCreate, LoanResponse
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class LoanCollector:
    """
    Main loan collector class that orchestrates the entire process.
    
    This class provides a high-level interface for fetching loans from Kameo's API,
    processing them, and saving them to the database.
    """
    
    def __init__(self, save_raw_data: bool = False):
        """
        Initialize the loan collector.
        
        Args:
            save_raw_data: Whether to save raw API responses for debugging
        """
        self.save_raw_data = save_raw_data
        
        # Load configurations
        self.kameo_config = self._load_kameo_config()
        self.db_config = self._load_database_config()
        
        if not self.kameo_config:
            raise RuntimeError("Failed to load Kameo configuration")
        
        # Initialize database
        self.db_manager = init_database(self.db_config)
        
        # Initialize services
        self.loan_service = LoanCollectorService(self.kameo_config, save_raw_data)
        self.loan_repository = LoanRepository()
        
        logger.info("LoanCollector initialized successfully")
    
    def _load_kameo_config(self) -> Optional[KameoConfig]:
        """Load Kameo configuration from environment variables."""
        try:
            config = KameoConfig()
            logger.info("Kameo configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load Kameo configuration: {e}")
            return None
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        try:
            config = DatabaseConfig()
            logger.info(f"Database configuration loaded: {config.db_url}")
            return config
        except Exception as e:
            logger.error(f"Failed to load database configuration: {e}")
            # Return default configuration
            return DatabaseConfig()
    
    def fetch_and_save_loans(self, max_pages: int = 10) -> Dict[str, Any]:
        """
        Fetch loans from Kameo and save them to the database.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            Dictionary with operation results
        """
        logger.info("Starting loan collection process...")
        
        try:
            # Fetch loans from API
            raw_loans = self.loan_service.fetch_all_loans(max_pages=max_pages)
            
            if not raw_loans:
                logger.warning("No loans fetched from API")
                return {'status': 'no_loans', 'message': 'No loans found'}
            
            # Convert to loan objects
            loan_objects = self.loan_service.convert_to_loan_objects(raw_loans)
            
            if not loan_objects:
                logger.warning("No valid loan objects created")
                return {'status': 'conversion_failed', 'message': 'Failed to convert loans'}
            
            # Save to database
            save_results = self.loan_repository.save_loans(loan_objects)
            
            logger.info(f"Loan collection completed: {save_results}")
            
            return {
                'status': 'success',
                'raw_loans_count': len(raw_loans),
                'converted_loans_count': len(loan_objects),
                'save_results': save_results
            }
            
        except Exception as e:
            logger.error(f"Error in loan collection process: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_fields(self) -> Dict[str, Any]:
        """
        Analyze all available fields from the API for debugging.
        
        Returns:
            Dictionary with field analysis
        """
        logger.info("Starting field analysis...")
        
        try:
            analysis = self.loan_service.collect_and_save_all_fields()
            logger.info("Field analysis completed successfully")
            return analysis
        except Exception as e:
            logger.error(f"Error in field analysis: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        logger.info("Retrieving database statistics...")
        
        try:
            stats = self.loan_repository.get_loan_statistics()
            logger.info("Statistics retrieved successfully")
            return stats
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_recent_loans(self, limit: int = 10) -> List[LoanResponse]:
        """
        Get recent loans from the database.
        
        Args:
            limit: Number of loans to retrieve
            
        Returns:
            List of recent loans
        """
        try:
            loans = self.loan_repository.get_recent_loans(limit)
            logger.info(f"Retrieved {len(loans)} recent loans")
            return loans
        except Exception as e:
            logger.error(f"Error retrieving recent loans: {e}")
            return []
    
    def search_loans(self, search_term: str) -> List[LoanResponse]:
        """
        Search for loans by title or description.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching loans
        """
        try:
            loans = self.loan_repository.search_loans(search_term)
            logger.info(f"Found {len(loans)} loans matching '{search_term}'")
            return loans
        except Exception as e:
            logger.error(f"Error searching loans: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the system.
        
        Returns:
            Dictionary with health status
        """
        health = {
            'database': False,
            'configuration': False,
            'overall': False
        }
        
        try:
            # Check database connection
            health['database'] = self.db_manager.health_check()
            
            # Check configuration
            health['configuration'] = self.kameo_config is not None
            
            # Overall health
            health['overall'] = health['database'] and health['configuration']
            
            logger.info(f"Health check completed: {health}")
            return health
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            health['error'] = str(e)
            return health
    
    def close(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'loan_service'):
                self.loan_service.close()
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            logger.info("LoanCollector closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# CLI Interface using Click
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--save-raw-data', is_flag=True, help='Save raw API responses for debugging')
@click.pass_context
def cli(ctx, debug, save_raw_data):
    """Loan Collector CLI - Fetch and manage loans from Kameo."""
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj['save_raw_data'] = save_raw_data


@cli.command()
@click.option('--max-pages', default=10, help='Maximum number of pages to fetch')
@click.pass_context
def fetch(ctx, max_pages):
    """Fetch loans from Kameo and save to database."""
    collector = None
    try:
        collector = LoanCollector(save_raw_data=ctx.obj.get('save_raw_data', False))
        
        click.echo("Fetching loans from Kameo...")
        results = collector.fetch_and_save_loans(max_pages=max_pages)
        
        if results['status'] == 'success':
            click.echo(f"✅ Success! Processed {results['raw_loans_count']} loans")
            click.echo(f"   - Converted: {results['converted_loans_count']}")
            click.echo(f"   - Saved: {results['save_results']['saved_loans']}")
            click.echo(f"   - Updated: {results['save_results']['updated_loans']}")
            
            if results['save_results']['failed_loans'] > 0:
                click.echo(f"   - Failed: {results['save_results']['failed_loans']}")
        else:
            click.echo(f"❌ Failed: {results.get('message', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        if collector:
            collector.close()


@cli.command()
@click.pass_context
def analyze(ctx):
    """Analyze all available fields from the API."""
    collector = None
    try:
        collector = LoanCollector(save_raw_data=True)  # Always save raw data for analysis
        
        click.echo("Analyzing API fields...")
        results = collector.analyze_fields()
        
        if 'status' in results and results['status'] == 'error':
            click.echo(f"❌ Error: {results['message']}")
            return
        
        click.echo(f"✅ Analysis complete!")
        click.echo(f"   - Total loans analyzed: {results['total_loans']}")
        click.echo(f"   - Unique fields found: {len(results['all_fields'])}")
        
        click.echo("\nAvailable fields:")
        for field in results['all_fields']:
            field_types = results['field_types'].get(field, ['unknown'])
            click.echo(f"   - {field}: {', '.join(field_types)}")
        
        # Save detailed analysis to file
        analysis_file = Path('logs/field_analysis.json')
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        click.echo(f"\nDetailed analysis saved to: {analysis_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        if collector:
            collector.close()


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    collector = None
    try:
        collector = LoanCollector(save_raw_data=ctx.obj.get('save_raw_data', False))
        
        click.echo("Retrieving database statistics...")
        stats = collector.get_statistics()
        
        if 'status' in stats and stats['status'] == 'error':
            click.echo(f"❌ Error: {stats['message']}")
            return
        
        click.echo(f"📊 Database Statistics:")
        click.echo(f"   - Total loans: {stats.get('total_loans', 0)}")
        
        # Status breakdown
        if 'by_status' in stats:
            click.echo("\n   Status breakdown:")
            for status, count in stats['by_status'].items():
                click.echo(f"     - {status}: {count}")
        
        # Amount statistics
        if 'amount_stats' in stats:
            amount_stats = stats['amount_stats']
            click.echo("\n   Amount statistics:")
            click.echo(f"     - Total: {amount_stats['total_amount']:,.2f} SEK")
            click.echo(f"     - Average: {amount_stats['avg_amount']:,.2f} SEK")
            click.echo(f"     - Min: {amount_stats['min_amount']:,.2f} SEK")
            click.echo(f"     - Max: {amount_stats['max_amount']:,.2f} SEK")
        
        # Recent loans
        if 'recent_loans' in stats:
            click.echo("\n   Recent loans:")
            for loan in stats['recent_loans']:
                click.echo(f"     - {loan['loan_id']}: {loan['title']} ({loan['amount']:,.2f} SEK)")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        if collector:
            collector.close()


@cli.command()
@click.argument('search_term')
@click.pass_context
def search(ctx, search_term):
    """Search for loans by title or description."""
    collector = None
    try:
        collector = LoanCollector(save_raw_data=ctx.obj.get('save_raw_data', False))
        
        click.echo(f"Searching for loans matching '{search_term}'...")
        loans = collector.search_loans(search_term)
        
        if not loans:
            click.echo("No loans found matching the search term.")
            return
        
        click.echo(f"Found {len(loans)} loans:")
        for loan in loans:
            click.echo(f"  - {loan.loan_id}: {loan.title}")
            click.echo(f"    Amount: {loan.amount:,.2f} SEK, Status: {loan.status}")
            if loan.url:
                click.echo(f"    URL: {loan.url}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        if collector:
            collector.close()


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health."""
    collector = None
    try:
        collector = LoanCollector(save_raw_data=ctx.obj.get('save_raw_data', False))
        
        click.echo("Checking system health...")
        health = collector.health_check()
        
        click.echo("\n🏥 Health Check Results:")
        click.echo(f"   - Database: {'✅ OK' if health['database'] else '❌ FAIL'}")
        click.echo(f"   - Configuration: {'✅ OK' if health['configuration'] else '❌ FAIL'}")
        click.echo(f"   - Overall: {'✅ HEALTHY' if health['overall'] else '❌ UNHEALTHY'}")
        
        if 'error' in health:
            click.echo(f"   - Error: {health['error']}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        if collector:
            collector.close()


# Main execution
if __name__ == '__main__':
    cli() 