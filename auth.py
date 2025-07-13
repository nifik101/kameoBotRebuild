"""Compatibility shim to allow `import auth` in legacy code and tests.

This module simply re-exports :class:`KameoAuthenticator` from ``src.auth`` so
that it can be imported as ``auth.KameoAuthenticator`` without requiring the
full ``src`` prefix.
"""

from src.auth import KameoAuthenticator  # noqa: F401  (re-export)

__all__ = ["KameoAuthenticator"] 