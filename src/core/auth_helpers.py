"""Authentication and session management helper utilities.

This module provides reusable authentication workflows to eliminate duplicated
login sequences and session context setup across orchestration files.
"""

from playwright.sync_api import Page

from src.web.pages.login_page import LoginPage
from src.web.pages.base_page import BasePage
from src.core.config import settings
from src.core.logger import log


def authenticate_user(page: Page, screenshot_dir: str) -> LoginPage:
    """
    Perform standard authentication workflow.

    This function encapsulates the complete login sequence:
    1. Navigate to login page
    2. Submit credentials
    3. Verify successful login

    Args:
        page: Playwright Page instance
        screenshot_dir: Directory for error screenshots

    Returns:
        Authenticated LoginPage instance for session recovery

    Example:
        >>> with browser_session(settings.trace_dir) as browser_context:
        ...     page = browser_context.new_page()
        ...     login_page = authenticate_user(page, settings.screenshot_dir)
    """
    login_page = LoginPage(page, screenshot_dir)
    login_page.goto(settings.base_url)
    login_page.login(settings.user, settings.password)
    login_page.assert_logged_in()
    log.info("Login successful")
    return login_page


def setup_session_context(page_instance: BasePage, login_page: LoginPage) -> None:
    """
    Configure session recovery context for a page instance.

    Sets up the page instance with credentials and login page reference
    to enable automatic session recovery via the @with_session_retry decorator.

    Args:
        page_instance: Page object to configure (e.g., AccountsPage, TransactionsPage)
        login_page: LoginPage instance for re-authentication

    Example:
        >>> accounts_page = AccountsPage(page)
        >>> setup_session_context(accounts_page, login_page)
        >>> # Now accounts_page methods with @with_session_retry will auto-recover
    """
    page_instance.set_session_context(
        login_page=login_page,
        credentials={
            "username": settings.user,
            "password": settings.password,
            "base_url": settings.base_url,
        },
    )


def authenticate_and_setup(
    page: Page, screenshot_dir: str, page_instance: BasePage
) -> LoginPage:
    """
    Convenience function to authenticate and setup session context in one call.

    Combines authenticate_user() and setup_session_context() for the common
    workflow of logging in and configuring a page for session recovery.

    Args:
        page: Playwright Page instance
        screenshot_dir: Directory for error screenshots
        page_instance: Page object to configure for session recovery

    Returns:
        Authenticated LoginPage instance

    Example:
        >>> accounts_page = AccountsPage(page)
        >>> login_page = authenticate_and_setup(
        ...     page,
        ...     settings.screenshot_dir,
        ...     accounts_page
        ... )
        >>> accounts_page.open()  # Ready to use with automatic session recovery
    """
    login_page = authenticate_user(page, screenshot_dir)
    setup_session_context(page_instance, login_page)
    return login_page
