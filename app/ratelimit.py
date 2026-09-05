"""Shared rate limiter (slowapi). Keyed by client IP by default.

Login is throttled hard to blunt credential-stuffing/brute force; everything
else gets a sane global default. Swap the storage_uri to Redis for multi-instance
deployments.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
