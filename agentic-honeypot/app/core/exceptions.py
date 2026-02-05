"""Custom exceptions for the honeypot system."""


class HoneypotException(Exception):
    """Base exception for honeypot system."""
    pass


class AuthenticationException(HoneypotException):
    """Raised when API key is invalid or missing."""
    pass


class InvalidPayloadException(HoneypotException):
    """Raised when request payload is invalid."""
    pass


class SessionException(HoneypotException):
    """Raised when session-related errors occur."""
    pass


class CallbackException(HoneypotException):
    """Raised when callback to GUVI endpoint fails."""
    pass