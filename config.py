from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import urljoin

class KameoConfig(BaseSettings):
    """Configuration for Kameo client"""
    email: str
    password: str
    base_url: str = "https://www.kameo.se"
    connect_timeout: float = 5.0
    read_timeout: float = 10.0
    max_redirects: int = 5
    totp_secret: Optional[str] = None
    user_agent: str = "KameoBot/1.0 (Python Requests)"

    def get_full_url(self, path: str) -> str:
        """Helper to join base URL with path"""
        return urljoin(self.base_url, path)

    model_config = SettingsConfigDict(
        env_prefix="KAMEO_",
        case_sensitive=True
    ) 