import time
from collections import defaultdict
from app.core.exceptions import RateLimitExceededError

class SlidingWindowRateLimiter:
    """In-memory sliding-window rate limiter per client IP / key."""
    
    def __init__(self, limit_per_minute: int = 60):
        self.limit = limit_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        
        # Clean timestamps older than 60 seconds
        self.requests[client_key] = [
            ts for ts in self.requests[client_key] if ts > window_start
        ]
        
        if len(self.requests[client_key]) >= self.limit:
            return False
            
        self.requests[client_key].append(now)
        return True

    def check(self, client_key: str):
        if not self.is_allowed(client_key):
            raise RateLimitExceededError(
                f"Rate limit exceeded: {self.limit} requests per minute maximum."
            )

rate_limiter = SlidingWindowRateLimiter()
