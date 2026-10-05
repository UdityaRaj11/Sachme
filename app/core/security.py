import ipaddress
import socket
from urllib.parse import urlparse
from app.core.exceptions import InvalidUrlError

DISALLOWED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254", # AWS/GCP metadata service
}

def is_safe_url(url: str) -> bool:
    """
    Validates a URL to prevent SSRF (Server-Side Request Forgery) attacks.
    Ensures URL scheme is http/https and host does not resolve to private/loopback/link-local IP addresses.
    """
    if not url or len(url) > 2048:
        return False
        
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme.lower() not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    hostname_lower = hostname.lower()
    if hostname_lower in DISALLOWED_HOSTS:
        return False

    # Check if host is direct IP address
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            return False
    except ValueError:
        # Not a direct IP address; resolve DNS
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                resolved_ip = ipaddress.ip_address(ip_str)
                if (
                    resolved_ip.is_private
                    or resolved_ip.is_loopback
                    or resolved_ip.is_link_local
                    or resolved_ip.is_multicast
                    or resolved_ip.is_reserved
                ):
                    return False
        except (socket.gaierror, socket.herror, Exception):
            # If DNS cannot be resolved, allow extractor to handle connection failure cleanly
            pass

    return True


def validate_and_sanitize_url(url: str) -> str:
    """Validates URL and returns cleaned string, or raises InvalidUrlError."""
    cleaned = url.strip()
    if not is_safe_url(cleaned):
        raise InvalidUrlError(
            f"The provided URL '{url}' is invalid or references an unsafe/disallowed destination.",
            url=url,
        )
    return cleaned
