# Loan Collector Module

A comprehensive Python module for collecting loan data from Kameo's API and storing it in a database. This module is designed to be both CLI-friendly and importable for use in other applications.

## Features

- **Real API Integration**: Uses actual Kameo API endpoints discovered through HAR analysis
- **Database Storage**: SQLite by default, ready for PostgreSQL migration
- **CLI Interface**: Easy-to-use command-line interface with multiple commands
- **Modular Design**: Clean separation of concerns with services, repositories, and models
- **Authentication**: Full support for Kameo login with 2FA
- **Data Validation**: Comprehensive validation using Pydantic models
- **Raw Data Debugging**: Optional saving of raw API responses for debugging
- **Comprehensive Testing**: Full test suite with unit and integration tests
- **Configuration Management**: Environment-based configuration with .env support

## Installation

### Prerequisites

- Python 3.8+
- uv (fast Python package installer: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Virtual environment (recommended)

### Setup

1. **Clone and navigate to the project**:
   ```bash
   cd kameoBotRebuild
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

## Configuration

The module uses environment variables for configuration. Create a `.env` file in the project root:

```env
# Kameo Authentication (required)
KAMEO_EMAIL=your.email@example.com
KAMEO_PASSWORD=your_password
KAMEO_TOTP_SECRET=your_totp_secret  # Optional, for 2FA

# Kameo API Settings (optional)
KAMEO_BASE_URL=https://www.kameo.se
KAMEO_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
KAMEO_CONNECT_TIMEOUT=5.0
KAMEO_READ_TIMEOUT=10.0

# Database Settings (optional)
LOAN_DB_DB_URL=sqlite:///./loans.db
LOAN_DB_ECHO=false
LOAN_DB_CREATE_TABLES=true
```

## Usage

### Command Line Interface

The module provides a comprehensive CLI for various operations:

#### Basic Commands

```bash
# Fetch loans from Kameo and save to database
uv run python loan_collector.py fetch

# Fetch with custom page limit
uv run python loan_collector.py fetch --max-pages 5

# Analyze all available API fields (debugging)
uv run python loan_collector.py analyze

# Show database statistics
uv run python loan_collector.py stats

# Search for loans
uv run python loan_collector.py search "real estate"

# Check system health
uv run python loan_collector.py health
```

#### Advanced Options

```bash
# Enable debug logging
uv run python loan_collector.py --debug fetch

# Save raw API responses for debugging
uv run python loan_collector.py --save-raw-data fetch

# Show help
uv run python loan_collector.py --help
```

### Programmatic Usage

The module can also be imported and used programmatically:

```python
from loan_collector import LoanCollector

# Initialize collector
collector = LoanCollector(save_raw_data=False)

# Fetch and save loans
results = collector.fetch_and_save_loans(max_pages=10)

if results['status'] == 'success':
    print(f"Successfully processed {results['raw_loans_count']} loans")
    print(f"Saved: {results['save_results']['saved_loans']}")
    print(f"Updated: {results['save_results']['updated_loans']}")

# Get statistics
stats = collector.get_statistics()
print(f"Total loans in database: {stats['total_loans']}")

# Search for loans
loans = collector.search_loans("fastighet")
print(f"Found {len(loans)} loans matching search term")

# Clean up
collector.close()
```

### Using Individual Services

For more granular control, you can use individual services:

```python
from config import KameoConfig
from src.services.loan_collector import LoanCollectorService
from src.services.loan_repository import LoanRepository
from src.database.config import DatabaseConfig
from src.database.connection import init_database

# Load configuration
config = KameoConfig()
db_config = DatabaseConfig()

# Initialize database
init_database(db_config)

# Create services
loan_service = LoanCollectorService(config, save_raw_data=True)
loan_repo = LoanRepository()

# Fetch loans
raw_loans = loan_service.fetch_all_loans(max_pages=5)
loan_objects = loan_service.convert_to_loan_objects(raw_loans)

# Save to database
results = loan_repo.save_loans(loan_objects)
print(f"Save results: {results}")

# Query database
recent_loans = loan_repo.get_recent_loans(limit=10)
stats = loan_repo.get_loan_statistics()
```

## API Endpoints

The module uses the following Kameo API endpoints (discovered through HAR analysis):

- **Loans listing**: `https://api.kameo.se/v1/loans/listing/investment-options`
- **Loan Q&A**: `https://api.kameo.se/v1/q-a?loan_application_id={id}`
- **Bidding data**: `https://api.kameo.se/v1/bidding/{id}/load`
- **Account info**: `https://www.kameo.se/ezjscore/call/kameo_transfer::init`

## Database Schema

The module creates the following database structure:

### `loans` table:
- `id` (Primary Key)
- `loan_id` (Unique, from API)
- `title`
- `status` (open, closed, funded, etc.)
- `amount`
- `interest_rate`
- `open_date`
- `close_date`
- `funding_progress`
- `funded_amount`
- `url`
- `description`
- `raw_data` (JSON, for debugging)
- `created_at`
- `updated_at`
- Additional fields: `borrower_type`, `loan_type`, `risk_grade`, `duration_months`

## Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_loan_collector.py

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Development

### Project Structure

```
kameoBotRebuild/
├── loan_collector.py          # Main CLI entry point
├── config.py                  # Existing Kameo configuration
├── auth.py                    # Existing authentication
├── kameo_client.py           # Existing Kameo client
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py           # SQLAlchemy base
│   │   └── loan.py           # Loan models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── loan_collector.py # Main service
│   │   └── loan_repository.py # Database operations
│   ├── database/
│   │   ├── __init__.py
│   │   ├── config.py         # Database configuration
│   │   └── connection.py     # Database connection
│   └── config/
├── tests/
│   └── test_loan_collector.py
├── logs/                     # Generated logs
├── .env                      # Configuration file
└── requirements.txt          # Dependencies
```

### Key Design Principles

1. **Modular Architecture**: Clear separation between API, database, and business logic
2. **Configuration Management**: Environment-based configuration with sensible defaults
3. **Error Handling**: Comprehensive error handling with detailed logging
4. **Testing**: Extensive test coverage with both unit and integration tests
5. **Documentation**: Comprehensive docstrings and type hints
6. **Extensibility**: Easy to extend with new features and API endpoints

### Adding New Features

1. **New API Endpoints**: Add to `LoanCollectorService.fetch_loan_details()`
2. **New Data Fields**: Update `Loan` model in `src/models/loan.py`
3. **New CLI Commands**: Add to `loan_collector.py` CLI section
4. **New Database Operations**: Add to `LoanRepository` class

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Check your email and password in `.env`
   - Ensure TOTP secret is correct if using 2FA
   - Verify your Kameo account is active

2. **Database Errors**:
   - Check database URL in configuration
   - Ensure write permissions for SQLite file
   - Check database connectivity for PostgreSQL

3. **API Errors**:
   - Check network connectivity
   - Verify API endpoints are still active
   - Check rate limiting (60 requests per minute)

4. **Import Errors**:
   - Ensure all dependencies are installed
   - Check Python version compatibility
   - Verify virtual environment is activated

### Debug Mode

Enable debug logging to see detailed information:

```bash
uv run python loan_collector.py --debug --save-raw-data fetch
```

This will:
- Show detailed HTTP requests and responses
- Save raw API responses to `logs/debug/`
- Provide verbose logging of all operations

### Log Files

- `logs/loan_collector.log`: Main application log
- `logs/debug/`: Raw API responses (when enabled)
- `logs/field_analysis.json`: API field analysis results

## Contributing

1. Follow PEP 8 style guide
2. Add comprehensive tests for new features
3. Update documentation
4. Use type hints throughout
5. Add detailed logging for debugging

## License

This project is part of the Kameo bidding bot system. Please refer to the main project license.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in debug mode
3. Check the test suite for examples
4. Review the existing codebase for patterns

## Changelog

### v1.0.0 (Current)
- Initial implementation with full API integration
- CLI interface with multiple commands
- Database storage with SQLite/PostgreSQL support
- Comprehensive testing and documentation
- Real-time data fetching from Kameo API
- Field analysis and debugging capabilities 