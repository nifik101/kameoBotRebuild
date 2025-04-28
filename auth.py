import pyotp
import logging
import base64
from typing import Optional
from datetime import datetime, timezone # Importera datetime och timezone

class KameoAuthenticator:
    """Hanterar autentisering inklusive 2FA (TOTP) för Kameo."""
    
    def __init__(self, totp_secret: Optional[str] = None):
        """
        Initialiserar autentiseraren med TOTP-hemligheten.

        Args:
            totp_secret: Base32-kodad TOTP-hemlighet.
        """
        self.totp_secret: Optional[str] = totp_secret
        self._totp: Optional[pyotp.TOTP] = None
        
        if totp_secret:
            # Försök normalisera hemligheten för att säkerställa korrekt format
            normalized_secret = self._normalize_secret(totp_secret)
            
            if normalized_secret:
                # Skapa standard TOTP-objekt (SHA1, 6 siffror, 30s intervall)
                self._totp = pyotp.TOTP(normalized_secret)
                # Logga endast delar av hemligheten av säkerhetsskäl
                logging.info(f"TOTP-autentiserare initierad med hemlighet: {normalized_secret[:3]}...{normalized_secret[-3:]}")
                
                # Logga verifierings-URL för enkel testning med authenticator-appar
                # Använd ett generiskt användarnamn, e-posten är inte kritisk här
                try:
                    provisioning_uri = self._totp.provisioning_uri("user@kameo-script", issuer_name="Kameo Script")
                    logging.info(f"TOTP Provisioning URI (för test): {provisioning_uri}")
                except Exception as e:
                    logging.warning(f"Kunde inte generera provisioning URI: {e}")
            else:
                logging.error("Misslyckades med att normalisera TOTP-hemligheten. Kontrollera att den är korrekt Base32-kodad.")
        else:
            logging.warning("Ingen TOTP-hemlighet angiven. 2FA kommer inte att fungera.")

    def _normalize_secret(self, secret: str) -> Optional[str]:
        """
        Normaliserar hemligheten för att säkerställa Base32-format och ta bort ogiltiga tecken.

        Args:
            secret: Den råa hemlighetssträngen.

        Returns:
            Den normaliserade Base32-strängen, eller None om normalisering misslyckas.
        """
        try:
            # Ta bort mellanslag och konvertera till versaler
            cleaned = secret.replace(" ", "").upper()
            
            # Kontrollera om strängen endast innehåller giltiga Base32-tecken
            valid_base32_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
            if not all(c in valid_base32_chars for c in cleaned):
                logging.warning("Hemligheten innehåller ogiltiga tecken för Base32. Försöker filtrera.")
                cleaned = "".join(filter(lambda c: c in valid_base32_chars, cleaned))
                if not cleaned:
                    logging.error("Hemligheten är tom efter filtrering av ogiltiga tecken.")
                    return None

            # Säkerställ korrekt padding för Base32-avkodning
            padding_needed = (8 - len(cleaned) % 8) % 8
            padded_secret = cleaned + '=' * padding_needed

            # Försök avkoda för att validera formatet
            base64.b32decode(padded_secret, casefold=True)
            
            # Returnera den rensade hemligheten (utan padding, då pyotp hanterar det)
            logging.info("TOTP-hemlighet normaliserad.")
            return cleaned 
            
        except Exception as e:
            logging.error(f"Fel vid normalisering av Base32-hemlighet: {e}")
            return None
    
    def get_2fa_code(self) -> Optional[str]:
        """
        Genererar den nuvarande 2FA-koden (TOTP).

        Returns:
            Den 6-siffriga TOTP-koden som en sträng, eller None om ingen hemlighet är konfigurerad eller om ett fel uppstår.
        """
        if self._totp:
            try:
                code = self._totp.now()
                logging.info(f"Genererad TOTP-kod: {code}")
                return code
            except Exception as e:
                logging.error(f"Kunde inte generera TOTP-kod: {e}")
                return None
        else:
            logging.warning("Försökte generera 2FA-kod men ingen TOTP-hemlighet är konfigurerad.")
            return None
        
    def verify_2fa_code(self, code: str, for_time: Optional[int] = None, valid_window: int = 1) -> bool:
        """
        Verifierar om en given 2FA-kod är giltig för den aktuella tiden (eller en specifik tidpunkt).

        Args:
            code: Koden som ska verifieras.
            for_time: Tidsstämpel (sekunder sedan epoch) att verifiera mot. Använder aktuell tid om None.
            valid_window: Antal tidsintervall (30s) framåt och bakåt som koden är giltig för. 
                          Standard är 1 (nuvarande, föregående, nästa intervall).

        Returns:
            True om koden är giltig, annars False.
        """
        if not self._totp:
            logging.warning("Försökte verifiera 2FA-kod men ingen TOTP-hemlighet är konfigurerad.")
            return False
            
        try:
            # Konvertera tidsstämpel till datetime-objekt om nödvändigt
            target_dt: Optional[datetime] = None
            if for_time is not None:
                try:
                    # Antag att for_time är en Unix-tidsstämpel (sekunder sedan epoch)
                    target_dt = datetime.fromtimestamp(for_time, tz=timezone.utc)
                except TypeError:
                     logging.error(f"Ogiltigt format för for_time: {for_time}. Förväntade sig en numerisk tidsstämpel.")
                     return False
                     
            # Anropa verify med korrekt typ (datetime eller None)
            is_valid = self._totp.verify(code, for_time=target_dt, valid_window=valid_window)
            
            if is_valid:
                logging.info(f"Verifiering av kod '{code}' lyckades.")
            else:
                logging.info(f"Verifiering av kod '{code}' misslyckades.")
            return is_valid
        except Exception as e:
             logging.error(f"Fel vid verifiering av TOTP-kod: {e}")
             return False
        
    @staticmethod
    def generate_new_secret() -> str:
        """Genererar en ny slumpmässig Base32 TOTP-hemlighet."""
        new_secret = pyotp.random_base32()
        logging.info(f"Ny TOTP-hemlighet genererad: {new_secret}")
        return new_secret

# Kommentar: Tog bort metoderna get_alternative_codes, get_multiple_algorithm_codes, _custom_hotp 
# då standard TOTP visade sig fungera och detta förenklar koden avsevärt.
# Förbättrade normaliseringen av hemligheten och lade till mer robust felhantering och loggning.
# Uppdaterade docstrings till svenska. 