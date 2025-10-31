"""Session timeout/logout handler with automatic retry."""

import time
from functools import wraps
from typing import Callable, Any
from src.core.logger import log
from src.core.constants import DEFAULT_MAX_RETRIES, SESSION_ERROR_KEYWORDS


class SessionExpiredError(Exception):
    """Raised when a session has expired and cannot be recovered."""

    pass


def with_session_retry(max_retries: int = DEFAULT_MAX_RETRIES):
    """
    Decorator to automatically handle session timeouts and re-authenticate.

    Args:
        max_retries: Maximum number of retry attempts on session failure

    Usage:
        @with_session_retry(max_retries=2)
        def get_account_summary(self):
            # This method will auto-retry with re-auth if session expires
            ...

    The decorated method's class must have:
        - self.page: Playwright Page object
        - self.login_page: LoginPage instance with is_logged_out() and login() methods
        - self.credentials: dict with 'username' and 'password' keys
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    # Execute the wrapped method
                    result = func(self, *args, **kwargs)
                    return result

                except Exception as e:
                    last_exception = e
                    error_message = str(e).lower()

                    # Check if this looks like a session/page error
                    is_session_error = any(
                        phrase in error_message for phrase in SESSION_ERROR_KEYWORDS
                    )

                    if not is_session_error:
                        # Not a session error, re-raise immediately
                        log.debug(f"Non-session error in {func.__name__}: {e}")
                        raise

                    # Check if actually logged out
                    if hasattr(self, "login_page"):
                        try:
                            if self.login_page.is_logged_out():
                                log.warning(
                                    f"Session expired during {func.__name__} (attempt {attempt}/{max_retries}). "
                                    f"Re-authenticating..."
                                )

                                # Re-authenticate
                                if hasattr(self, "credentials"):
                                    self.login_page.goto(self.credentials["base_url"])
                                    self.login_page.login(
                                        self.credentials["username"],
                                        self.credentials["password"],
                                    )
                                    self.login_page.assert_logged_in()
                                    log.info(
                                        f"Re-authentication successful. Retrying {func.__name__}..."
                                    )

                                    # Exponential backoff before retry
                                    time.sleep(min(2**attempt, 8))
                                    continue
                                else:
                                    raise SessionExpiredError(
                                        f"Session expired but no credentials available for re-auth in {func.__name__}"
                                    )
                        except Exception as auth_error:
                            log.error(f"Re-authentication failed: {auth_error}")
                            if attempt == max_retries:
                                raise SessionExpiredError(
                                    f"Failed to recover session after {max_retries} attempts in {func.__name__}"
                                ) from last_exception

                    # If we couldn't determine logout status or re-auth failed, retry if attempts remain
                    if attempt < max_retries:
                        log.warning(
                            f"Retrying {func.__name__} due to error: {e} (attempt {attempt}/{max_retries})"
                        )
                        time.sleep(min(2**attempt, 8))
                        continue
                    else:
                        # Out of retries
                        raise

            # Should never reach here, but just in case
            raise (
                last_exception
                if last_exception
                else SessionExpiredError(
                    f"Unknown error in {func.__name__} after {max_retries} retries"
                )
            )

        return wrapper

    return decorator
