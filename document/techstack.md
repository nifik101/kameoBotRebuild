# Technology Stack

## Core Technologies

### Backend Framework & Language
- **Python 3.8+** - Primary programming language with modern features
- **SQLAlchemy 2.0+** - Modern ORM with declarative mapping and async support
- **Pydantic 2.11+** - Data validation and settings management with v2 features

### Database & Storage
- **SQLite** - Default database for development and small-scale deployments
- **PostgreSQL** - Production-ready database (migration-ready)
- **Alembic** - Database migration and schema versioning

### HTTP & API Integration
- **HTTPX 0.27+** - Modern async-capable HTTP client
- **Requests 2.31+** - Legacy HTTP client for simple synchronous requests
- **BeautifulSoup4 4.12+** - HTML parsing for fallback data extraction

### Authentication & Security
- **PyOTP 2.9+** - TOTP (Time-based One-Time Password) for 2FA support
- **python-dotenv 1.0+** - Environment variable management for secure configuration

### CLI & User Interface
- **Click 8.0+** - Command-line interface framework
- **Rich** - Enhanced console output (future consideration)

### Testing & Quality Assurance
- **Pytest 8.0+** - Modern testing framework with fixtures and parametrization
- **Responses 0.24+** - HTTP request mocking for testing
- **Ruff 0.11.7+** - Fast Python linter and formatter (replaces flake8, black, isort)

### Development Tools
- **uv** - Fast Python package installer and virtual environment manager
- **mypy** - Static type checking (future consideration)

## Architecture Patterns

### Design Patterns
- **Repository Pattern** - Centralized data access through loan repository
- **Service Layer Pattern** - Business logic separated in service classes
- **Model-View-Controller (MVC)** - Clear separation of concerns
- **Configuration as Code** - Environment-based configuration with validation

### Data Architecture
- **ORM (Object-Relational Mapping)** - SQLAlchemy for database abstraction
- **Data Transfer Objects (DTOs)** - Pydantic models for API data validation
- **Database-First Approach** - Schema-driven development with migrations

### API Integration
- **RESTful API consumption** - Standard HTTP methods and status codes
- **HAR analysis-driven development** - Real API endpoint discovery
- **Rate limiting awareness** - Respectful API consumption patterns

## Code Quality & Standards

### Code Style
- **PEP 8** - Python style guide compliance
- **Type Hints** - Full type annotation for better IDE support and validation
- **Docstrings** - Comprehensive documentation for all modules and functions
- **Error Handling** - Comprehensive exception handling with custom exceptions

### Testing Strategy
- **Unit Testing** - Individual component testing
- **Integration Testing** - Database and API integration testing
- **Mock Testing** - External dependency isolation
- **Production Testing** - Real API verification with actual data

### Security Considerations
- **Environment Variables** - Secure credential management
- **Input Validation** - Pydantic-based data validation
- **SQL Injection Prevention** - SQLAlchemy ORM protection
- **HTTPS** - Secure API communication

## File Structure & Organization

```
src/
├── models/          # Data models (SQLAlchemy + Pydantic)
├── services/        # Business logic and external integrations
├── database/        # Database configuration and connections
tests/              # Comprehensive test suite
docs/               # Documentation and guides
logs/               # Application logging output
```

## Dependencies Summary

### Production Dependencies
```
requests>=2.31.0          # HTTP client
beautifulsoup4>=4.12.0    # HTML parsing
pyotp>=2.9.0             # 2FA TOTP generation
pydantic>=2.11.3         # Data validation
pydantic-settings>=2.9.0  # Settings management
python-dotenv>=1.0.0     # Environment variables
sqlalchemy>=2.0.0        # ORM
alembic>=1.13.0          # Database migrations
click>=8.0.0             # CLI framework
httpx>=0.27.0            # Modern HTTP client
```

### Development Dependencies
```
pytest>=8.0.0            # Testing framework
responses>=0.24.0        # HTTP mocking
ruff>=0.11.7             # Linting and formatting
```

## Performance Characteristics

### Scalability Features
- **Database connection pooling** - Efficient database resource management
- **Async HTTP support** - Non-blocking API requests (HTTPX)
- **Lazy loading** - On-demand data loading with SQLAlchemy
- **Pagination support** - Memory-efficient large dataset handling

### Monitoring & Observability
- **Structured logging** - JSON-formatted logs for analysis
- **Health checks** - System health monitoring endpoints
- **Performance metrics** - Database query timing and API response times
- **Error tracking** - Comprehensive exception logging and context capture

## Future Technology Considerations

### Potential Enhancements
- **FastAPI** - Modern API framework for web endpoints
- **Redis** - Caching and session storage
- **Celery** - Background task processing
- **Docker** - Containerization for deployment
- **GitHub Actions** - CI/CD pipeline automation
