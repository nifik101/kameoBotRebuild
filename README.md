# Kameo Bot Rebuild

A comprehensive Python application for interacting with Kameo's lending platform. This bot provides loan collection, analysis, and automated bidding capabilities based on real API integration discovered through HAR analysis.

## Features

- **Real API Integration**: Uses actual Kameo API endpoints discovered through HAR analysis
- **Automated Bidding**: Intelligent bidding system with risk analysis and rate limiting
- **Loan Collection**: Comprehensive loan data collection and storage
- **Database Storage**: SQLite by default, ready for PostgreSQL migration
- **CLI Interface**: Unified command-line interface for all operations
- **Modular Design**: Clean separation of concerns with services, repositories, and models
- **Authentication**: Full support for Kameo login with 2FA (TOTP)
- **Data Validation**: Comprehensive validation using Pydantic models
- **Raw Data Debugging**: Optional saving of raw API responses for debugging
- **Comprehensive Testing**: Full test suite with unit and integration tests
- **Configuration Management**: Environment-based configuration with .env support

## Installation

### Prerequisites

- Python 3.8+
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
   pip install -r requirements.txt
   ```

4. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

## Configuration

The application uses environment variables for configuration. Edit your `.env` file:

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
LOAN_DB_POOL_SIZE=5
LOAN_DB_MAX_OVERFLOW=10
LOAN_DB_POOL_TIMEOUT=30
LOAN_DB_POOL_RECYCLE=3600

# Backup Settings (optional)
LOAN_DB_BACKUP_ENABLED=true
LOAN_DB_BACKUP_INTERVAL_HOURS=24
LOAN_DB_BACKUP_RETENTION_DAYS=7
```

## Usage

### Command Line Interface

The application provides a unified CLI for all operations:

#### Loan Collection and Analysis

```bash
# Fetch loans from Kameo and save to database
python -m src.cli loans fetch

# Fetch with custom page limit
python -m src.cli loans fetch --max-pages 5

# Analyze all available API fields (debugging)
python -m src.cli loans analyze

# Show database statistics
python -m src.cli loans stats
```

#### Bidding Operations

```bash
# List available loans for bidding
python -m src.cli bidding list

# List with custom page limit
python -m src.cli bidding list --max-pages 5

# Analyze a specific loan for bidding potential
python -m src.cli bidding analyze <loan_id>

# Place a bid on a loan
python -m src.cli bidding bid <loan_id> <amount>

# Place a bid with down payment option
python -m src.cli bidding bid <loan_id> <amount> --payment-option dp
```

#### Demo and Debugging

```bash
# Run a demonstration of the bidding functionality
python -m src.cli demo

# Enable debug logging
python -m src.cli --debug loans fetch

# Save raw API responses for debugging
python -m src.cli --save-raw-data loans fetch
```

### Programmatic Usage

You can also use the modules programmatically:

```python
from src.config import KameoConfig
from src.services.bidding_service import BiddingService, BiddingRequest
from src.services.loan_collector import LoanCollectorService

# Initialize configuration
config = KameoConfig()

# Initialize services
bidding_service = BiddingService(config)
loan_service = LoanCollectorService(config)

# Fetch loans
loans = loan_service.fetch_all_loans(max_pages=3)

# Place a bid
request = BiddingRequest(loan_id=123, amount=5000, payment_option="ip")
response = bidding_service.place_bid(request)
```

## Project Structure

```
kameoBotRebuild/
├── src/
│   ├── cli.py                 # Unified CLI interface
│   ├── config.py              # Configuration management
│   ├── auth.py                # Authentication utilities
│   ├── kameo_client.py        # Kameo API client
│   ├── models/                # Data models
│   │   ├── base.py
│   │   └── loan.py
│   ├── services/              # Business logic services
│   │   ├── bidding_service.py
│   │   ├── loan_collector.py
│   │   └── loan_repository.py
│   └── database/              # Database layer
│       ├── config.py
│       └── connection.py
├── tests/                     # Test suite
├── docs/                      # Documentation
├── data/                      # HAR files and raw data
├── logs/                      # Application logs
├── simple_bidding.py          # Demo script
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_client.py

# Run with coverage
pytest --cov=src
```

## Development

### Code Style

The project follows Python best practices:

- **Type Hints**: All functions and methods use type hints
- **Docstrings**: Comprehensive documentation for all public APIs
- **Error Handling**: Robust error handling with meaningful messages
- **Logging**: Structured logging throughout the application
- **Testing**: Comprehensive test coverage

### Adding New Features

1. **Models**: Add new data models in `src/models/`
2. **Services**: Add business logic in `src/services/`
3. **CLI Commands**: Add new commands in `src/cli.py`
4. **Tests**: Add corresponding tests in `tests/`

## Security Considerations

- **Credentials**: Never commit `.env` files with real credentials
- **Rate Limiting**: The application respects Kameo's rate limits
- **2FA**: Full support for TOTP-based two-factor authentication
- **Session Management**: Proper session handling and cleanup

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Authentication Failures**: Check your `.env` configuration
3. **Rate Limiting**: Wait between requests if you hit rate limits
4. **Database Errors**: Check database configuration and permissions

### Debug Mode

Enable debug logging to get detailed information:

```bash
python -m src.cli --debug demo
```

### Raw Data Analysis

Save raw API responses for debugging:

```bash
python -m src.cli --save-raw-data loans fetch
```

## License

This project is for educational and personal use. Please respect Kameo's terms of service and rate limits.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Changelog

See [changelog.md](changelog.md) for a detailed history of changes. 