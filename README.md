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

```bash
# Fetch loans from Kameo and save to database
python loan_collector.py fetch

# Fetch with custom page limit
python loan_collector.py fetch --max-pages 5

# Analyze all available API fields (debugging)
python loan_collector.py analyze

# Show database statistics
python loan_collector.py stats

# Search for loans
python loan_collector.py search "real estate"

# Check system health
python loan_collector.py health
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v
```

## Project Structure

```
kameoBotRebuild/
├── loan_collector.py          # Main CLI entry point
├── src/
│   ├── models/
│   ├── services/
│   ├── database/
│   ├── auth.py
│   ├── kameo_client.py
│   └── config.py
├── tests/
├── logs/
├── .env
└── requirements.txt
``` 