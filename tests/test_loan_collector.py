"""
Tests for the loan collector system.

This module contains comprehensive tests for the loan collector functionality,
including API integration tests, database operations, and CLI commands.
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from pathlib import Path

# Import the modules to test
try:
    from src.models.loan import LoanCreate, LoanStatus, LoanResponse
    from src.services.loan_collector import LoanCollectorService
    from src.services.loan_repository import LoanRepository
    from src.database.config import DatabaseConfig
    from src.config import KameoConfig
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestLoanModels:
    """Test loan data models."""
    
    def test_loan_create_validation(self):
        """Test LoanCreate model validation."""
        valid_loan = LoanCreate(
            loan_id="123",
            title="Test Loan",
            amount=Decimal("100000.00"),
            status=LoanStatus.OPEN
        )
        
        assert valid_loan.loan_id == "123"
        assert valid_loan.title == "Test Loan"
        assert valid_loan.amount == Decimal("100000.00")
        assert valid_loan.status == LoanStatus.OPEN
    
    def test_loan_create_validation_errors(self):
        """Test LoanCreate model validation errors."""
        with pytest.raises(ValueError, match="Loan ID cannot be empty"):
            LoanCreate(
                loan_id="",
                title="Test Loan",
                amount=Decimal("100000.00")
            )
        
        with pytest.raises(ValueError, match="Loan title cannot be empty"):
            LoanCreate(
                loan_id="123",
                title="",
                amount=Decimal("100000.00")
            )
        
        with pytest.raises(ValueError, match="Loan amount must be positive"):
            LoanCreate(
                loan_id="123",
                title="Test Loan",
                amount=Decimal("-100.00")
            )
    
    def test_loan_status_enum(self):
        """Test LoanStatus enum values."""
        assert LoanStatus.OPEN.value == "open"
        assert LoanStatus.CLOSED.value == "closed"
        assert LoanStatus.FUNDED.value == "funded"
        assert LoanStatus.ACTIVE.value == "active"
        assert LoanStatus.COMPLETED.value == "completed"
        assert LoanStatus.CANCELED.value == "canceled"
        assert LoanStatus.UNKNOWN.value == "unknown"


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_config(self):
        """Test default database configuration."""
        config = DatabaseConfig()
        
        assert config.db_url == "sqlite:///./loans.db"
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.create_tables is True
        assert config.echo is False
    
    def test_sqlite_detection(self):
        """Test SQLite database detection."""
        config = DatabaseConfig(db_url="sqlite:///test.db")
        
        assert config.is_sqlite() is True
        assert config.is_postgresql() is False
    
    def test_postgresql_detection(self):
        """Test PostgreSQL database detection."""
        config = DatabaseConfig(db_url="postgresql://user:pass@localhost/db")
        
        assert config.is_sqlite() is False
        assert config.is_postgresql() is True
    
    def test_validation_errors(self):
        """Test configuration validation errors."""
        with pytest.raises(ValueError, match="Pool size must be at least 1"):
            DatabaseConfig(pool_size=0)
        
        with pytest.raises(ValueError, match="Backup interval must be at least 1 hour"):
            DatabaseConfig(backup_interval_hours=0)


class TestLoanCollectorService:
    """Test loan collector service."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Kameo configuration."""
        config = Mock(spec=KameoConfig)
        config.totp_secret = "test_secret"
        config.email = "test@example.com"
        config.password = "test_password"
        config.base_url = "https://test.kameo.se"
        config.user_agent = "Test Agent"
        config.connect_timeout = 5.0
        config.read_timeout = 10.0
        return config
    
    @pytest.fixture
    def loan_service(self, mock_config):
        """Create loan collector service with mocked config."""
        with patch('src.services.loan_collector.KameoAuthenticator'):
            service = LoanCollectorService(mock_config, save_raw_data=False)
            return service
    
    def test_initialization(self, loan_service, mock_config):
        """Test service initialization."""
        assert loan_service.config == mock_config
        assert loan_service.save_raw_data is False
        assert loan_service.is_authenticated is False
    
    def test_convert_single_loan(self, loan_service):
        """Test conversion of single loan data."""
        raw_loan = {
            'id': '123',
            'title': 'Test Loan',
            'amount': '100000.00',
            'interest_rate': '5.5',
            'status': 'open',
            'description': 'Test description'
        }
        
        loan_obj = loan_service._convert_single_loan(raw_loan)
        
        assert loan_obj is not None
        assert loan_obj.loan_id == '123'
        assert loan_obj.title == 'Test Loan'
        assert loan_obj.amount == Decimal('100000.00')
        assert loan_obj.interest_rate == Decimal('5.5')
        assert loan_obj.status == LoanStatus.OPEN
        assert loan_obj.description == 'Test description'
    
    def test_determine_loan_status(self, loan_service):
        """Test loan status determination."""
        assert loan_service._determine_loan_status({'status': 'open'}) == LoanStatus.OPEN
        assert loan_service._determine_loan_status({'status': 'closed'}) == LoanStatus.CLOSED
        assert loan_service._determine_loan_status({'status': 'funded'}) == LoanStatus.FUNDED
        assert loan_service._determine_loan_status({'status': 'unknown_status'}) == LoanStatus.UNKNOWN
        assert loan_service._determine_loan_status({}) == LoanStatus.UNKNOWN
    
    def test_parse_date(self, loan_service):
        """Test date parsing."""
        # Test various date formats
        assert loan_service._parse_date('2023-01-01') is not None
        assert loan_service._parse_date('2023-01-01 12:00:00') is not None
        assert loan_service._parse_date('2023-01-01T12:00:00') is not None
        assert loan_service._parse_date('2023-01-01T12:00:00Z') is not None
        assert loan_service._parse_date('invalid_date') is None
        assert loan_service._parse_date(None) is None
        assert loan_service._parse_date('') is None
    
    @patch('src.services.loan_collector.requests.Session')
    def test_fetch_loans_not_authenticated(self, mock_session, loan_service):
        """Test fetching loans when not authenticated."""
        loan_service.is_authenticated = False
        
        with patch.object(loan_service, 'authenticate', return_value=False):
            with pytest.raises(RuntimeError, match="Authentication failed"):
                loan_service.fetch_loans()
    
    def test_fetch_loans_success(self, loan_service):
        """Test successful loan fetching."""
        loan_service.is_authenticated = True
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '123',
                    'title': 'Test Loan',
                    'amount': '100000.00',
                    'status': 'open'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(loan_service.session, 'request', return_value=mock_response):
            loans = loan_service.fetch_loans()
        
        assert len(loans) == 1
        assert loans[0]['id'] == '123'
        assert loans[0]['title'] == 'Test Loan'
    
    def test_save_raw_data(self, loan_service, tmp_path):
        """Test raw data saving."""
        # Change working directory to temp path
        original_cwd = Path.cwd()
        
        try:
            import os
            os.chdir(tmp_path)
            
            loan_service.save_raw_data = True
            test_data = {'test': 'data'}
            
            loan_service._save_raw_data('test_type', test_data, 'test_id')
            
            # Check that file was created
            logs_dir = tmp_path / 'logs' / 'debug'
            assert logs_dir.exists()
            
            # Check that a JSON file was created
            json_files = list(logs_dir.glob('test_type_test_id_*.json'))
            assert len(json_files) == 1
            
            # Check file content
            with open(json_files[0]) as f:
                saved_data = json.load(f)
            
            assert saved_data == test_data
            
        finally:
            os.chdir(original_cwd)


class TestLoanRepository:
    """Test loan repository."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def loan_repo(self):
        """Create loan repository."""
        return LoanRepository()
    
    def test_initialization(self, loan_repo):
        """Test repository initialization."""
        assert loan_repo is not None
    
    def test_save_loan_new(self, loan_repo, mock_session):
        """Test saving a new loan."""
        loan_data = LoanCreate(
            loan_id="123",
            title="Test Loan",
            amount=Decimal("100000.00"),
            status=LoanStatus.OPEN
        )
        
        # Mock database session context manager
        with patch('src.services.loan_repository.db_session_scope') as mock_scope:
            mock_scope.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Mock the _create_new_loan method
            with patch.object(loan_repo, '_create_new_loan') as mock_create:
                mock_response = Mock(spec=LoanResponse)
                mock_create.return_value = mock_response
                
                result = loan_repo.save_loan(loan_data)
                
                assert result == mock_response
                mock_create.assert_called_once_with(mock_session, loan_data)


class TestCLICommands:
    """Test CLI commands."""
    
    def test_cli_help(self):
        """Test CLI help command."""
        from click.testing import CliRunner
        
        # Import the CLI after dependencies are available
        with patch('loan_collector.LoanCollector'):
            from loan_collector import cli
            
            runner = CliRunner()
            result = runner.invoke(cli, ['--help'])
            
            assert result.exit_code == 0
            assert 'Loan Collector CLI' in result.output
            assert 'fetch' in result.output
            assert 'analyze' in result.output
            assert 'stats' in result.output
    
    def test_cli_health_command(self):
        """Test CLI health command."""
        from click.testing import CliRunner
        
        with patch('loan_collector.LoanCollector') as mock_collector_class:
            from loan_collector import cli
            
            # Mock the collector instance
            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector
            mock_collector.health_check.return_value = {
                'database': True,
                'configuration': True,
                'overall': True
            }
            
            runner = CliRunner()
            result = runner.invoke(cli, ['health'])
            
            assert result.exit_code == 0
            assert '✅ HEALTHY' in result.output
    
    def test_cli_stats_command(self):
        """Test CLI stats command."""
        from click.testing import CliRunner
        
        with patch('loan_collector.LoanCollector') as mock_collector_class:
            from loan_collector import cli
            
            # Mock the collector instance
            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector
            mock_collector.get_statistics.return_value = {
                'total_loans': 10,
                'by_status': {'open': 5, 'closed': 5},
                'amount_stats': {
                    'total_amount': 1000000.0,
                    'avg_amount': 100000.0,
                    'min_amount': 50000.0,
                    'max_amount': 200000.0
                }
            }
            
            runner = CliRunner()
            result = runner.invoke(cli, ['stats'])
            
            assert result.exit_code == 0
            assert 'Total loans: 10' in result.output
            assert 'Total: 1,000,000.00 SEK' in result.output


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.skipif(
        not Path('.env').exists(),
        reason="No .env file found - skipping integration tests"
    )
    def test_database_connection(self):
        """Test actual database connection."""
        from src.database.config import DatabaseConfig
        from src.database.connection import DatabaseManager
        
        config = DatabaseConfig(db_url="sqlite:///test_integration.db")
        db_manager = DatabaseManager(config)
        
        assert db_manager.health_check() is True
        
        # Clean up
        db_manager.close()
        test_db = Path("test_integration.db")
        if test_db.exists():
            test_db.unlink()
    
    @pytest.mark.skipif(
        not Path('.env').exists(),
        reason="No .env file found - skipping integration tests"
    )
    def test_full_workflow_with_mock_data(self):
        """Test the full workflow with mocked API data."""
        from loan_collector import LoanCollector
        
        # Create a temporary database
        test_db = Path("test_workflow.db")
        
        try:
            # Set up test environment
            import os
            os.environ['LOAN_DB_DB_URL'] = f"sqlite:///{test_db}"
            
            # Mock the authentication to prevent import issues
            with patch('auth.KameoAuthenticator') as mock_auth:
                mock_auth.return_value.authenticate.return_value = True
                
                # Mock the API calls
                with patch('src.services.loan_collector.LoanCollectorService') as mock_service_class:
                    mock_service = Mock()
                    mock_service_class.return_value = mock_service
                    mock_service.authenticate.return_value = True
                    mock_service.is_authenticated = True
                    
                    # Mock data
                    mock_service.fetch_all_loans.return_value = [
                        {
                            'id': '123',
                            'title': 'Test Loan',
                            'amount': '100000.00',
                            'status': 'open'
                        }
                    ]
                    
                    mock_service.convert_to_loan_objects.return_value = [
                        LoanCreate(
                            loan_id="123",
                            title="Test Loan",
                            amount=Decimal("100000.00"),
                            status=LoanStatus.OPEN
                        )
                    ]
                    
                    # Test the workflow
                    collector = LoanCollector(save_raw_data=False)
                    results = collector.fetch_and_save_loans()
                    
                    assert results['status'] == 'success'
                    assert results['raw_loans_count'] == 1
                    assert results['converted_loans_count'] == 1
                
                collector.close()
                
        finally:
            # Clean up
            if test_db.exists():
                test_db.unlink()


# Test fixtures and utilities
@pytest.fixture
def sample_loan_data():
    """Sample loan data for testing."""
    return {
        'id': '123',
        'title': 'Test Loan - Real Estate Investment',
        'amount': '100000.00',
        'interest_rate': '5.5',
        'status': 'open',
        'description': 'A test loan for real estate investment',
        'open_date': '2023-01-01T09:00:00Z',
        'close_date': '2023-01-31T17:00:00Z',
        'funding_progress': '25.5',
        'funded_amount': '25500.00',
        'url': 'https://www.kameo.se/listing/investment-option/123',
        'borrower_type': 'company',
        'loan_type': 'real_estate',
        'risk_grade': 'B',
        'duration_months': 24
    }


@pytest.fixture
def sample_loan_object():
    """Sample LoanCreate object for testing."""
    return LoanCreate(
        loan_id="123",
        title="Test Loan - Real Estate Investment",
        amount=Decimal("100000.00"),
        interest_rate=Decimal("5.5"),
        status=LoanStatus.OPEN,
        description="A test loan for real estate investment",
        open_date=datetime(2023, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        close_date=datetime(2023, 1, 31, 17, 0, 0, tzinfo=timezone.utc),
        funding_progress=Decimal("25.5"),
        funded_amount=Decimal("25500.00"),
        url="https://www.kameo.se/listing/investment-option/123",
        borrower_type="company",
        loan_type="real_estate",
        risk_grade="B",
        duration_months=24
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 