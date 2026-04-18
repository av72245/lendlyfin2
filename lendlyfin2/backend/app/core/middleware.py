"""
Middleware:
- RateLimitMiddleware  — limits requests per IP to prevent abuse
- SecurityHeadersMiddleware — adds security headers to all responses
- RequestLoggingMiddleware  — logs requests in production
"""
import time
import logging
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    Limits each IP to max_requests per window_seconds.
    
    Public endpoints (lead submission, rates): 30 req/min
    Auth endpoints (login): 10 req/min — prevents brute force
    
    For production with multiple workers, replace with Redis-backed limiter.
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests   = max_requests
        self.window_seconds = window_seconds
        self._counts: dict  = defaultdict(list)  # ip → [timestamps]

    def _get_ip(self, request: Request) -> str:
        # Respect X-Forwarded-For from Railway/Netlify proxies
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip  = self._get_ip(request)
        now = time.time()

        # Stricter limit on login endpoint to prevent brute force
        limit = 10 if "/api/auth/login" in request.url.path else self.max_requests

        # Clean old timestamps
        self._counts[ip] = [t for t in self._counts[ip] if now - t < self.window_seconds]

        if len(self._counts[ip]) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please wait a moment and try again.",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._counts[ip].append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]          = "DENY"
        response.headers["X-XSS-Protection"]         = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "camera=(), microphone=(), geolocation=()"
        # Only add HSTS in production — breaks local dev with HTTP
        if request.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)

        # Skip logging for health checks to avoid noise
        if request.url.path != "/api/health":
            logger.info(
                f"{request.method} {request.url.path} "
                f"→ {response.status_code} ({duration}ms)"
            )
        return response
