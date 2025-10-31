"""Account summary page automation for Altoro Mutual."""

from typing import Dict, List, Iterator, Tuple, Optional, Any
from playwright.sync_api import Page, Locator

from src.core.utils import parse_money, clean_account_name
from src.web.pages.base_page import BasePage
from src.core.session_handler import with_session_retry
from src.core.constants import (
    SELECTOR_ACCOUNT_DROPDOWN,
    SELECTOR_GET_ACCOUNT_BUTTON,
    ACCOUNT_SUMMARY_COLUMNS,
)
from src.core.logger import log


class AccountsPage(BasePage):
    """
    Handles account summary and transaction history scraping.

    Provides methods for:
    - Navigating to account summary page
    - Iterating through multiple accounts
    - Parsing account balance information
    - Extracting transaction history (credits and debits)
    - Auto-recovery from session timeouts

    Attributes:
        accounts_summary: Dictionary mapping account_id to balance data
        transaction_history: Dictionary mapping account_id to transaction list
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize AccountsPage with Playwright page.

        Args:
            page: Playwright Page object for browser automation
        """
        super().__init__(page)
        self.accounts_summary: Dict[str, Dict[str, Any]] = {}
        self.transaction_history: Dict[str, List[Dict[str, Any]]] = {}

    def open(self) -> None:
        """
        Navigate to the Account Summary page.

        Clicks the "View Account Summary" link using humanized behavior.
        """
        link = self.page.get_by_role("link", name="View Account Summary")
        if link.count():
            self.click(link, description="View Account Summary link")

    def get_account_list(self) -> List[Dict[str, str]]:
        """
        Get list of all available accounts from the dropdown selector.

        Returns:
            List of dictionaries, each containing:
            - "account_id": Account ID/number
            - "account_name": Account name/type

        Note:
            This method only reads the dropdown options without changing UI state.
            Use iter_accounts() if you need to navigate through each account.
        """
        account_options = self.page.locator(f"{SELECTOR_ACCOUNT_DROPDOWN} option").all()
        accounts = []

        for option in account_options:
            account_id = option.get_attribute("value")
            account_name = option.inner_text().strip()

            if account_id and account_id.strip():
                accounts.append(
                    {
                        "account_id": account_id.strip(),
                        "account_name": clean_account_name(account_name),
                    }
                )

        return accounts

    def read_table(self) -> List[Dict[str, Any]]:
        """
        Read all account data with balances by iterating through accounts.

        This is a convenience method that combines account listing with balance extraction.
        It iterates through each account, extracts balance information, and returns
        a consolidated list.

        Returns:
            List of dictionaries, each containing:
            - "account_id": Account ID/number
            - "account_name": Account name/type
            - "total": Total balance
            - "available": Available balance

        Note:
            This method changes UI state by clicking through accounts.
            Each account is selected and its balance is read.
            Useful for getting snapshot of all account balances.

        Warning:
            This method modifies page state. If you need to preserve current state,
            use get_account_list() instead (which only reads dropdown options).
        """
        accounts_data = []

        for account_id, account_name in self.iter_accounts():
            # Parse balance summary for this account
            summary = self.parse_summary()

            # Compile account data
            account_record = {
                "account_id": account_id,
                "account_name": account_name,
                "total": summary.get("Total Balance", 0.0),
                "available": summary.get("Available Balance", 0.0),
            }
            accounts_data.append(account_record)

        return accounts_data

    def iter_accounts(self) -> Iterator[Tuple[str, str]]:
        """
        Iterate through all accounts in the dropdown selector.

        For each account:
        1. Selects the account from dropdown
        2. Clicks "Get Account" button
        3. Yields account ID and name

        Yields:
            Tuple of (account_id, account_name) for each account

        Example:
            >>> for account_id, name in accounts_page.iter_accounts():
            ...     print(f"Processing {account_id}: {name}")
        """
        accounts = self.page.locator(f"{SELECTOR_ACCOUNT_DROPDOWN} option").all()
        log.info(f"Found Accounts: {len(accounts)}")
        for account in accounts:
            account_id = account.get_attribute("value").strip()
            account_name = account.inner_text().strip()
            self.select_option(SELECTOR_ACCOUNT_DROPDOWN, value=account_id)
            self.click(SELECTOR_GET_ACCOUNT_BUTTON)
            yield account_id, account_name

    def parse_summary(self) -> Dict[str, Any]:
        """
        Parse the Balance Detail table to extract Total Balance and Available Balance.

        Searches for the Balance Detail table in the page HTML and extracts:
        - Ending balance (mapped to "Total Balance")
        - Available balance

        Returns:
            Dictionary with keys:
            - "Total Balance": Float value from ending balance row
            - "Available Balance": Float value from available balance row
            Returns zeros if table not found.

        Note:
            Uses Playwright locators to parse the page DOM.
        """
        # Find the Balance Detail table by looking for the header
        balance_table = None
        tables = self.page.locator("table").all()

        for table in tables:
            # Check if this table has a <th> containing "Balance Detail"
            headers = table.locator("th").all()
            for header in headers:
                if "Balance Detail" in header.inner_text():
                    balance_table = table
                    break
            if balance_table:
                break

        if not balance_table:
            return {"Total Balance": 0.0, "Available Balance": 0.0}

        # Extract all rows
        rows = balance_table.locator("tr").all()

        total_balance = 0.0
        available_balance = 0.0

        for row in rows:
            cells = row.locator("td").all()
            if len(cells) >= 2:
                label = cells[0].inner_text().strip()
                value = cells[1].inner_text().strip()

                # Check for "Ending balance" (maps to Total Balance)
                if "Ending balance" in label:
                    total_balance = parse_money(value)
                # Check for "Available balance"
                elif "Available balance" in label:
                    available_balance = parse_money(value)
        return {"Total Balance": total_balance, "Available Balance": available_balance}

    def parse_transaction_history_table(
        self, table: Optional[Locator], credit: bool
    ) -> List[Dict[str, Any]]:
        """
        Parse a single transaction table (either Credits or Debits).

        Args:
            table: Playwright Locator object representing the table element
            credit: True if parsing credits table, False if parsing debits table

        Returns:
            List of transaction dictionaries, each containing:
            - "Transaction Date": Date string from table
            - "Transaction Description": Description text from table
            - "Credit Amount" or "Debit Amount": Parsed float value

        Note:
            Returns empty list if table is None.
            Amount key changes based on credit parameter.
        """
        if not table:
            return []
        records = []
        rows = table.locator("tr").all()
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) >= 4:
                amount_key = "Credit Amount" if credit else "Debit Amount"
                transaction = {
                    "Transaction Date": cells[1].inner_text().strip(),
                    "Transaction Description": cells[2].inner_text().strip(),
                    amount_key: parse_money(cells[3].inner_text().strip()),
                }
                records.append(transaction)
        return records

    def parse_account_transaction_history(self) -> List[Dict[str, Any]]:
        """
        Parse Credits and Debits transaction tables and combine them into a single list.

        Searches for two separate tables on the page:
        - Credits table (div#credits)
        - Debits table (div#debits)

        Combines all transactions into a single list.

        Returns:
            List of transaction dictionaries, each containing:
            - "Transaction Date": Date string
            - "Transaction Description": Description text
            - "Credit Amount": Float value (for credit transactions)
            - "Debit Amount": Float value (for debit transactions)

        Note:
            Waits for page load state before parsing.
            Returns empty list if no transaction tables found.
        """
        self.page.wait_for_load_state()
        transactions = []

        # Parse Credits table
        credits_div = self.page.locator("div#credits").first
        if credits_div.is_visible():
            credits_table = credits_div.locator("table").first
            if credits_table.count() > 0:
                transactions.extend(
                    self.parse_transaction_history_table(credits_table, credit=True)
                )

        # Parse Debits table
        debits_div = self.page.locator("div#debits").first
        if debits_div.is_visible():
            debits_table = debits_div.locator("table").first
            if debits_table.count() > 0:
                transactions.extend(
                    self.parse_transaction_history_table(debits_table, credit=False)
                )

        return transactions

    @with_session_retry()
    def run(self) -> None:
        """
        Run account scraping with automatic session recovery.

        Iterates through all accounts, collecting summary and transaction data.
        If session expires during iteration, automatically re-authenticates and retries.

        Populates:
            self.accounts_summary: Dictionary mapping account_id to balance data
            self.transaction_history: Dictionary mapping account_id to transaction list

        Note:
            Decorated with @with_session_retry for automatic recovery from session timeouts.
            Maximum 2 retry attempts on session expiration.
        """
        for account_id, account_name in self.iter_accounts():
            # Account Summary
            account_summary = self.parse_summary()
            account_summary[ACCOUNT_SUMMARY_COLUMNS[0]] = account_id
            account_summary[ACCOUNT_SUMMARY_COLUMNS[1]] = clean_account_name(
                account_name
            )
            self.accounts_summary[account_id] = account_summary
            # Transaction history
            transactions = self.parse_account_transaction_history()
            self.transaction_history[account_id] = transactions
