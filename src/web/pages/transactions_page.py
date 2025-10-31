"""Transaction history page automation for Altoro Mutual."""

from typing import List, Dict, Any
from datetime import datetime
from playwright.sync_api import Page

from src.core.utils import parse_money
from src.web.pages.base_page import BasePage
from src.core.constants import SELECTOR_TRANSACTIONS_TABLE


class TransactionsPage(BasePage):
    """
    Handles transaction history viewing and filtering operations.

    Provides methods for:
    - Navigating to recent transactions page
    - Applying date range filters to transactions
    - Parsing and extracting transaction data
    - Auto-recovery from session timeouts

    Page Structure (as per actual HTML):
    - Shows ALL transactions from ALL accounts in a single table
    - Table columns: Transaction ID, Transaction Time, Account ID, Action, Amount
    - Date filter with "After" and "Before" fields (yyyy-mm-dd format)
    - No account selector dropdown

    Typical transaction record contains:
        - transaction_id: Unique transaction identifier
        - transaction_time: Timestamp of transaction
        - account_id: Account ID where transaction occurred
        - action: "Deposit" or "Withdrawal"
        - amount: Transaction amount (positive for deposits, negative for withdrawals)
        - debit: Debit amount (for reporting)
        - credit: Credit amount (for reporting)
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize TransactionsPage with Playwright page.

        Args:
            page: Playwright Page object for browser automation
        """
        super().__init__(page)

    def open_recent(self) -> None:
        """
        Navigate to the Recent Transactions page.

        Clicks the "View Recent Transactions" link if available.
        Uses humanized clicking behavior from BasePage.
        """
        link = self.page.get_by_role("link", name="View Recent Transactions")
        if link.count():
            self.click(link, description="View Recent Transactions link")

    def filter_dates(self, start_date: str, end_date: str) -> None:
        """
        Apply date range filter to transaction list.

        Args:
            start_date: Start date string in YYYY-MM-DD format (After date)
            end_date: End date string in YYYY-MM-DD format (Before date)

        Note:
            - Fills "After" and "Before" date fields
            - Clicks Submit button
            - Waits for filtered results to load
            - Date format must be yyyy-mm-dd as required by the web form
        """
        # Find date input fields by their name attributes
        start_date_field = self.page.locator('input[name="startDate"]')
        end_date_field = self.page.locator('input[name="endDate"]')

        if start_date_field.count() and end_date_field.count():
            self.fill(
                start_date_field, start_date, description="After (startDate) field"
            )
            self.fill(end_date_field, end_date, description="Before (endDate) field")

            # Find and click the Submit button
            submit_button = self.page.locator('input[type="submit"][value="Submit"]')
            self.click(submit_button, description="Submit button")

            # Wait for filtered results to load
            self.page.wait_for_load_state()

    def read_transactions(self, time_format: str) -> List[Dict[str, Any]]:
        """
        Parse and extract all transactions from the transaction table.

        Args:
            time_format: Datetime format string for parsing (e.g., "%Y-%m-%d %H:%M")

        Returns:
            List of transaction dictionaries, each containing:
            - transaction_id: str - Unique transaction ID
            - transaction_time: datetime - Transaction timestamp
            - account_id: str - Account ID
            - action: str - "Deposit" or "Withdrawal"
            - amount: float - Raw amount (positive or negative)
            - debit: float - Debit amount (0.0 for deposits)
            - credit: float - Credit amount (0.0 for withdrawals)

        Note:
            Table structure (actual HTML):
            - Column 0: Transaction ID
            - Column 1: Transaction Time (YYYY-MM-DD HH:MM)
            - Column 2: Account ID
            - Column 3: Action (Deposit/Withdrawal)
            - Column 4: Amount ($X.XX or -$X.XX)

            Conversion logic:
            - If Action = "Withdrawal" OR Amount is negative: debit = abs(amount), credit = 0
            - If Action = "Deposit" OR Amount is positive: credit = amount, debit = 0

            Returns empty list if no transactions found.
        """
        # Locate the transaction table by its ID
        table_locator = self.page.locator(SELECTOR_TRANSACTIONS_TABLE)

        # Get all table rows
        table_rows = table_locator.locator("tr").all()

        # Skip header row (first row)
        data_rows = table_rows[1:] if len(table_rows) > 1 else []

        transactions = []
        for row in data_rows:
            cells = [cell.inner_text().strip() for cell in row.locator("td").all()]

            # Ensure row has all required columns (5 columns)
            if len(cells) >= 5:
                # Parse each column
                transaction_id = cells[0]
                transaction_time_str = cells[1]
                account_id = cells[2]
                action = cells[3]
                amount_str = cells[4]

                # Parse transaction time
                try:
                    transaction_time = datetime.strptime(
                        transaction_time_str, time_format
                    )
                except ValueError:
                    # Skip row if time parsing fails
                    continue

                # Parse amount
                amount = parse_money(amount_str)

                # Determine debit/credit based on action and amount
                if action == "Withdrawal" or amount < 0:
                    debit = abs(amount)
                    credit = 0.0
                else:  # Deposit or positive amount
                    debit = 0.0
                    credit = abs(amount)

                transaction = {
                    "transaction_id": transaction_id,
                    "transaction_time": transaction_time,
                    "account_id": account_id,
                    "action": action,
                    "amount": amount,
                    "debit": debit,
                    "credit": credit,
                }
                transactions.append(transaction)

        return transactions
