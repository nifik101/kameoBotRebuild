import pytest
from unittest.mock import Mock, patch
import responses
import requests
# No longer need importlib or module reload
# import importlib 
# import config as config_module
from src.config import KameoConfig # Import the class directly
from src.auth import KameoAuthenticator
from src.kameo_client import KameoClient


@pytest.fixture
def mock_env_dict(): # Renamed to avoid confusion, provides dict
    """Provides test configuration values as a dictionary."""
    return {
        'email': 'test@example.com',
        'password': 'testpassword123',
        'totp_secret': 'JBSWY3DPEHPK3PXP', # Use model field names
        'base_url': 'https://test.kameo.se'
    }

@pytest.fixture
def config(mock_env_dict): # Use the dict fixture
    """Test configuration fixture initialized directly from dict."""
    # Instantiate directly using test values, bypassing env var loading
    return KameoConfig(**mock_env_dict)

@pytest.fixture
def client(config):
    """Test client fixture"""
    return KameoClient(config)

def test_config_loading(mock_env_dict): # Use the dict fixture
    """Test configuration object creation from dictionary."""
    # Instantiate directly for this test too
    cfg = KameoConfig(**mock_env_dict)
    assert cfg.email == mock_env_dict['email']
    assert cfg.password == mock_env_dict['password']
    assert cfg.base_url == mock_env_dict['base_url']
    # Optional: Check default values if needed
    # assert cfg.connect_timeout == 5.0

def test_2fa_generation(config): # Use the config fixture
    """Test 2FA code generation using config fixture."""
    # Use the config object from the fixture
    auth = KameoAuthenticator(totp_secret=config.totp_secret)
    code = auth.get_2fa_code()
    assert code is not None
    assert len(code) == 6
    assert code.isdigit()

def test_2fa_verification(config): # Use the config fixture
    """Test 2FA code verification using config fixture."""
    auth = KameoAuthenticator(totp_secret=config.totp_secret)
    code = auth.get_2fa_code()
    assert auth.verify_2fa_code(code) is True
    assert auth.verify_2fa_code("000000") is False

# The rest of the tests use the client fixture, which uses the config fixture,
# so they should work correctly.
@responses.activate
def test_login_flow(client, config):
    """Test the complete login flow"""
    # Mock login page
    responses.add(
        responses.GET,
        f"{config.base_url}/user/login",
        status=200,
        body=""
    )
    
    # Mock login post
    responses.add(
        responses.POST,
        f"{config.base_url}/user/login",
        status=302,
        headers={'Location': '/auth/2fa'}
    )
    
    # Mock 2FA page
    responses.add(
        responses.GET,
        f"{config.base_url}/auth/2fa",
        status=200,
        body='''
            <html><body>
                <form action="/auth/2fa" method="post">
                    <input type="hidden" name="ezxform_token" value="mock_token_value" />
                    <input type="text" name="AuthCode" />
                    <button type="submit" name="ValidateButton"></button>
                </form>
            </body></html>
        '''
    )
    
    # Mock 2FA submission
    responses.add(
        responses.POST,
        f"{config.base_url}/auth/2fa",
        status=302,
        headers={'Location': '/investor/dashboard'}
    )
    
    # Mock dashboard
    responses.add(
        responses.GET,
        f"{config.base_url}/investor/dashboard",
        status=200,
        body='<div class="account-number">12345</div>'
    )
    
    assert client.login() is True
    assert client.handle_2fa() is True
    assert client.get_account_number() == "12345"

@responses.activate
def test_redirect_handling(client, config):
    """Test proper handling of redirects"""
    # Mock a chain of redirects
    responses.add(
        responses.GET,
        f"{config.base_url}/start",
        status=301,
        headers={'Location': f"{config.base_url}/middle"}
    )
    
    responses.add(
        responses.GET,
        f"{config.base_url}/middle",
        status=302,
        headers={'Location': f"{config.base_url}/end"}
    )
    
    responses.add(
        responses.GET,
        f"{config.base_url}/end",
        status=200,
        body="final"
    )
    
    response = client._make_request('GET', '/start')
    assert response.status_code == 200
    assert response.text == "final"

def test_request_timeout(client):
    """Test timeout handling"""
    with patch('requests.Session') as mock_session:
        session = Mock()
        session.request.side_effect = requests.exceptions.Timeout
        mock_session.return_value = session
        
        client.session = session
        with pytest.raises(requests.exceptions.Timeout):
            client._make_request('GET', '/timeout') 