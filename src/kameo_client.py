from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup, Tag
import logging
import time
from typing import Optional
import re # Importeras för get_account_number

# Importera konfiguration och autentiserare från src-paketet
from src.config import KameoConfig
from src.auth import KameoAuthenticator
from pydantic import ValidationError

# Ladda miljövariabler från .env-fil. 
# Pydantic-settings laddar också, men detta säkerställer att de finns *innan* Pydantic-instansiering 
# och att de skriver över existerande variabler om override=True.
load_dotenv(override=True)

# Konfigurera loggning globalt
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s' # Lade till filnamn/radnummer
)

class KameoClient:
    """Klient för att interagera med Kameos webbplats, hantera inloggning och hämta kontonummer."""
    
    def __init__(self, config: KameoConfig):
        """
        Initialiserar klienten med konfiguration och en session.

        Args:
            config: Ett KameoConfig-objekt med nödvändiga inställningar.
        """
        self.config = config
        self.session = requests.Session()
        if config.totp_secret:
            self.authenticator: Optional[KameoAuthenticator] = KameoAuthenticator(config.totp_secret)
        else:
            self.authenticator: Optional[KameoAuthenticator] = None
        
        # Sätt User-Agent och Accept-header för sessionen
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        })
        
        # Sätt maximalt antal omdirigeringar för sessionen
        self.session.max_redirects = config.max_redirects
        logging.info(f"KameoClient initialiserad för {config.email} på {config.base_url}")

    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Intern hjälpmetod för att göra HTTP-requests med sessionen.
        Hanterar URL-konstruktion, timeouts och grundläggande felhantering.

        Args:
            method: HTTP-metod (t.ex. 'GET', 'POST').
            path: Relativ sökväg för requesten (t.ex. '/user/login').
            **kwargs: Ytterligare argument att skicka till requests.Session.request.

        Returns:
            Ett requests.Response-objekt.

        Raises:
            requests.exceptions.RequestException: Om requesten misslyckas av någon anledning.
        """
        full_url = self.config.get_full_url(path)
        timeout = (self.config.connect_timeout, self.config.read_timeout)
        
        logging.debug(f"Gör request: {method} {full_url}") # Använd debug-nivå för detaljerad info
        try:
            response = self.session.request(
                method=method,
                url=full_url,
                timeout=timeout,
                allow_redirects=True, # Standard för sessionen, men tydliggör
                **kwargs
            )
            # Kasta exception för HTTP-fel (statuskod 4xx eller 5xx)
            response.raise_for_status() 
            logging.debug(f"Mottog svar: {response.status_code} från {response.url}")
            return response
            
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout vid request till {full_url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Request till {full_url} misslyckades: {e}")
            # Logga eventuellt svar om det finns, kan ge mer info vid t.ex. 4xx/5xx fel
            if e.response is not None:
                 logging.error(f"Fel-respons status: {e.response.status_code}, innehåll: {e.response.text[:500]}...") # Logga början av svaret
            raise

    def login(self) -> bool:
        """
        Utför det initiala inloggningssteget med användarnamn och lösenord.

        Returns:
            True om inloggningen lyckades (ledde till 2FA-sidan eller dashboard), annars False.
        """
        login_path = '/user/login'
        logging.info(f"Påbörjar inloggning för {self.config.email}...")
        try:
            # Steg 1: Hämta inloggningssidan för att få cookies och eventuell CSRF-token
            # Använd _make_request som hanterar grundläggande fel
            login_get_response = self._make_request('GET', login_path)
            
            # Försök extrahera CSRF-token (även om den inte verkar användas i detta flöde, bra att ha kvar)
            soup = BeautifulSoup(login_get_response.text, 'html.parser')
            csrf_token: Optional[str] = None
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if isinstance(csrf_meta, Tag) and csrf_meta.has_attr('content'):
                token_value = csrf_meta.get('content')
                if isinstance(token_value, str):
                    csrf_token = token_value
                    logging.info(f"Hittade CSRF-token: {csrf_token[:5]}...") # Logga bara början
                
            # Steg 2: Skicka inloggningsuppgifter
            payload = {
                'Login': self.config.email,
                'Password': self.config.password,
                'LoginButton': '', # Namnet på submit-knappen
                'RedirectURI': ''  # Verkar inte användas men skickas med
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.config.get_full_url(login_path),
                'Origin': self.config.base_url # Viktig header enligt Postman-analys
            }
            
            # Lägg till CSRF-token i header om den hittades (för framtida bruk?)
            if csrf_token:
                headers['X-CSRF-Token'] = csrf_token
            
            logging.info("Skickar inloggningsuppgifter...")
            # Använd session.request direkt här då _make_request alltid följer redirects,
            # men vi behöver analysera det *omedelbara* svaret efter POST.
            # Vi behöver dock fortfarande timeouts.
            response = self.session.request(
                method='POST',
                url=self.config.get_full_url(login_path),
                data=payload,
                headers=headers,
                timeout=(self.config.connect_timeout, self.config.read_timeout),
                allow_redirects=True # Följ redirects som normalt efter POST
            )
            response.raise_for_status() # Kontrollera för HTTP-fel
            
            logging.info(f"Svar efter inloggnings-POST: Status={response.status_code}, URL={response.url}")
            
            # Kontrollera om vi hamnade på 2FA-sidan eller direkt på dashboard
            if '/auth/2fa' in response.url:
                logging.info("Inloggning lyckades, omdirigerad till 2FA-sidan.")
                return True
            elif '/investor/dashboard' in response.url:
                logging.info("Inloggning lyckades, omdirigerad direkt till dashboard (2FA kanske ej aktiv?).")
                return True
            else:
                # Oväntat resultat, logga och misslyckas
                logging.error(f"Oväntad URL efter inloggning: {response.url}")
                logging.error(f"Response text (start): {response.text[:500]}...")
                return False
            
        except requests.exceptions.RequestException as e:
            # Fel loggas redan i _make_request eller i POST-anropet ovan
            logging.error(f"Inloggningsprocessen misslyckades: {e}")
            return False

    def handle_2fa(self) -> bool:
        """
        Hanterar 2FA-autentisering med TOTP-kod enligt det fungerande Postman-flödet.
        Hämtar 2FA-sidan, extraherar token, och skickar koden.

        Returns:
            True om 2FA-autentiseringen lyckades, annars False.
        """
        auth_path = '/auth/2fa'
        logging.info("Påbörjar 2FA-hantering...")
        try:
            # Steg 1: Hämta 2FA-sidan för att få en färsk ezxform_token
            logging.info(f"Hämtar {auth_path} för att få 2FA-formulär/token...")
            get_response = self._make_request('GET', auth_path)

            # Steg 2: Extrahera ezxform_token från formuläret
            soup = BeautifulSoup(get_response.text, 'html.parser')
            form = soup.find('form', {'action': auth_path})
            if not isinstance(form, Tag):
                logging.error(f"Kunde inte hitta 2FA-formulär med action='{auth_path}' på sidan {get_response.url}")
                logging.debug(f"Sidans innehåll (start): {get_response.text[:500]}...")
                return False

            token_input = form.find('input', {'name': 'ezxform_token'})
            ezxform_token: Optional[str] = None
            if isinstance(token_input, Tag) and token_input.has_attr('value'):
                 token_value = token_input.get('value')
                 if isinstance(token_value, str) and token_value:
                      ezxform_token = token_value
                      logging.info(f"Hittade ezxform_token: {ezxform_token}")
                 else:
                     logging.warning("Hittade ezxform_token-input men värdet saknas eller är inte en sträng.")
            
            if not ezxform_token:
                 logging.error("Kunde inte extrahera ett giltigt 'ezxform_token' från 2FA-formuläret.")
                 return False

            # Steg 3: Generera standard TOTP-kod
            code = self.authenticator.get_2fa_code()
            if not code:
                logging.error("Kunde inte generera 2FA-kod. Kontrollera TOTP-hemligheten i konfigurationen.")
                return False

            # Steg 4: Skicka 2FA-koden och token
            payload = {
                'ezxform_token': ezxform_token,
                'code': code,
                'submit_code': '' # Namnet på submit-knappen ("Fortsätt")
            }
            
            logging.info(f"Skickar 2FA-kod ({code})...")
            response = self._make_request(
                method='POST',
                path=auth_path,
                data=payload,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': get_response.url, # Referer från GET-requesten
                    'Origin': self.config.base_url # Viktig header
                }
            )
            
            logging.info(f"Svar efter 2FA-POST: Status={response.status_code}, URL={response.url}")

            # Steg 5: Kontrollera om autentiseringen lyckades (om vi inte är kvar på 2FA-sidan)
            if auth_path not in response.url:
                logging.info(f"2FA-autentisering lyckades med kod {code}.")
                return True
            else:
                logging.error(f"2FA-autentisering misslyckades med kod {code}. Fortfarande på URL: {response.url}")
                # Försök hitta och logga felmeddelande från sidan
                error_soup = BeautifulSoup(response.text, 'html.parser')
                # Leta efter vanliga felmeddelande-divar
                alert_danger = error_soup.find('div', class_='alert-danger') 
                if alert_danger and isinstance(alert_danger, Tag):
                    error_text = alert_danger.text.strip()
                    logging.error(f"Felmeddelande hittat på sidan: {error_text}")
                else:
                     logging.warning("Inget specifikt felmeddelande (alert-danger) hittades på 2FA-sidan efter misslyckat försök.")
                     logging.debug(f"Sidans innehåll (start): {response.text[:500]}...") # Logga början för manuell inspektion
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"2FA-hantering misslyckades: {e}")
            return False

    def get_account_number(self) -> Optional[str]:
        """
        Hämtar användarens kontonummer genom att först försöka API-anropet,
        och falla tillbaka på HTML-parsning om det misslyckas.

        Returns:
            Kontonumret som en sträng om det hittas, annars None.
        """
        # Försök först med API-anropet
        api_account_number = self.get_account_number_from_api()
        if api_account_number:
            return api_account_number
        
        # Om API misslyckas, falla tillbaka på HTML-parsning
        logging.warning("API-anropet för kontonummer misslyckades, försöker HTML-parsning...")
        return self.get_account_number_from_html()

    def get_account_number_from_api(self) -> Optional[str]:
        """
        Hämtar kontonummer via Kameos JSON-API (primär metod).

        Returns:
            Kontonumret som en sträng om det hittas, annars None.
        """
        api_path = '/ezjscore/call/kameo_transfer::init'
        logging.info("Försöker hämta kontonummer via API...")
        try:
            response = self._make_request('GET', api_path)
            
            # Försök tolka JSON-svaret
            try:
                data = response.json()
                logging.debug(f"API-svar: {data}")
                
                # Navigera genom JSON-strukturen för att hitta kontonumret
                # Baserat på observerad struktur: content -> account_number
                if isinstance(data, dict) and 'content' in data:
                    content = data['content']
                    if isinstance(content, dict) and 'account_number' in content:
                        account_number = content['account_number']
                        if isinstance(account_number, str) and account_number.strip():
                            logging.info(f"Kontonummer hämtat via API: {account_number}")
                            return account_number.strip()
                
                # Om strukturen inte matchar förväntan
                logging.warning("API-svaret har inte förväntad struktur för kontonummer")
                logging.debug(f"Fullständigt API-svar: {data}")
                return None
                
            except ValueError as e:
                logging.error(f"Kunde inte tolka API-svar som JSON: {e}")
                logging.debug(f"Raw API-svar: {response.text[:500]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"API-anrop för kontonummer misslyckades: {e}")
            return None

    def get_account_number_from_html(self) -> Optional[str]:
        """
        Hämtar kontonummer genom att parsa HTML från dashboard (fallback-metod).

        Returns:
            Kontonumret som en sträng om det hittas, annars None.
        """
        dashboard_path = '/investor/dashboard'
        logging.info("Försöker hämta kontonummer via HTML-parsning...")
        try:
            response = self._make_request('GET', dashboard_path)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Försök hitta kontonumret med CSS-selektor
            account_div = soup.select_one('.account-number')
            if account_div and isinstance(account_div, Tag):
                account_text = account_div.text.strip()
                if account_text:
                    logging.info(f"Kontonummer hämtat via HTML: {account_text}")
                    return account_text
            
            # Om CSS-selektor inte fungerar, försök med regex
            logging.warning("CSS-selektor för kontonummer misslyckades, försöker regex...")
            account_match = re.search(r'kontonummer[:\s]*(\d+)', response.text, re.IGNORECASE)
            if account_match:
                account_number = account_match.group(1)
                logging.info(f"Kontonummer hämtat via regex: {account_number}")
                return account_number
            
            logging.error("Kunde inte hitta kontonummer på dashboard-sidan")
            # Spara HTML för manuell inspektion (kommenterat för att undvika stora loggar)
            # with open('dashboard_debug.html', 'w', encoding='utf-8') as f:
            #     f.write(response.text)
            # logging.info("Dashboard HTML sparad som 'dashboard_debug.html' för manuell inspektion")
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Kunde inte hämta dashboard för kontonummer: {e}")
            return False

def load_configuration() -> Optional[KameoConfig]:
    """
    Laddar konfiguration från miljövariabler med felhantering.

    Returns:
        Ett KameoConfig-objekt om konfigurationen är giltig, annars None.
    """
    try:
        config = KameoConfig()
        logging.info("Konfiguration laddad framgångsrikt.")
        return config
    except ValidationError as e:
        logging.error(f"Konfigurationsfel: {e}")
        # Visa specifika fel för varje fält
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            logging.error(f"  {field}: {message}")
        return None
    except Exception as e:
        logging.error(f"Oväntat fel vid konfigurationsladdning: {e}")
        return None

def main():
    """Huvudfunktion för att demonstrera användningen av KameoClient."""
    logging.info("Startar Kameo-klient...")
    
    # Ladda konfiguration
    config = load_configuration()
    if not config:
        logging.error("Kunde inte ladda konfiguration. Avbryter.")
        return

    # Skapa klient och försök logga in
    client = KameoClient(config)
    
    try:
        # Steg 1: Logga in
        if not client.login():
            logging.error("Inloggning misslyckades. Avbryter.")
            return

        # Steg 2: Hantera 2FA (om nödvändigt)
        # Kontrollera om vi är på 2FA-sidan
        current_response = client._make_request('GET', '/investor/dashboard')
        if '/user/login' in current_response.url or '/auth/2fa' in current_response.url:
            logging.info("2FA krävs...")
            if not client.handle_2fa():
                logging.error("2FA-autentisering misslyckades. Avbryter.")
                return

        # Steg 3: Hämta kontonummer
        account_number = client.get_account_number()
        if account_number:
            print(f"Kontonummer: {account_number}")
            logging.info(f"Framgångsrikt hämtat kontonummer: {account_number}")
        else:
            logging.error("Kunde inte hämta kontonummer.")

    except Exception as e:
        logging.error(f"Ett oväntat fel inträffade: {e}")
    
    logging.info("Kameo-klient avslutad.")

if __name__ == "__main__":
    main() 