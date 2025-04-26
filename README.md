# Kameo Bot

A Python client for automating interactions with Kameo's investor platform. Features proper session management, 2FA support, and robust error handling.

## Features

- Secure configuration management using Pydantic
- TOTP-based 2FA support
- Proper session and redirect handling
- Comprehensive test coverage
- Environment variable support

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd kameo-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The bot can be configured using environment variables or by creating a `.env` file:

```env
KAMEO_EMAIL=your.email@example.com
KAMEO_PASSWORD=your-password
KAMEO_TOTP_SECRET=your-2fa-secret  # Optional
KAMEO_BASE_URL=https://www.kameo.se  # Optional
```

Required environment variables:
- `KAMEO_EMAIL`: Your Kameo login email
- `KAMEO_PASSWORD`: Your Kameo password

Optional environment variables:
- `KAMEO_TOTP_SECRET`: Your 2FA secret key (if 2FA is enabled)
- `KAMEO_BASE_URL`: Alternative base URL (default: https://www.kameo.se)
- `KAMEO_CONNECT_TIMEOUT`: Connection timeout in seconds (default: 5.0)
- `KAMEO_READ_TIMEOUT`: Read timeout in seconds (default: 10.0)

## Usage

Basic usage example:

```python
from config import KameoConfig
from get_it_done import KameoClient

# Configuration will be loaded from environment variables
config = KameoConfig()
client = KameoClient(config)

# Login and handle 2FA
if client.login() and client.handle_2fa():
    # Get account information
    account_number = client.get_account_number()
    print(f"Account number: {account_number}")
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=. --cov-report=term-missing
```

## Error Handling

The client includes comprehensive error handling:

- Network errors are logged and raised as exceptions
- 2FA failures are properly handled
- Redirect loops are prevented
- Timeouts are properly managed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

MIT License - see LICENSE file for details 