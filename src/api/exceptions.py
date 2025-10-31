"""Custom exception hierarchy for API client error handling.

This module provides specific exception types for different API error conditions,
enabling precise error handling and recovery strategies.
"""


class APIError(Exception):
    """Base exception for all API-related errors."""

    def __init__(
        self, message: str, status_code: int = None, response_body: str = None
    ):
        """
        Initialize API error with context.

        Args:
            message: Human-readable error message
            status_code: HTTP status code if available
            response_body: Response body content if available
        """
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"{self.message} (HTTP {self.status_code})"
        return self.message


class APIAuthenticationError(APIError):
    """
    Raised when authentication fails (401 Unauthorized, 403 Forbidden).

    This error indicates invalid credentials, expired tokens, or insufficient permissions.
    Automatic retry with re-authentication may be appropriate.
    """

    pass


class APIRateLimitError(APIError):
    """
    Raised when API rate limit is exceeded (429 Too Many Requests).

    This error indicates too many requests in a given time period.
    Should be handled with exponential backoff and retry.
    """

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying (from Retry-After header)
            **kwargs: Additional arguments passed to APIError
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class APIServerError(APIError):
    """
    Raised when server returns 5xx errors (500, 502, 503, 504).

    This error indicates temporary server-side issues.
    Should be handled with retry logic and exponential backoff.
    """

    pass


class APITimeoutError(APIError):
    """
    Raised when API request times out.

    This error indicates network issues or slow server response.
    Should be handled with retry logic.
    """

    pass


class APIConnectionError(APIError):
    """
    Raised when connection to API server fails.

    This error indicates network connectivity issues, DNS failures,
    or service unavailability. Should be handled with retry logic.
    """

    pass


class MaxRetriesExceededError(APIError):
    """
    Raised when maximum retry attempts have been exhausted.

    This error indicates that retries have been attempted but failed consistently.
    No further automatic retry should be attempted.
    """

    def __init__(
        self, message: str, attempts: int, last_error: Exception = None, **kwargs
    ):
        """
        Initialize max retries exceeded error.

        Args:
            message: Error message
            attempts: Number of retry attempts made
            last_error: The last exception that occurred
            **kwargs: Additional arguments passed to APIError
        """
        super().__init__(message, **kwargs)
        self.attempts = attempts
        self.last_error = last_error
