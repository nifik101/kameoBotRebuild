"""
TOTP Authentication module for Kameo integration.

This module provides functionality for generating and verifying Time-based One-Time Passwords (TOTP)
for two-factor authentication with Kameo's platform.
"""

import pyotp
import logging

logger = logging.getLogger(__name__)


class KameoAuthenticator:
    """
    Handles TOTP (Time-based One-Time Password) authentication for Kameo.
    
    This class provides methods to generate and verify 2FA codes using the TOTP standard,
    which is compatible with authenticator apps like Google Authenticator, Authy, etc.
    """
    
    def __init__(self, totp_secret: str):
        """
        Initialize the authenticator with a TOTP secret.
        
        Args:
            totp_secret: Base32-encoded TOTP secret from Kameo's 2FA setup
        """
        self.totp_secret = self._normalize_secret(totp_secret)
        self.totp = pyotp.TOTP(self.totp_secret)
    
    def _normalize_secret(self, secret: str) -> str:
        """
        Normalize the TOTP secret by removing spaces and ensuring proper padding.
        
        Args:
            secret: Raw TOTP secret string
            
        Returns:
            Normalized Base32 secret
        """
        # Remove spaces and convert to uppercase
        normalized = secret.replace(' ', '').upper()
        
        # Ensure proper Base32 padding
        while len(normalized) % 8 != 0:
            normalized += '='
        
        return normalized
    
    def get_2fa_code(self) -> str:
        """
        Generate a current TOTP code.
        
        Returns:
            6-digit TOTP code as string
        """
        code = self.totp.now()
        logger.debug(f"Generated 2FA code: {code}")
        # Logga verifierings-URL för enkel testning med authenticator-appar
        verification_url = self.totp.provisioning_uri(
            name="Kameo",
            issuer_name="Kameo Authentication"
        )
        logger.debug(f"TOTP provisioning URL: {verification_url}")
        return code
    
    def verify_2fa_code(self, code: str) -> bool:
        """
        Verify a TOTP code against the current time window.
        
        Args:
            code: 6-digit TOTP code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            is_valid = self.totp.verify(code)
            logger.debug(f"2FA code {code} verification: {'valid' if is_valid else 'invalid'}")
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying 2FA code: {e}")
            return False 