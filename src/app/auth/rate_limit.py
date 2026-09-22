import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# IP -> list of timestamps (in seconds) of recent attempts
_attempts: dict[str, list[float]] = defaultdict(list)

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


def check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Drop timestamps older than the window
    _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW_SECONDS]

    if len(_attempts[ip]) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
        )

    _attempts[ip].append(now)