#!/usr/bin/env python3
"""
Kameo Bot - Main Application Entry Point

This file serves as the main entry point for the Kameo Bot application.
It can start the application in different modes:
- API server mode (for web interface)
- CLI mode (for command-line operations)
- Both modes simultaneously

Usage:
    python run.py                    # Start API server
    python run.py --cli              # Start CLI interface
    python run.py --api              # Start API server (default)
    python run.py --help             # Show help
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
try:
    from src.config import KameoConfig
    from src.database.config import DatabaseConfig
    from src.database.connection import init_database
    from src.services.loan_operations_service import LoanOperationsService
    from src.services.job_service import get_job_service
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed: uv sync")
    sys.exit(1)


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / 'kameo_bot.log', mode='a')
        ]
    )


def validate_configuration() -> bool:
    """Validate that all required configuration is present."""
    logger = logging.getLogger(__name__)
    
    try:
        # Test Kameo configuration
        kameo_config = KameoConfig()
        logger.info("✅ Kameo configuration loaded successfully")
        
        # Test database configuration
        db_config = DatabaseConfig()
        logger.info(f"✅ Database configuration loaded: {db_config.db_url}")
        
        # Test database connection
        db_manager = init_database(db_config)
        if db_manager.health_check():
            logger.info("✅ Database connection successful")
        else:
            logger.error("❌ Database connection failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False


def start_api_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False) -> None:
    """Start the FastAPI server."""
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        from src.api import app
        
        logger.info(f"🚀 Starting API server on {host}:{port}")
        logger.info(f"📖 API documentation available at: http://{host}:{port}/docs")
        logger.info(f"🔍 Health check available at: http://{host}:{port}/api/health")
        
        # Start the server
        uvicorn.run(
            "src.api:app",
            host=host,
            port=port,
            reload=debug,
            log_level="debug" if debug else "info"
        )
        
    except ImportError:
        logger.error("❌ FastAPI/uvicorn not installed. Install with: uv sync")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        sys.exit(1)


def start_frontend() -> None:
    """Start the frontend development server."""
    logger = logging.getLogger(__name__)
    
    try:
        import subprocess
        import os
        
        # Check if frontend directory exists
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            logger.error("❌ Frontend directory not found")
            sys.exit(1)
        
        # Check if Node.js is available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
            logger.info("✅ Node.js found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Node.js not found. Please install Node.js from https://nodejs.org")
            sys.exit(1)
        
        # Check if pnpm is available
        try:
            subprocess.run(["pnpm", "--version"], check=True, capture_output=True)
            logger.info("✅ pnpm found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ pnpm not found. Please install pnpm:")
            logger.error("   npm install -g pnpm")
            logger.error("   # Or: curl -fsSL https://get.pnpm.io/install.sh | sh -")
            sys.exit(1)
        
        # Change to frontend directory
        os.chdir(frontend_dir)
        
        # Check if node_modules exists
        if not Path("node_modules").exists():
            logger.info("📦 Installing frontend dependencies...")
            subprocess.run(["pnpm", "install"], check=True)
            logger.info("✅ Frontend dependencies installed")
        
        logger.info("🚀 Starting frontend development server...")
        logger.info("🌐 Frontend will be available at: http://localhost:5173")
        logger.info("🔧 API proxy configured to: http://localhost:8000")
        
        # Start the frontend
        subprocess.run(["pnpm", "run", "dev"], check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to start frontend: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start frontend: {e}")
        sys.exit(1)


def start_cli_interface() -> None:
    """Start the CLI interface."""
    logger = logging.getLogger(__name__)
    
    try:
        from src.cli import cli
        
        logger.info("🚀 Starting CLI interface")
        logger.info("💡 Use 'python run.py --cli --help' for available commands")
        
        # Run the CLI
        cli()
        
    except Exception as e:
        logger.error(f"❌ Failed to start CLI interface: {e}")
        sys.exit(1)


def run_demo() -> None:
    """Run a quick demo of the application."""
    logger = logging.getLogger(__name__)
    
    try:
        from src.services.loan_operations_service import LoanOperationsService
        
        logger.info("🎬 Running Kameo Bot Demo")
        logger.info("=" * 50)
        
        # Initialize service
        config = KameoConfig()
        service = LoanOperationsService(config)
        
        # Run demo
        result = service.run_demo()
        
        if result.get('demo_completed'):
            logger.info("✅ Demo completed successfully!")
            logger.info(f"   📊 Loans found: {result.get('loans_found', 0)}")
            if result.get('loan_analysis'):
                logger.info("   🔍 Loan analysis: Available")
        else:
            logger.error(f"❌ Demo failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Kameo Bot - Automated loan bidding and monitoring system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Start API server
  python run.py --cli              # Start CLI interface
  python run.py --demo             # Run demo
  python run.py --api --port 8080  # Start API on custom port
  python run.py --debug            # Enable debug mode
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--api',
        action='store_true',
        help='Start API server (default)'
    )
    mode_group.add_argument(
        '--cli',
        action='store_true',
        help='Start CLI interface'
    )
    mode_group.add_argument(
        '--frontend',
        action='store_true',
        help='Start frontend (React app)'
    )
    mode_group.add_argument(
        '--demo',
        action='store_true',
        help='Run demo'
    )
    
    # API server options
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host for API server (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for API server (default: 8000)'
    )
    
    # General options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration and exit'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Print banner
    print("🤖 Kameo Bot - Automated Loan Bidding System")
    print("=" * 50)
    
    # Validate configuration
    logger.info("🔧 Validating configuration...")
    if not validate_configuration():
        logger.error("❌ Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    logger.info("✅ Configuration validated successfully")
    
    # If only validating, exit here
    if args.validate_only:
        logger.info("✅ Configuration validation completed successfully")
        return
    
    # Determine mode
    if args.demo:
        run_demo()
    elif args.cli:
        start_cli_interface()
    elif args.frontend:
        start_frontend()
    else:
        # Default to API mode
        start_api_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main() 