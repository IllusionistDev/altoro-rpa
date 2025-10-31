"""API retry handler with exponential backoff and intelligent error recovery.

This module provides a decorator for automatic retry logic with exponential backoff,
similar to the web layer's session retry mechanism but specialized for API calls.
"""

import time
import random
from functools import wraps
from typing import Callable, Any
import httpx

from src.api.exceptions import (
    APIError,
    APIAuthenticationError,
    APIConnectionError,
    MaxRetriesExceededError,
)
from src.core.logger import log


# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {
    500,  # Internal Server Error
}

# HTTP status codes that are explicitly handled (no retry)
HANDLED_STATUS_CODES = {
    400,  # Bad Request
    401,  # Unauthorized
    501,  # Not Implemented
}


def with_api_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 32.0,
    jitter: bool = True,
):
    """
    Decorator to automatically retry API requests with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        max_backoff: Maximum backoff time in seconds (default: 32.0)
        jitter: Add random jitter to prevent thundering herd (default: True)

    Returns:
        Decorated function with automatic retry logic

    Usage:
        @with_api_retry(max_retries=3, backoff_factor=2.0)
        def get_accounts(self):
            # This method will auto-retry on transient failures
            ...

    Retry Behavior:
        - Retries on: 500 (Internal Server Error), network errors, timeouts
        - Does NOT retry on: 400, 401, 501, and all other HTTP status codes
        - Uses exponential backoff: wait = backoff_factor ^ attempt
        - Adds jitter to prevent synchronized retries
        - Logs each retry attempt with context

    Status Code Handling:
        - 200: Success (no exception)
        - 400: Bad Request → APIError (no retry)
        - 401: Unauthorized → APIAuthenticationError (no retry)
        - 500: Internal Server Error → Retry with backoff
        - 501: Not Implemented → APIError (no retry)
        - All others: Generic APIError (no retry)

    Exception Handling:
        - Raises MaxRetriesExceededError after exhausting all retries
        - Preserves original exception context for debugging
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            attempt = 0

            while attempt <= max_retries:
                try:
                    # Execute the wrapped method
                    result = func(*args, **kwargs)

                    # Success! Log if this was a retry
                    if attempt > 0:
                        log.info(f"{func.__name__} succeeded after {attempt} retries")

                    return result

                except httpx.HTTPStatusError as e:
                    last_exception = e
                    attempt += 1
                    status_code = e.response.status_code

                    # Handle specific status codes
                    if status_code == 401:
                        # Authentication error - don't retry, raise immediately
                        raise APIAuthenticationError(
                            f"Authentication failed (401): {e}",
                            status_code=status_code,
                            response_body=e.response.text[:500],
                        ) from e

                    elif status_code == 400:
                        # Bad Request - don't retry
                        raise APIError(
                            f"Bad Request (400): {e}",
                            status_code=status_code,
                            response_body=e.response.text[:500],
                        ) from e

                    elif status_code == 501:
                        # Not Implemented - don't retry
                        raise APIError(
                            f"Not Implemented (501): {e}",
                            status_code=status_code,
                            response_body=e.response.text[:500],
                        ) from e

                    elif status_code == 500:
                        # Internal Server Error - retry with backoff
                        if attempt > max_retries:
                            raise MaxRetriesExceededError(
                                f"Server error (500) persisted after {max_retries} retries",
                                attempts=attempt,
                                last_error=e,
                                status_code=status_code,
                            ) from e

                        wait_time = _calculate_backoff(
                            attempt, backoff_factor, max_backoff, jitter
                        )
                        log.warning(
                            f"Server error (500) in {func.__name__} (attempt {attempt}/{max_retries}). "
                            f"Retrying in {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        continue

                    else:
                        # All other status codes - generic error, don't retry
                        raise APIError(
                            f"HTTP error {status_code}: {e}",
                            status_code=status_code,
                            response_body=e.response.text[:500],
                        ) from e

                except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                    # Connection error - retry with backoff
                    last_exception = e
                    attempt += 1

                    if attempt > max_retries:
                        raise MaxRetriesExceededError(
                            f"Connection failed after {max_retries} retries: {e}",
                            attempts=attempt,
                            last_error=e,
                        ) from e

                    wait_time = _calculate_backoff(
                        attempt, backoff_factor, max_backoff, jitter
                    )
                    log.warning(
                        f"Connection error in {func.__name__} (attempt {attempt}/{max_retries}). "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    time.sleep(wait_time)
                    continue

                except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
                    # Timeout error - retry with backoff
                    last_exception = e
                    attempt += 1

                    if attempt > max_retries:
                        raise MaxRetriesExceededError(
                            f"Request timeout after {max_retries} retries: {e}",
                            attempts=attempt,
                            last_error=e,
                        ) from e

                    wait_time = _calculate_backoff(
                        attempt, backoff_factor, max_backoff, jitter
                    )
                    log.warning(
                        f"Timeout in {func.__name__} (attempt {attempt}/{max_retries}). "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    time.sleep(wait_time)
                    continue

                except httpx.RequestError as e:
                    # Generic request error - retry with backoff
                    last_exception = e
                    attempt += 1

                    if attempt > max_retries:
                        raise APIConnectionError(
                            f"Request failed after {max_retries} retries: {e}",
                            attempts=attempt,
                            last_error=e,
                        ) from e

                    wait_time = _calculate_backoff(
                        attempt, backoff_factor, max_backoff, jitter
                    )
                    log.warning(
                        f"Request error in {func.__name__} (attempt {attempt}/{max_retries}). "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    time.sleep(wait_time)
                    continue

                except Exception as e:
                    # Unknown error - don't retry, log and raise
                    log.error(
                        f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}"
                    )
                    raise

            # Should never reach here, but just in case
            raise MaxRetriesExceededError(
                f"Exhausted all {max_retries} retries for {func.__name__}",
                attempts=attempt,
                last_error=last_exception,
            ) from last_exception

        return wrapper

    return decorator


def _calculate_backoff(
    attempt: int, backoff_factor: float, max_backoff: float, jitter: bool
) -> float:
    """
    Calculate exponential backoff time with optional jitter.

    Args:
        attempt: Current attempt number (1-indexed)
        backoff_factor: Exponential backoff multiplier
        max_backoff: Maximum backoff time in seconds
        jitter: Whether to add random jitter

    Returns:
        Backoff time in seconds
    """
    # Exponential backoff: backoff_factor ^ (attempt - 1)
    backoff = min(backoff_factor ** (attempt - 1), max_backoff)

    # Add jitter (random value between 0 and backoff * 0.1)
    if jitter:
        jitter_amount = random.uniform(0, backoff * 0.1)
        backoff += jitter_amount

    return backoff
