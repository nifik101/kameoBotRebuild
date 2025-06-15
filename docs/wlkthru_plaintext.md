## Kameo Klient Dokumentation

**Inledning**
Denna kod implementerar en Python-klient för att automatisera interaktioner med Kameos webbplats, specifikt inloggning (inklusive 2FA) och hämtning av kontonummer. Konfiguration hanteras via miljövariabler för flexibilitet.

**Vad gör koden?**

*   **Konfiguration (`config.py`):** Laddar och validerar konfigurationsparametrar (e-post, lösenord, URL, timeouts, TOTP-hemlighet) från miljövariabler eller `.env`-fil.
*   **Autentisering (`auth.py`):** Hanterar generering och validering av TOTP-koder (Time-based One-Time Password) för tvåfaktorsautentisering (2FA).
*   **Klientlogik (`kameo_client.py`):**
    *   Orkestrerar inloggningsflödet genom att göra HTTP GET/POST-anrop till Kameos inloggnings- och 2FA-sidor.
    *   Använder `requests.Session` för att behålla cookies mellan anrop.
    *   Extraherar nödvändig information (t.ex. formulär-tokens) från HTML med `BeautifulSoup`.
    *   Hämtar kontonumret från användarens dashboard efter lyckad inloggning.
    *   Innehåller en `main`-funktion för att demonstrera användningen.
*   **Testning (`test_kameo.py`):** Innehåller enhetstester med `pytest` och `responses` för att verifiera konfigurationsladdning, 2FA-logik och det simulerade inloggningsflödet utan att göra riktiga nätverksanrop.

**Varför gör vi så?**

*   **Konfiguration (`config.py`):**
    *   `pydantic/BaseSettings`: Ger typ-säkerhet, automatisk validering och enkel laddning från miljövariabler/`.env`-fil, vilket minskar risken för felkonfiguration och förenklar driftsättning.
    *   Specifika fält (t.ex. `email`, `password`) är obligatoriska (`...`) för att säkerställa att nödvändig data finns.
    *   `@validator`: Används för anpassad validering (t.ex. att `base_url` är en giltig URL) utöver Pydantics inbyggda kontroller.
    *   `get_full_url`: Centraliserar logiken för att skapa URL:er, vilket gör koden mer robust mot felaktiga sökvägar.
*   **Autentisering (`auth.py`):**
    *   `pyotp`: Standardbibliotek för TOTP, vältestat och pålitligt.
    *   Normalisering av hemlighet (`_normalize_secret`): Ökar robustheten genom att hantera vanliga formateringsproblem (mellanslag, skiftläge, padding) i Base32-hemligheter.
    *   Separation av `Authenticator`-klass: Håller autentiseringslogiken isolerad från klientens HTTP-interaktioner, vilket förbättrar modularitet och testbarhet.
*   **Klientlogik (`kameo_client.py`):**
    *   `requests.Session`: Effektivt för att hantera cookies och anslutningspooler automatiskt, vilket är nödvändigt för webbinteraktioner som kräver inloggning.
    *   `BeautifulSoup`: Kraftfullt bibliotek för att parsa och navigera i HTML, nödvändigt för att extrahera tokens och data från webbsidor utan ett formellt API.
    *   `_make_request`: Centraliserar logiken för att göra HTTP-anrop, hantera timeouts, sätta headers och grundläggande felhantering (t.ex. `raise_for_status`), vilket minskar kodduplicering.
    *   Detaljerad loggning (`logging`): Hjälper till med felsökning genom att ge insikt i flödet och eventuella problem under körning.
    *   Stegvis inloggning (`login`, `handle_2fa`): Bryter ner den komplexa processen i logiska delar, vilket gör koden lättare att följa och underhålla.
*   **Testning (`test_kameo.py`):**
    *   `pytest`: Modernt och flexibelt testramverk för Python. Fixtures (`@pytest.fixture`) gör det enkelt att återanvända testdata och objekt (som `config` och `client`).
    *   `responses`: Möjliggör simulering av HTTP-svar utan att behöva köra en riktig webbserver eller göra externa anrop, vilket gör testerna snabba, isolerade och pålitliga.
    *   `unittest.mock.patch`: Används för att ersätta delar av koden (som `requests.Session`) under testning, t.ex. för att simulera nätverksfel som timeouts.

**Specialkomponenter**

*   **Decorator (`@validator`, `@classmethod`, `@staticmethod`, `@pytest.fixture`, `@responses.activate`):**
    *   *Vad:* En funktion som modifierar eller utökar beteendet hos en annan funktion eller metod. Den "dekorerar" den ursprungliga funktionen.
    *   *Varför:* Används för att lägga till återanvändbar funktionalitet (t.ex. Pydantic-validering med `@validator`, skapa klassmetoder med `@classmethod`), definiera testuppsättningar (`@pytest.fixture`) eller aktivera kontext (`@responses.activate`) på ett deklarativt och läsbart sätt.
*   **`BaseSettings` (från `pydantic-settings`):**
    *   *Vad:* En basklass från Pydantic specifikt designad för att hantera applikationskonfiguration.
    *   *Varför:* Gör det extremt enkelt att definiera konfigurationsparametrar med Python-typer, få automatisk validering och ladda värden från miljövariabler och `.env`-filer med minimal kod. Förbättrar robusthet och underhållbarhet jämfört med manuell hantering av miljövariabler.
*   **`requests.Session`:**
    *   *Vad:* Ett objekt från `requests`-biblioteket som bibehåller tillstånd mellan flera HTTP-anrop till samma domän.
    *   *Varför:* Nödvändigt för webb-skrapning och interaktioner med webbplatser som kräver inloggning, eftersom det automatiskt hanterar cookies (som sessions-ID) och kan optimera anslutningar.
*   **`BeautifulSoup`:**
    *   *Vad:* Ett Python-bibliotek för att parsa HTML- och XML-dokument.
    *   *Varför:* Används för att navigera i HTML-strukturen på Kameos sidor och extrahera specifik data, som `ezxform_token` från 2FA-formuläret och kontonumret från dashboarden, när ett formellt API saknas.
*   **`pyotp`:**
    *   *Vad:* Ett Python-bibliotek för att generera och verifiera engångslösenord, inklusive TOTP (som används i många 2FA-system).
    *   *Varför:* Implementerar den standardiserade algoritmen för TOTP, vilket möjliggör korrekt generering och verifiering av 2FA-koder baserat på en delad hemlighet och aktuell tid.
