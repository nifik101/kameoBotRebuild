# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Renamed `kameo_fetcher.py` to `kameo_client.py` and the class `KameoFetcher` to `KameoClient`.
- Updated imports in `test_kameo.py` to match the new file name.
- Fixed linting errors using `ruff`.
- Corrected mock response in `test_login_flow` to ensure test passes.
- Revised and translated `README.md` to Swedish for clarity and completeness. 