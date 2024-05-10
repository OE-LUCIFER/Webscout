class WebscoutE(Exception):
    """Base exception class for duckduckgo_search."""


class RatelimitE(Exception):
    """Raised for rate limit exceeded errors during API requests."""


class TimeoutE(Exception):
    """Raised for timeout errors during API requests."""
    
class FailedToGenerateResponseError(Exception):
    
    """Provider failed to fetch response"""
class AllProvidersFailure(Exception):
    """None of the providers generated response successfully"""

    pass