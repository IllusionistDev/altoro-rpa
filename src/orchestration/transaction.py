"""Part 3: Transaction analysis and advanced filtering automation orchestration."""

import pandas as pd
from pathlib import Path
from src.web.browser import browser_session
from src.web.pages.transactions_page import TransactionsPage
from src.core.config import settings
from src.core.excel import ExcelWriter
from src.core.logger import log
from src.core.constants import (
    SHEET_FILTERED_TRANSACTIONS,
    SHEET_HIGH_VALUE_CREDITS,
    HIGH_VALUE_CREDIT_THRESHOLD,
    TRANSACTION_DISPLAY_COLUMNS,
)
from src.core.auth_helpers import authenticate_and_setup


def run_part3_transactions() -> None:
    """
    Execute Part 3: Transaction analysis with date filtering and credit analysis.

    Workflow:
    1. Authenticate user via login page
    2. Navigate to "View Recent Transactions" page
    3. Apply date range filter (2025-02-01 to 2025-04-15)
    4. Extract ALL transactions across ALL accounts from single table
    5. Create analysis reports:
       - Date-filtered transactions
       - High-value credit analysis (>= $150)
    6. Save data to Excel sheets

    Task 3.1: Date-Range Transaction Filtering
    - Filter dates: 02/01/2025 - 04/15/2025 (from settings)
    - Excel sheet: "Filtered_Transactions"

    Task 3.2: High-Value Credit Analysis
    - Filter: Credits >= $150.00
    - Sort: Descending by credit amount
    - Excel sheet: "High_Value_Credits"

    Features:
    - Single unified transaction view across all accounts
    - Web-based date filtering (no programmatic iteration needed)
    - Session recovery on timeout
    - Overwrites existing Excel file

    Note:
        Uses configuration from settings:
        - base_url, user, password: Authentication
        - filter_start, filter_end: Date range (yyyy-mm-dd format)
        - transaction_time_format: Datetime parsing format
        - excel_path: Output file path
        Saves browser trace to settings.trace_dir
    """
    with browser_session(settings.trace_dir) as browser_context:
        page = browser_context.new_page()

        # Authenticate user and setup session context
        transactions_page = TransactionsPage(page)
        authenticate_and_setup(page, settings.screenshot_dir, transactions_page)

        # Navigate to Recent Transactions page
        transactions_page.open_recent()
        log.info("Navigated to Recent Transactions page")

        # Apply date range filter and extract transactions
        # Note: Web UI filters all accounts automatically
        transactions_page.filter_dates(settings.filter_start, settings.filter_end)
        log.info(
            f"Applied date filter: {settings.filter_start} to {settings.filter_end}"
        )

        # Extract all filtered transactions
        all_transactions = transactions_page.read_transactions(
            settings.transaction_time_format
        )
        log.info(f"Extracted {len(all_transactions)} transactions from all accounts")

    # Convert to DataFrame for analysis
    transactions_df = pd.DataFrame(all_transactions)

    # Task 3.1: Filtered Transactions with Summary Statistics
    if not transactions_df.empty:
        # Prepare display DataFrame (exclude internal fields for cleaner Excel output)
        display_df = transactions_df[
            [
                "transaction_id",
                "transaction_time",
                "account_id",
                "action",
                "debit",
                "credit",
            ]
        ].copy()

        # Rename columns for better Excel presentation
        display_df.columns = TRANSACTION_DISPLAY_COLUMNS
        filtered_df = display_df

        log.info(f"Task 3.1 Summary - {len(filtered_df)} transactions extracted")
    else:
        log.warning("No transactions found in specified date range")
        filtered_df = pd.DataFrame(columns=TRANSACTION_DISPLAY_COLUMNS)

    # Task 3.2: High-Value Credit Analysis
    if not transactions_df.empty:
        # Filter for credits >= threshold (exclude summary row)
        high_value_mask = transactions_df["credit"] >= HIGH_VALUE_CREDIT_THRESHOLD
        high_value_df = transactions_df[high_value_mask].copy()

        if not high_value_df.empty:
            # Sort by credit amount in descending order
            high_value_df = high_value_df.sort_values("credit", ascending=False)

            # Prepare display DataFrame
            display_high_value = high_value_df[
                [
                    "transaction_id",
                    "transaction_time",
                    "account_id",
                    "action",
                    "debit",
                    "credit",
                ]
            ].copy()

            display_high_value.columns = TRANSACTION_DISPLAY_COLUMNS
            high_value_credits_df = display_high_value

            log.info(
                f"Task 3.2 Summary - "
                f"High-value credits (>= ${HIGH_VALUE_CREDIT_THRESHOLD:.2f}): {len(high_value_df)} transactions"
            )
        else:
            log.warning(
                f"No credit transactions >= ${HIGH_VALUE_CREDIT_THRESHOLD:.2f} found"
            )
            high_value_credits_df = pd.DataFrame(columns=TRANSACTION_DISPLAY_COLUMNS)
    else:
        high_value_credits_df = pd.DataFrame(columns=TRANSACTION_DISPLAY_COLUMNS)

    # Write Excel Output
    output_path = Path(settings.excel_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    excel_writer = ExcelWriter(str(output_path))

    # Sheet 1: Filtered Transactions (Task 3.1)
    excel_writer.write_df(SHEET_FILTERED_TRANSACTIONS, filtered_df)
    log.info(f"Wrote {SHEET_FILTERED_TRANSACTIONS} sheet ({len(filtered_df)} rows)")

    # Sheet 2: High Value Credits (Task 3.2)
    excel_writer.write_df(SHEET_HIGH_VALUE_CREDITS, high_value_credits_df)
    log.info(
        f"Wrote {SHEET_HIGH_VALUE_CREDITS} sheet ({len(high_value_credits_df)} rows)"
    )

    excel_writer.close()

    log.info(f"Part 3 complete → Excel workbook saved to {output_path}")


if __name__ == "__main__":
    run_part3_transactions()
