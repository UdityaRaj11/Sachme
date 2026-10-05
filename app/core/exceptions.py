"""Custom application exceptions for the TruthFirewall backend."""

class TruthFirewallException(Exception):
    """Base exception for all TruthFirewall errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedContentError(TruthFirewallException):
    """Raised when a URL or content format cannot be reliably processed.
    Ensures the system fails gracefully rather than hallucinating."""
    def __init__(self, message: str, platform: str = None, url: str = None):
        super().__init__(
            message=message,
            details={"platform": platform, "url": url}
        )


class InvalidUrlError(TruthFirewallException):
    """Raised when an invalid, dangerous (SSRF), or malformed URL is supplied."""
    def __init__(self, message: str, url: str = None):
        super().__init__(message=message, details={"url": url})


class ContentExtractionError(TruthFirewallException):
    """Raised when extraction from a valid source fails (network, paywall, deleted)."""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message=message, details={"url": url, "status_code": status_code})


class EvidenceRetrievalError(TruthFirewallException):
    """Raised when evidence searching or indexing fails."""
    def __init__(self, message: str, query: str = None):
        super().__init__(message=message, details={"query": query})


class VerificationEngineError(TruthFirewallException):
    """Raised when model inference or claim verification logic encounters an unrecoverable state."""
    pass


class JobNotFoundError(TruthFirewallException):
    """Raised when a background verification job ID is not found."""
    def __init__(self, job_id: str):
        super().__init__(f"Job with ID '{job_id}' not found.", details={"job_id": job_id})


class RateLimitExceededError(TruthFirewallException):
    """Raised when client exceeds rate limits."""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message=message)
