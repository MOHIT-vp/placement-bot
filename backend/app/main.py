"""
Main FastAPI application — Labs 1–12.

Security hardening (Lab 12):
- Security headers middleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Simple in-process per-IP rate limiter (sliding window)
- Strict CORS configuration from settings
"""
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import api_router
from app.config import settings


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add defensive HTTP security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers.pop("server", None)
            return response
        except Exception as e:
            import logging
            logging.error(f"Middleware Error: {e}", exc_info=True)
            raise


# ---------------------------------------------------------------------------
# Simple In-Process Rate Limiter (sliding window per IP)
# ---------------------------------------------------------------------------

_rate_limit_store: dict = defaultdict(deque)

RATE_LIMIT_REQUESTS = 60    # requests
RATE_LIMIT_WINDOW   = 60    # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter: 60 requests / 60 seconds per IP.
    Excluded: /docs, /redoc, /openapi.json, health check.
    """

    EXCLUDED_PATHS = {"/docs", "/redoc", "/openapi.json", "/api/v1/admin/system/health"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW

        queue = _rate_limit_store[client_ip]
        # Drop timestamps outside the window
        while queue and queue[0] < window_start:
            queue.popleft()

        if len(queue) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again in 60 seconds."},
                headers={"Retry-After": "60"},
            )

        queue.append(now)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for the Placement Readiness & Career Intelligence Portal",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middlewares disabled for debugging exception bubbling
# app.add_middleware(RateLimitMiddleware)
# app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

# 4. Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/admin/system/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
