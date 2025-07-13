# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Separated configuration into `config.py` using Pydantic.
- Separated authentication logic into `auth.py` using `pyotp`.
- Added `README.md` for project documentation.
- Added `.gitignore` file.
- Added `changelog.md` for tracking changes.
- Added `requirements.txt` to list dependencies.

### Changed
- Restructured project from a single script to multiple modules.
- Renamed `kameo_fetcher.py` to `kameo_client.py` and the class `KameoFetcher` to `KameoClient`.
- Updated imports in `test_kameo.py` to match the new file name.
- Fixed linting errors using `ruff`.
- Corrected mock response in `test_login_flow` to ensure test passes.
- Revised and translated `README.md` to Swedish for clarity and completeness. 

### Förbättringar
- Kontonummer hämtas nu primärt via Kameos JSON-API (`/ezjscore/call/kameo_transfer::init`) istället för att parsa HTML från dashboarden. Detta är robustare mot ändringar i sidlayouten och följer det faktiska flödet enligt HAR-filerna.
- Om API-anropet misslyckas används HTML-parsning som fallback (legacy-metod). 