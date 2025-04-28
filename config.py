from pydantic import Field, HttpUrl, validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import urljoin

class KameoConfig(BaseSettings):
    """Konfiguration för Kameo-klienten, laddad från miljövariabler."""
    
    email: str = Field(..., description="Användarens e-postadress för Kameo-inloggning.")
    password: str = Field(..., description="Användarens lösenord för Kameo-inloggning.")
    # Använd str för default och validera formatet med en validator
    base_url: str = Field(default="https://www.kameo.se", description="Bas-URL för Kameo API/webbplats.")
    connect_timeout: float = Field(default=5.0, description="Timeout i sekunder för att etablera anslutning.")
    read_timeout: float = Field(default=10.0, description="Timeout i sekunder för att vänta på data.")
    max_redirects: int = Field(default=5, description="Maximalt antal omdirigeringar att följa.")
    totp_secret: Optional[str] = Field(default=None, description="Base32-kodad TOTP-hemlighet för 2FA.")
    user_agent: str = Field(default="KameoBot/1.0 (Python Requests)", description="User-Agent header att skicka med requests.")

    @validator('base_url')
    def validate_base_url(cls, v: str) -> str:
        """Validerar att base_url är en giltig HTTP/HTTPS URL."""
        try:
            # Försök att parsea som en HttpUrl för validering
            HttpUrl(v)
            return v
        except ValidationError:
            raise ValueError(f"'{v}' is not a valid HTTP/HTTPS URL")

    def get_full_url(self, path: str) -> str:
        """Skapar en fullständig URL genom att kombinera bas-URL med en relativ sökväg."""
        # urljoin hanterar sammanslagning av sökvägar korrekt, inklusive snedstreck
        return urljoin(self.base_url, path)

    model_config = SettingsConfigDict(
        # Prefix för miljövariabler (t.ex. KAMEO_EMAIL)
        env_prefix="KAMEO_",
        # Tillåt skiftlägeskänsliga miljövariabler
        case_sensitive=False, # Ändrat till False, vanligare och mindre felbenäget
        # Läs från .env-fil automatiskt (om python-dotenv är installerat)
        env_file='.env', 
        env_file_encoding='utf-8'
    ) 