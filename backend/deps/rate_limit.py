"""
deps/rate_limit.py — Shared SlowAPI limiter instance.

Import `limiter` in main.py to attach it to the FastAPI app, and import
`limiter` in any router that needs rate limiting.

Storage: in-memory (MemoryStorage) — correct for single-server deployments.
For multi-instance deployments swap to RedisStorage.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter keyed on the client's IP address.
limiter = Limiter(key_func=get_remote_address)
