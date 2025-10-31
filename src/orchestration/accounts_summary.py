"""Part 2: Account summary and transaction history automation orchestration."""

import pandas as pd
from src.web.browser import browser_session
from src.web.pages.accounts_page import AccountsPage
from src.core.config import settings
from src.core.logger import log
from src.core.auth_helpers import authenticate_user, setup_session_context
from src.core.excel_helpers import write_single_sheet
from src.core.constants import SHEET_ACCOUNT_SUMMARY, SHEET_TRANSACTIONS_PREFIX


def run_part2_accounts() -> None:
    """
    Execute Part 2: Account summary and transaction history scraping.

    Workflow:
    1. Authenticate user via login page
    2. Navigate to account summary page
    3. Iterate through all accounts and extract:
       - Account balances (Total Balance, Available Balance)
       - Transaction history (Credits and Debits)
    4. Save data to Excel files:
       - Account_Summary.xlsx: All account balances
       - Transactions_[AccountID].xlsx: Transaction history per account

    Features:
    - Automatic session recovery if timeout occurs during scraping
    - Creates output directory if it doesn't exist
    - Overwrites existing Excel files

    Note:
        Uses configuration from settings (base_url, user, password, excel_path, etc.)
        Saves browser trace to settings.trace_dir
        All Excel files saved to parent directory of settings.excel_path
    """

    log.info("PART 2: Account Summary & Transaction History Extraction")

    with browser_session(settings.trace_dir) as browser_context:
        page = browser_context.new_page()

        # Authenticate user and setup session context
        login_page = authenticate_user(page, settings.screenshot_dir)
        accounts_page = AccountsPage(page)
        setup_session_context(accounts_page, login_page)

        # Open accounts page and run scraping (with automatic session recovery)
        log.info("Opening account summary page...")
        accounts_page.open()

        log.info("Starting account and transaction data extraction...")
        accounts_page.run()

        num_accounts = len(accounts_page.accounts_summary)
        log.info(f"Extraction complete - {num_accounts} accounts processed")

    # 1. Save Account Summary to main Excel workbook
    if accounts_page.accounts_summary:
        # Convert accounts_summary dict to list of dicts for DataFrame
        summary_data = list(accounts_page.accounts_summary.values())
        summary_df = pd.DataFrame(summary_data)

        log.info("Account Summary Statistics:")
        log.info(f"  • Total accounts: {len(summary_df)}")

        # Write to Account_Summary sheet in Altoro_Report.xlsx
        write_single_sheet(settings.excel_path, SHEET_ACCOUNT_SUMMARY, summary_df)
        log.info(f"Saved account summary to sheet: {SHEET_ACCOUNT_SUMMARY}")
    else:
        log.warning("No account summary data to save")

    # 2. Save Transaction History for each account as separate sheets in main workbook
    if accounts_page.transaction_history:
        total_transactions = 0
        sheets_written = 0

        for account_id, transactions in accounts_page.transaction_history.items():
            if transactions:
                # Convert transactions list to DataFrame
                transactions_df = pd.DataFrame(transactions)
                transaction_count = len(transactions_df)
                total_transactions += transaction_count

                # Write to Transactions_{AccountID} sheet in Altoro_Report.xlsx
                sheet_name = f"{SHEET_TRANSACTIONS_PREFIX}{account_id}"
                write_single_sheet(settings.excel_path, sheet_name, transactions_df)
                sheets_written += 1

                log.info(
                    f"Saved {transaction_count} transactions for account {account_id} to sheet: {sheet_name}"
                )
            else:
                log.warning(f"No transaction history for account {account_id}")

        log.info("Transaction Summary:")
        log.info(f"  • Total transaction sheets created: {sheets_written}")
        log.info(f"  • Total transactions extracted: {total_transactions}")
    else:
        log.warning("No transaction history data to save")

    log.info(f"Part 2 complete → Excel workbook: {settings.excel_path}")


if __name__ == "__main__":
    run_part2_accounts()
