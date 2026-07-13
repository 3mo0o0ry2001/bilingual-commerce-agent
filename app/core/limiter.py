"""
limiter.py

Shared rate limiter instance, imported by main.py and any router
that needs rate limiting. Kept separate to avoid circular imports.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)