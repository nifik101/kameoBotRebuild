"""Configuration module for Kameo client settings."""

from typing import Optional
from urllib.parse import urljoin

from pydantic import Field, HttpUrl, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class KameoConfig(BaseSettings):
    """Configuration for Kameo client, loaded from environment variables."""
    
    email: str = Field(..., description="User's email address for Kameo login.")
    password: str = Field(..., description="User's password for Kameo login.")
    # Use str for default and validate format with a validator
    base_url: str = Field(
        default="https://www.kameo.se", 
        description="Base URL for Kameo API/website."
    )
    connect_timeout: float = Field(
        default=5.0, 
        description="Timeout in seconds for establishing connection."
    )
    read_timeout: float = Field(
        default=10.0, 
        description="Timeout in seconds for waiting for data."
    )
    max_redirects: int = Field(
        default=5, 
        description="Maximum number of redirects to follow."
    )
    totp_secret: Optional[str] = Field(
        default=None, 
        description="Base32-encoded TOTP secret for 2FA."
    )
    user_agent: str = Field(
        default="KameoBot/1.0 (Python Requests)", 
        description="User-Agent header to send with requests."
    )

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate that base_url is a valid HTTP/HTTPS URL."""
        try:
            # Try to parse as HttpUrl for validation
            HttpUrl(v)
            return v
        except ValidationError:
            raise ValueError(f"'{v}' is not a valid HTTP/HTTPS URL")

    def get_full_url(self, path: str) -> str:
        """Create a complete URL by combining base URL with a relative path."""
        # urljoin handles path combination correctly, including slashes
        return urljoin(self.base_url, path)

    model_config = SettingsConfigDict(
        # Prefix for environment variables (e.g. KAMEO_EMAIL)
        env_prefix="KAMEO_",
        # Allow case-insensitive environment variables
        case_sensitive=False,  # Changed to False, more common and less error-prone
        # Read from .env file automatically (if python-dotenv is installed)
        env_file='.env', 
        env_file_encoding='utf-8',
        extra='ignore'
    ) 