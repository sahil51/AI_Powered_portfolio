import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # In-memory rate limiter: per-process only.
        # Does not synchronize across multiple workers.
        # Replace with Redis-backed limiter for horizontal scaling.
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60

        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < window]

        if len(self.requests[client_ip]) >= settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
