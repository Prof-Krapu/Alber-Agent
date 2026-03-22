"""
Rate Limiter simple et robuste pour Albert IA Agentic.
Utilise une implémentation Token Bucket en mémoire.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from functools import wraps


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 30
    burst_size: int = 5


class TokenBucket:
    """
    Implémentation Token Bucket pour rate limiting.
    Thread-safe et performante.
    """

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens par seconde
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Tente de consommer des tokens.
        Returns: (accepted, retry_after_seconds)
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Régénération des tokens
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0

            # Temps avant disponibilité
            retry_after = (tokens - self.tokens) / self.rate
            return False, max(0, retry_after)


class RateLimiter:
    """
    Rate Limiter centralisé par IP.
    """

    def __init__(self, requests_per_minute: int = 30, burst_size: int = 5):
        self.rate = requests_per_minute / 60.0  # Convertir en tokens/sec
        self.burst = burst_size
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.rate, self.burst)
        )
        self.lock = threading.Lock()
        self.client_ips: Dict[str, float] = {}

    def _get_client_ip(self, request=None) -> str:
        """Extrait l'IP du client (support proxy via X-Forwarded-For)."""
        if request:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            return request.client.host if request.client else "127.0.0.1"
        return "unknown"

    def check(
        self, identifier: Optional[str] = None, request=None
    ) -> Tuple[bool, Optional[float]]:
        """
        Vérifie si une requête est autorisée.
        Returns: (allowed, retry_after)
        """
        ip = identifier or self._get_client_ip(request)

        with self.lock:
            if ip not in self.buckets:
                self.buckets[ip] = TokenBucket(self.rate, self.burst)

        allowed, retry_after = self.buckets[ip].consume()
        return allowed, retry_after if not allowed else None

    def cleanup_inactive(self, max_age_seconds: int = 3600):
        """Nettoie les entrées inactives pour éviter memory leak."""
        now = time.time()
        with self.lock:
            expired = [
                ip
                for ip, last in self.client_ips.items()
                if now - last > max_age_seconds
            ]
            for ip in expired:
                del self.buckets[ip]
                del self.client_ips[ip]


# Instance globale
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        from config import config

        _rate_limiter = RateLimiter(
            requests_per_minute=config.RATE_LIMIT_REQUESTS,
            burst_size=config.RATE_LIMIT_REQUESTS // 6,
        )
    return _rate_limiter


def rate_limit(requests_per_minute: Optional[int] = None):
    """
    Decorator pour rate limiting des endpoints Flask.

    Usage:
        @app.route('/api/chat', methods=['POST'])
        @require_auth
        @rate_limit(requests_per_minute=30)
        def chat():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            allowed, retry_after = limiter.check()

            if not allowed:
                # FastAPI/ASGI style response expected by callers. Return a tuple to let
                # frameworks construct a proper response.
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": "Rate limit exceeded",
                        "retry_after": int(retry_after) if retry_after else 60,
                    },
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_client_ip(request=None) -> str:
    """Helper pour obtenir l'IP du client."""
    return get_rate_limiter()._get_client_ip(request)
