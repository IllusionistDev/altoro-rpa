"""Login page automation for Altoro Mutual demo site."""

from playwright.sync_api import Page, expect
from pathlib import Path
from datetime import datetime


class LoginPage:
    """
    Handles login operations and session validation.

    Provides methods for:
    - Navigation to login page
    - User authentication
    - Session state validation
    - Error message capture
    - Screenshot capture

    Attributes:
        page: Playwright Page object for browser automation
        screenshot_dir: Directory path for saving error screenshots
    """

    # Timeout constants
    LOGIN_WAIT_TIMEOUT = 5000  # Wait for login completion
    ASSERT_LOGIN_TIMEOUT = 7000  # Wait for assertion verification
    SESSION_CHECK_TIMEOUT = 2000  # Quick session state check
    FORM_CHECK_TIMEOUT = 1000  # Quick login form visibility check

    def __init__(self, page: Page, screenshot_dir: str) -> None:
        """
        Initialize LoginPage with Playwright page and screenshot directory.

        Args:
            page: Playwright Page object
            screenshot_dir: Directory path for error screenshots
        """
        self.page = page
        self.screenshot_dir = Path(screenshot_dir)

    def goto(self, base_url: str) -> None:
        """
        Navigate to the login page.

        Args:
            base_url: Base URL of the site (e.g., "https://demo.testfire.net")

        """
        self.page.goto(f"{base_url}/login.jsp", wait_until="domcontentloaded")

    def login(self, username: str, password: str) -> None:
        """
        Perform login by filling credentials and submitting form.

        Args:
            username: User login name
            password: User password
        """
        self.page.fill("#uid", username)
        self.page.fill("#passw", password)
        self.page.click('input[name="btnSubmit"]')
        self.page.wait_for_selector("text=MY ACCOUNT", timeout=self.LOGIN_WAIT_TIMEOUT)

    def assert_logged_in(self) -> None:
        """
        Assert that user is logged in with stronger verification.
        """
        expect(self.page.locator("text=MY ACCOUNT")).to_be_visible(
            timeout=self.ASSERT_LOGIN_TIMEOUT
        )

    def is_logged_in(self) -> bool:
        """
        Check if user is currently logged in without raising exceptions.

        Performs two checks:
        1. "MY ACCOUNT" text is visible (indicates logged in)
        2. Login form is NOT visible (confirms not on login page)

        Returns:
            True if both checks pass, False otherwise or on exception
        """
        try:
            my_account_visible = self.page.locator("text=MY ACCOUNT").is_visible(
                timeout=self.SESSION_CHECK_TIMEOUT
            )
            login_form_hidden = not self.page.locator('input[name="uid"]').is_visible(
                timeout=self.FORM_CHECK_TIMEOUT
            )
            return my_account_visible and login_form_hidden
        except Exception:
            return False

    def is_logged_out(self) -> bool:
        """
        Check if user has been logged out or session expired.

        Performs two checks:
        1. Login form is visible (indicates logged out)
        2. Current URL contains "/login.jsp" or is root page

        Returns:
            True if either check passes, True on exception (safe default)
        """
        try:
            login_form_visible = self.page.locator('input[name="uid"]').is_visible(
                timeout=self.SESSION_CHECK_TIMEOUT
            )
            current_url = self.page.url
            on_login_page = "/login.jsp" in current_url or current_url.endswith("/")

            return login_form_visible or on_login_page
        except Exception:
            return True  # Assume logged out if state cannot be determined

    def capture_error_message(self) -> str:
        """
        Capture login error message from page if visible.

        Returns:
            Error message text if present, empty string otherwise
        """
        msg_locator = self.page.locator("span#_ctl0__ctl0_Content_Main_message")
        return msg_locator.inner_text().strip() if msg_locator.count() else ""

    def error_screenshot(self, tag: str) -> str:
        """
        Take a screenshot for failed login attempts.

        Args:
            tag: Identifier tag for the screenshot filename

        Returns:
            Full path to the saved screenshot file

        Note:
            Filename format: {tag}_{timestamp}.png
            Creates screenshot directory if it doesn't exist
        """
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{tag}_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        self.page.screenshot(path=str(screenshot_path))
        return str(screenshot_path)
