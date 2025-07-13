# Kameo Bot - Hämta Kontonummer

Detta Python-skript loggar in på Kameos webbplats, hanterar tvåfaktorsautentisering (2FA/TOTP) om det är konfigurerat, och hämtar användarens kontonummer från Kameos API (eller dashboard-sidan som fallback).

## Funktioner

*   Loggar in på Kameo med e-post och lösenord.
*   Hanterar 2FA med TOTP (Google Authenticator, Authy, etc.) om en hemlighet anges.
*   Hämtar och skriver ut användarens kontonummer.
*   **Hämtar kontonummer via Kameos JSON-API** (`/ezjscore/call/kameo_transfer::init`) för robusthet mot sidändringar.
*   Om API-anropet misslyckas används HTML-parsning av dashboard som fallback.
*   Använder `requests` för HTTP-anrop och `BeautifulSoup` för HTML-parsning.
*   Läser konfiguration från miljövariabler eller en `.env`-fil via `pydantic-settings`.
*   Detaljerad loggning av processen.

## Installation

1.  **Klona repot (om du inte redan gjort det):**
    ```bash
    git clone <repo-url>
    cd <repo-mapp>
    ```

2.  **Skapa en virtuell miljö (rekommenderas):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # eller
    # .venv\Scripts\activate  # Windows
    ```

3.  **Installera beroenden:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Om `requirements.txt` inte finns, behöver den skapas. Kör `pip freeze > requirements.txt` efter att ha installerat paketen nedan manuellt)*
    *   `requests`
    *   `beautifulsoup4`
    *   `pydantic`
    *   `pydantic-settings`
    *   `python-dotenv`
    *   `pyotp`

## Konfiguration

Skriptet konfigureras via miljövariabler eller en `.env`-fil i samma mapp som `kameo_fetcher.py`.

Skapa en fil med namnet `.env` och lägg till följande variabler:

```dotenv
# Obligatoriska
KAMEO_EMAIL="din.epost@example.com"
KAMEO_PASSWORD="ditt_kameo_losenord"

# Obligatorisk om du använder 2FA/TOTP hos Kameo
KAMEO_TOTP_SECRET="DIN_BASE32_KODADE_TOTP_HEMLIGHET"

# Valfria (har standardvärden)
# KAMEO_BASE_URL="https://www.kameo.se"
# KAMEO_CONNECT_TIMEOUT=5.0
# KAMEO_READ_TIMEOUT=10.0
# KAMEO_MAX_REDIRECTS=5
# KAMEO_USER_AGENT="KameoBot/1.0 (Python Requests)"
```

**Viktigt:**

*   Ersätt platshållarna med dina faktiska uppgifter.
*   `KAMEO_TOTP_SECRET` är den Base32-kodade hemlighet du får när du konfigurerar 2FA i din authenticator-app. Den ser ofta ut som en serie versaler och siffrorna 2-7.
*   Om du inte använder 2FA hos Kameo kan du utelämna `KAMEO_TOTP_SECRET` eller lämna värdet tomt.

## Användning

När du har installerat beroenden och skapat `.env`-filen, kör skriptet från terminalen:

```bash
python kameo_fetcher.py
```

Skriptet kommer att logga sina steg i terminalen och avsluta med att skriva ut kontonumret om det lyckas, eller ett felmeddelande om något går fel.

## Kodstruktur

*   `kameo_fetcher.py`: Huvudskriptet som innehåller `KameoClient`-klassen och `main`-funktionen.
*   `config.py`: Definierar `KameoConfig`-klassen för att hantera konfiguration via `pydantic-settings`.
*   `auth.py`: Definierar `KameoAuthenticator`-klassen för att hantera TOTP-generering.
*   `.env`: Fil för att lagra känsliga konfigurationsuppgifter (bör inte versionshanteras om repot är publikt).
*   `requirements.txt`: Lista över Python-beroenden.

## Felsökning

*   **Valideringsfel vid start:** Kontrollera att `KAMEO_EMAIL` och `KAMEO_PASSWORD` är satta i `.env`-filen eller som miljövariabler.
*   **Inloggning misslyckas:** Kontrollera att e-post och lösenord är korrekta.
*   **2FA misslyckas:**
    *   Kontrollera att `KAMEO_TOTP_SECRET` är korrekt angiven i Base32-format.
    *   Säkerställ att klockan på datorn där skriptet körs är synkroniserad (NTP).
*   **Kontonummer hittas ej:**
    *   Kontrollera loggarna. Om API-anropet mot `/ezjscore/call/kameo_transfer::init` misslyckas, försöker skriptet parsa HTML från dashboarden som fallback.
    *   Om både API och HTML-parsning misslyckas, kan webbplatsens struktur ha ändrats. Undersök loggarna (`logging.debug`-nivå kan ge mer info om HTML) och eventuellt spara HTML-sidorna som är utkommenterade i koden för manuell analys. Uppdatera CSS-selektorerna i `get_account_number`-metoden vid behov.

## Notis om kontonummer-hämtning

> **Från och med [Unreleased]:** Kontonummer hämtas nu primärt via Kameos JSON-API (`/ezjscore/call/kameo_transfer::init`). Detta är robustare mot ändringar i sidlayouten. Om API-anropet misslyckas används HTML-parsning av dashboard som fallback.

# TODO & PRD: Selenium → FastAPI-migrering

## Produktkrav (PRD)

**Syfte:**
Migrera affärslogik och API-flöden från Selenium-baserad browser automation till en modern FastAPI-backend, med automatiserad modell- och endpointgenerering, robust testning och CI/CD.

**Mål:**
- Fånga och analysera all HTTP-trafik från Selenium-flöden
- Generera Pydantic-modeller och FastAPI-endpoints automatiskt
- Flytta affärslogik till backend
- Säkerställa testtäckning och CI/CD

---

## TODO-lista (migreringsplan)

### 1. Förberedelse & Miljö
- [ ] Säkerställ att alla beroenden finns i `pyproject.toml` (uv, selenium-wire, fastapi, pydantic, httpx, pytest, ruff)
- [ ] Skapa feature branch: `feature/migrate-api-capture`

### 2. HTTP-trafikinsamling från Selenium
- [ ] Modifiera Selenium-setup (Selenium Wire) för att logga HTTP-trafik
- [ ] Skapa script: `scripts/capture_har.py` som kör Selenium-flöde och sparar HAR/JSON
- [ ] Spara output i `logs/har/`

### 3. Analys & Modellgenerering
- [ ] Skapa script: `scripts/generate_models.py` som läser HAR/JSON och genererar Pydantic-modeller samt förslag på FastAPI-endpoints
- [ ] Spara modeller i `src/models/auto_generated.py` och endpoints i `src/api/auto_generated.py`

### 4. FastAPI-backend & Refaktorering
- [ ] Skapa/uppdatera FastAPI-appstruktur enligt repo-regler
- [ ] Implementera endpoints med genererade modeller
- [ ] Flytta affärslogik från Selenium-skript till FastAPI-tjänster
- [ ] Implementera autentisering/session (JWT/cookies) om det behövs

### 5. Testning
- [ ] Skriv pytest-tester med httpx.AsyncClient för varje endpoint
- [ ] Säkerställ testtäckning för alla flöden

### 6. Kvalitet & Dokumentation
- [ ] Lintning med Ruff, typkontroll med Pydantic
- [ ] Uppdatera README och auto-generera OpenAPI/Swagger
- [ ] Dokumentera capture-script, modellgenerering och API-start

### 7. CI/CD & Deployment
- [ ] Uppdatera Docker/uv/compose-manifest för nya endpoints
- [ ] Lägg till pipeline-steg för automatiska API-tester
- [ ] Säkerställ att HAR-filer/loggar sparas för felsökning

---

**Ansvar:**
- Backend/API: AI-assistent + utvecklingsteam
- Test & QA: Utvecklingsteam
- DevOps/CI: DevOps-ansvarig

--- 