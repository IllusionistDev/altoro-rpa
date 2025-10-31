"""Fund transfer page automation for Altoro Mutual."""

from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import Page

from src.web.pages.base_page import BasePage
from src.core.session_handler import with_session_retry


class TransferPage(BasePage):
    """
    Handles fund transfer operations between accounts.

    Provides methods for:
    - Navigating to Transfer Funds page
    - Selecting source and destination accounts
    - Executing fund transfers
    - Capturing confirmation messages and details
    - Taking screenshots of confirmations
    - Auto-recovery from session timeouts

    Page Structure (as per actual HTML):
    - Form ID: tForm
    - From Account dropdown: #fromAccount (select by value)
    - To Account dropdown: #toAccount (select by value)
    - Transfer Amount input: #transferAmount
    - Submit button: input[type="submit"][value="Transfer Money"]
    - Confirmation spans: #_ctl0__ctl0_Content_Main_postResp, #soapResp

    Typical confirmation contains:
        - Success message text
        - Transaction/reference number (if available)
        - Timestamp information
    """

    def __init__(self, page: Page, screenshot_dir: str) -> None:
        """
        Initialize TransferPage with Playwright page and screenshot directory.

        Args:
            page: Playwright Page object for browser automation
            screenshot_dir: Directory path for saving screenshots
        """
        super().__init__(page)
        self.screenshot_dir = Path(screenshot_dir)

    def navigate(self) -> None:
        """
        Navigate to the Transfer Funds page.

        Clicks the "Transfer Funds" link using humanized behavior.
        """
        link = self.page.get_by_role("link", name="Transfer Funds")
        if link.count():
            self.click(link, description="Transfer Funds link")

    def execute_transfer(
        self, from_account_value: str, to_account_value: str, amount: float
    ) -> None:
        """
        Execute a fund transfer between two accounts.

        Args:
            from_account_value: Source account ID value (e.g., "800002")
            to_account_value: Destination account ID value (e.g., "800003")
            amount: Amount to transfer (will be formatted to 2 decimal places)

        Note:
            - Uses account VALUES from dropdown, not labels
            - For "800002 Savings", use value="800002"
            - Waits for confirmation message after submission
        """
        # Select source account by value
        from_account_dropdown = self.page.locator("#fromAccount")
        self.select_option(
            from_account_dropdown, value=from_account_value, description="From Account"
        )

        # Select destination account by value
        to_account_dropdown = self.page.locator("#toAccount")
        self.select_option(
            to_account_dropdown, value=to_account_value, description="To Account"
        )

        # Fill transfer amount
        amount_field = self.page.locator("#transferAmount")
        self.fill(amount_field, f"{amount:.2f}", description="Transfer Amount field")

        # Submit the transfer
        submit_button = self.page.locator(
            'input[type="submit"][value="Transfer Money"]'
        )
        self.click(submit_button, description="Transfer Money button")

        # Wait for confirmation message to appear
        self.page.wait_for_load_state()

    def capture_confirmation(self) -> Dict[str, str]:
        """
        Capture confirmation message and extract details from response.

        Attempts to extract:
        - Confirmation message text
        - Reference/transaction number (if present)
        - Any additional confirmation details

        Returns:
            Dictionary containing:
            - "message": Full confirmation message text
            - "reference_number": Transaction/reference number if found, empty string otherwise
            - "status": "success" or "error"

        Note:
            Checks multiple possible confirmation span locations:
            - #_ctl0__ctl0_Content_Main_postResp
            - #soapResp
            - Text containing "successfully transferred"
        """
        confirmation_data = {"message": "", "reference_number": "", "status": "unknown"}

        # Try to get confirmation from primary response span
        primary_span = self.page.locator("#_ctl0__ctl0_Content_Main_postResp")
        if primary_span.count() > 0:
            message_text = primary_span.inner_text().strip()
            if message_text:
                confirmation_data["message"] = message_text
                if "successfully" in message_text.lower():
                    confirmation_data["status"] = "success"

        # Try to get confirmation from SOAP response span
        soap_span = self.page.locator("#soapResp")
        if soap_span.count() > 0:
            soap_text = soap_span.inner_text().strip()
            if soap_text:
                # If primary was empty, use this
                if not confirmation_data["message"]:
                    confirmation_data["message"] = soap_text
                if "successfully" in soap_text.lower():
                    confirmation_data["status"] = "success"

        # Fallback: Check for any element containing success message
        if not confirmation_data["message"]:
            try:
                success_element = self.page.get_by_text("successfully transferred")
                if success_element.count() > 0:
                    confirmation_data["message"] = success_element.inner_text().strip()
                    confirmation_data["status"] = "success"
            except Exception:
                pass

        return confirmation_data

    def take_screenshot(self, tag: str) -> str:
        """
        Take a screenshot for transfer confirmation.

        Args:
            tag: Identifier tag for the screenshot filename

        Returns:
            Full path to the saved screenshot file

        Note:
            Filename format: {tag}_{timestamp}.png
            Creates screenshot directory if it doesn't exist
            Uses UTC timestamp
        """
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{tag}_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        self.page.screenshot(path=str(screenshot_path))
        return str(screenshot_path)

    @with_session_retry()
    def run_transfer(
        self, from_account_label: str, to_account_label: str, amount: float
    ) -> Dict[str, Any]:
        """
        Execute complete transfer workflow with session recovery.

        Workflow:
        1. Navigate to Transfer Funds page
        2. Execute transfer
        3. Capture confirmation details
        4. Take screenshot
        5. Return comprehensive transfer result

        Args:
            from_account_label: Source account label (e.g., "800002 Savings")
            to_account_label: Destination account label (e.g., "800003 Checking")
            amount: Amount to transfer

        Returns:
            Dictionary containing:
            - "from_account_value": Source account ID
            - "to_account_value": Destination account ID
            - "amount": Transfer amount
            - "confirmation_message": Success message text
            - "reference_number": Transaction reference if available
            - "status": "success" or "error"
            - "screenshot": Path to screenshot file
            - "timestamp": UTC timestamp of transfer

        Note:
            Decorated with @with_session_retry for automatic recovery from session timeouts.
            Maximum 2 retry attempts on session expiration.
            Parses account labels to extract account values (e.g., "800002 Savings" → "800002").
        """
        # Extract account values from labels
        # Format: "800002 Savings" → "800002"
        from_account_value = from_account_label.split()[0]
        to_account_value = to_account_label.split()[0]

        # Navigate to transfer page
        self.navigate()

        # Execute the transfer
        self.execute_transfer(from_account_value, to_account_value, amount)

        # Capture confirmation details
        confirmation = self.capture_confirmation()

        # Take screenshot
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        screenshot_path = self.take_screenshot("transfer")

        # Compile result
        result = {
            "from_account_value": from_account_value,
            "to_account_value": to_account_value,
            "amount": amount,
            "confirmation_message": confirmation["message"],
            "reference_number": confirmation["reference_number"],
            "status": confirmation["status"],
            "screenshot": screenshot_path,
            "timestamp": timestamp,
        }

        return result
