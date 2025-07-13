# Översikt över Kodstruktur

Detta dokument ger en kort beskrivning av huvudklasserna i Kameo Bot-projektet.

## `config.py` - `KameoConfig`

*   **Ansvar:** Hanterar all konfiguration för skriptet.
*   **Implementation:** Använder `pydantic` och `pydantic-settings` för att:
    *   Definiera förväntade konfigurationsparametrar (t.ex. `email`, `password`, `totp_secret`, `base_url`).
    *   Ange standardvärden för valfria parametrar.
    *   Läsa in värden från miljövariabler (med prefixet `KAMEO_`) och/eller en `.env`-fil.
    *   Validera datatyper och format (t.ex. att `base_url` är en giltig URL).
*   **Användning:** Ett `KameoConfig`-objekt skapas i början av `main`-funktionen i `get_it_done.py` och skickas sedan vidare till `KameoClient`.

## `auth.py` - `KameoAuthenticator`

*   **Ansvar:** Hanterar generering och validering av TOTP-koder (Time-based One-Time Password) för tvåfaktorsautentisering (2FA).
*   **Implementation:** Använder `pyotp`-biblioteket för att:
    *   Ta emot en Base32-kodad TOTP-hemlighet vid initialisering.
    *   Normalisera hemligheten för att säkerställa korrekt format.
    *   Generera den aktuella 6-siffriga TOTP-koden (`get_2fa_code`).
    *   (Innehåller även en metod för att verifiera en kod, `verify_2fa_code`, som för närvarande inte används aktivt i huvudflödet men kan vara användbar.)
*   **Användning:** Ett `KameoAuthenticator`-objekt skapas inuti `KameoClient` och används i `handle_2fa`-metoden för att få fram den kod som ska skickas till Kameo.

## `get_it_done.py` - `KameoClient`

*   **Ansvar:** Är huvudklienten som orkestrerar hela processen med att interagera med Kameos webbplats.
*   **Implementation:**
    *   Innehåller en `requests.Session` för att hantera HTTP-anrop, cookies och headers över flera requests.
    *   Tar emot ett `KameoConfig`-objekt för att få tillgång till inställningar.
    *   Skapar en instans av `KameoAuthenticator`.
    *   Har metoder för varje logiskt steg:
        *   `_make_request`: En intern hjälpmetod för att göra standardiserade HTTP-anrop med felhantering och timeouts.
        *   `login`: Hanterar det första inloggningssteget med e-post och lösenord.
        *   `handle_2fa`: Hanterar 2FA-processen (hämtar sida, extraherar token, genererar kod via `KameoAuthenticator`, skickar kod).
        *   `get_account_number`: **Hämtar kontonummer via Kameos JSON-API (`/ezjscore/call/kameo_transfer::init`).** Om API-anropet misslyckas används HTML-parsning av dashboard som fallback. Detta är robustare mot ändringar i sidlayouten och följer det faktiska flödet enligt HAR-filerna.
*   **Användning:** Ett `KameoClient`-objekt skapas i `main`-funktionen. Metoderna `login`, `handle_2fa` (om nödvändigt) och `get_account_number` anropas i sekvens för att slutföra uppgiften.

## `get_it_done.py` - `main` och `load_configuration`

*   **`load_configuration`:** Funktion som ansvarar för att skapa `KameoConfig`-objektet och hantera eventuella valideringsfel vid uppstart.
*   **`main`:** Huvudfunktionen som:
    *   Anropar `load_configuration`.
    *   Skapar `KameoClient`.
    *   Anropar klientens metoder i rätt ordning.
    *   Skriver ut det slutliga resultatet (kontonummer eller felmeddelande).
    *   Initierar och styr den övergripande loggningen. 