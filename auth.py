import pyotp
import time
import logging
import hmac
import hashlib
import base64
import struct
from typing import Optional, List, Dict, Any

class KameoAuthenticator:
    """Handles authentication including 2FA for Kameo"""
    
    def __init__(self, totp_secret: Optional[str] = None):
        self.totp_secret = totp_secret
        self._totp = None
        
        if totp_secret:
            # Try to normalize the secret if needed
            normalized_secret = self._normalize_secret(totp_secret)
            
            if normalized_secret:
                # Standard TOTP with 30 second interval
                self._totp = pyotp.TOTP(normalized_secret)
                logging.info(f"TOTP authenticator initialized with secret: {normalized_secret[:3]}...{normalized_secret[-3:]}")
                
                # Log verification URL for testing with Google Authenticator
                provisioning_uri = self._totp.provisioning_uri("kameo@example.com", issuer_name="Kameo")
                logging.info(f"TOTP provisioning URI: {provisioning_uri}")
            else:
                logging.error("Failed to normalize TOTP secret")
    
    def _normalize_secret(self, secret: str) -> Optional[str]:
        """Normalize the secret to ensure it's in the correct format"""
        try:
            # Remove spaces and convert to uppercase
            cleaned = secret.replace(" ", "").upper()
            
            # Check if it's a valid base32 string
            try:
                base64.b32decode(cleaned, casefold=True)
                return cleaned
            except Exception:
                logging.warning("Secret does not appear to be valid base32, trying to convert...")
            
            # Try to convert from other formats if needed
            # For example, if it's hex encoded
            if all(c in "0123456789ABCDEFabcdef" for c in cleaned):
                try:
                    # Convert hex to bytes, then encode as base32
                    hex_bytes = bytes.fromhex(cleaned)
                    base32_str = base64.b32encode(hex_bytes).decode('utf-8')
                    return base32_str
                except Exception:
                    logging.warning("Failed to convert from hex to base32")
            
            return None
        except Exception as e:
            logging.error(f"Error normalizing secret: {e}")
            return None
    
    def get_2fa_code(self) -> Optional[str]:
        """Generate current 2FA code if secret is configured"""
        if self._totp:
            code = self._totp.now()
            logging.info(f"Generated TOTP code: {code}")
            return code
        return None
    
    def get_alternative_codes(self, time_skew_seconds: int = 60) -> List[str]:
        """
        Generate alternative TOTP codes for times around current time.
        Useful when there's time skew between server and client.
        
        Args:
            time_skew_seconds: Maximum time skew to account for in seconds
            
        Returns:
            List of possible codes around current time
        """
        codes: List[str] = []
        if not self._totp:
            return codes
            
        # Current time
        current_time = int(time.time())
        logging.info(f"Current time: {current_time}")
        
        # Generate codes for times around current time
        for offset in range(-time_skew_seconds, time_skew_seconds + 1, 30):
            if offset == 0:
                continue  # Skip current time (already returned by get_2fa_code)
                
            # Generate code for time with offset
            offset_time = current_time + offset
            code = self._totp.at(offset_time)
            codes.append(code)
            logging.info(f"Generated code for time offset {offset} seconds: {code}")
            
        # Also try with different digest algorithms
        try:
            if self.totp_secret:
                normalized_secret = self._normalize_secret(self.totp_secret)
                if normalized_secret:
                    # Try SHA256 instead of default SHA1
                    totp_sha256 = pyotp.TOTP(normalized_secret, digest=hashlib.sha256)
                    code_sha256 = totp_sha256.now()
                    codes.append(code_sha256)
                    logging.info(f"Generated code with SHA256: {code_sha256}")
                    
                    # Try with 8 digits instead of 6
                    totp_8digits = pyotp.TOTP(normalized_secret, digits=8)
                    code_8digits = totp_8digits.now()
                    codes.append(code_8digits)
                    logging.info(f"Generated 8-digit code: {code_8digits}")
        except Exception as e:
            logging.warning(f"Error generating alternative algorithm codes: {e}")
            
        return codes
    
    def get_multiple_algorithm_codes(self) -> Dict[str, str]:
        """
        Generate TOTP codes with different algorithms and settings
        
        Returns:
            Dictionary of format {description: code}
        """
        results: Dict[str, str] = {}
        if not self.totp_secret:
            return results
            
        normalized_secret = self._normalize_secret(self.totp_secret)
        if not normalized_secret:
            return results
            
        try:
            # Standard algorithm (SHA1, 6 digits, 30s interval)
            standard_totp = pyotp.TOTP(normalized_secret)
            results["standard"] = standard_totp.now()
            
            # SHA256
            sha256_totp = pyotp.TOTP(normalized_secret, digest=hashlib.sha256)
            results["sha256"] = sha256_totp.now()
            
            # SHA512
            sha512_totp = pyotp.TOTP(normalized_secret, digest=hashlib.sha512)
            results["sha512"] = sha512_totp.now()
            
            # Different digit lengths
            digits7_totp = pyotp.TOTP(normalized_secret, digits=7)
            results["7digits"] = digits7_totp.now()
            
            digits8_totp = pyotp.TOTP(normalized_secret, digits=8)
            results["8digits"] = digits8_totp.now()
            
            # Different intervals
            interval60_totp = pyotp.TOTP(normalized_secret, interval=60)
            results["60s_interval"] = interval60_totp.now()
            
            # Custom HOTP implementation as fallback
            counter = int(time.time()) // 30
            results["custom_hotp"] = self._custom_hotp(normalized_secret, counter)
            
        except Exception as e:
            logging.error(f"Error generating multi-algorithm codes: {e}")
            
        for desc, code in results.items():
            logging.info(f"Generated code with {desc}: {code}")
            
        return results
    
    def _custom_hotp(self, secret: str, counter: int, digits: int = 6) -> str:
        """
        Custom HOTP implementation as a fallback
        
        Args:
            secret: Base32 encoded secret
            counter: Counter value
            digits: Number of digits in the code
            
        Returns:
            HOTP code
        """
        try:
            # Decode the base32 secret
            key = base64.b32decode(secret, casefold=True)
            
            # Convert counter to bytes
            counter_bytes = struct.pack(">Q", counter)
            
            # Calculate HMAC-SHA1
            h = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            
            # Dynamic truncation
            offset = h[-1] & 0x0F
            binary = ((h[offset] & 0x7F) << 24 |
                     (h[offset + 1] & 0xFF) << 16 |
                     (h[offset + 2] & 0xFF) << 8 |
                     (h[offset + 3] & 0xFF))
            
            # Generate code
            code = binary % (10 ** digits)
            return str(code).zfill(digits)
        except Exception as e:
            logging.error(f"Error in custom HOTP: {e}")
            return ""
        
    @staticmethod
    def generate_new_secret() -> str:
        """Generate a new TOTP secret key"""
        return pyotp.random_base32()
    
    def verify_2fa_code(self, code: str) -> bool:
        """Verify if a given 2FA code is valid"""
        if not self._totp:
            return False
        return self._totp.verify(code) 