"""Part 1: Login automation orchestration for Altoro Mutual."""

from src.web.browser import browser_session
from src.web.pages.login_page import LoginPage
from src.core.config import settings
from src.core.logger import log


def run_part1_login() -> None:
    """
    Execute Part 1: Login testing with happy path and negative login scenarios.

    Performs two login tests:
    1. Happy path: Login with correct credentials (with retries)
    2. Negative test: Login with incorrect password to capture error state

    Retry logic:
    - Attempts login up to max_login_retries times
    - Captures screenshot on each failure
    - Raises exception if all retries fail

    Raises:
        Exception: If login fails after all retry attempts

    Note:
        Uses configuration from settings (base_url, user, password, etc.)
        Saves error screenshots to settings.screenshot_dir
        Saves browser trace to settings.trace_dir
    """
    with browser_session(settings.trace_dir) as browser_context:
        page = browser_context.new_page()
        login_page = LoginPage(page, settings.screenshot_dir)
        login_page.goto(settings.base_url)

        # Happy path with retry
        for attempt in range(1, settings.max_login_retries + 1):
            try:
                login_page.login(settings.user, settings.password)
                login_page.assert_logged_in()
                log.info(f"Login successful (attempt {attempt})")
                break
            except Exception:
                screenshot_path = login_page.error_screenshot(
                    f"login_attempt_{attempt}"
                )
                log.exception(
                    f"Login attempt {attempt} failed. Screenshot: {screenshot_path}"
                )
                if attempt == settings.max_login_retries:
                    raise

        # Negative login
        page.goto(f"{settings.base_url}/login.jsp")
        login_page.login(settings.user, "wrong_password")
        screenshot_path = login_page.error_screenshot("negative_login")
        log.info(f"Captured negative login state: {screenshot_path}")
