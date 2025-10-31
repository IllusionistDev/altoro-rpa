"""Part 4: Automated fund transfer with balance verification orchestration."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
from src.web.browser import browser_session
from src.web.pages.accounts_page import AccountsPage
from src.web.pages.transfer_page import TransferPage
from src.core.config import settings
from src.core.excel import ExcelWriter
from src.core.logger import log
from src.core.utils import clean_account_name
from src.core.constants import SHEET_TRANSFER_DETAILS
from src.core.auth_helpers import authenticate_user, setup_session_context


def get_balances(accounts_page: AccountsPage) -> Dict[str, Dict[str, Any]]:
    """
    Helper function to get account balances indexed by account name.

    Args:
        accounts_page: AccountsPage instance to read balances from

    Returns:
        Dictionary mapping account_name to account data containing:
        - account_id: Account identifier
        - account_name: Account name/type
        - total: Total balance
        - available: Available balance
    """
    accounts = accounts_page.read_table()
    accounts_by_name = {account["account_name"]: account for account in accounts}
    return accounts_by_name


def run_part4_transfer() -> None:
    """
    Execute Part 4: Automated fund transfer with verification and confirmation capture.

    Workflow:
    1. Authenticate user via login page
    2. Navigate to Account Summary and capture balances BEFORE transfer
    3. Execute fund transfer:
       - Source: 800002 Savings
       - Destination: 800003 Checking
       - Amount: $250.00
    4. Capture transfer confirmation:
       - Confirmation message
       - Reference number (if available)
       - Screenshot of confirmation
    5. Navigate to Account Summary and capture balances AFTER transfer
    6. Verify balance changes match transfer amount:
       - Source balance decreased by $250
       - Destination balance increased by $250
    7. Save comprehensive transfer details to Excel:
       - "Transfer_Details" sheet with all information

    Features:
    - Automatic balance verification
    - Confirmation message capture
    - Reference number extraction
    - Screenshot documentation
    - Before/after balance tracking
    - Session recovery on timeout
    - Overwrites existing Excel file

    Raises:
        AssertionError: If balance changes don't match expected transfer amount

    Note:
        Uses configuration from settings:
        - transfer_from: "800002 Savings"
        - transfer_to: "800003 Checking"
        - transfer_amount: 250.00
        Saves browser trace to settings.trace_dir
        Saves screenshot to settings.screenshot_dir
        Excel file saved to settings.excel_path
    """
    with browser_session(settings.trace_dir) as browser_context:
        page = browser_context.new_page()

        # Authenticate user
        login_page = authenticate_user(page, settings.screenshot_dir)

        # Get balances BEFORE transfer
        accounts_page = AccountsPage(page)
        setup_session_context(accounts_page, login_page)
        accounts_page.open()
        balances_before = get_balances(accounts_page)
        log.info(
            f"Captured balances BEFORE transfer for {len(balances_before)} accounts"
        )

        # Initialize TransferPage with session recovery
        transfer_page = TransferPage(page, settings.screenshot_dir)
        setup_session_context(transfer_page, login_page)

        # Execute transfer
        log.info(
            f"Executing transfer: {settings.transfer_from} → {settings.transfer_to}, "
            f"Amount: ${settings.transfer_amount:.2f}"
        )
        transfer_result = transfer_page.run_transfer(
            settings.transfer_from, settings.transfer_to, settings.transfer_amount
        )
        log.info(f"Transfer executed - Status: {transfer_result['status']}")
        log.info(f"Confirmation: {transfer_result['confirmation_message']}")
        if transfer_result["reference_number"]:
            log.info(f"Reference Number: {transfer_result['reference_number']}")
        log.info(f"Screenshot saved: {transfer_result['screenshot']}")

        # Get balances AFTER transfer
        accounts_page.open()
        balances_after = get_balances(accounts_page)
        log.info(f"Captured balances AFTER transfer for {len(balances_after)} accounts")

    # Extract balances for verification
    source_account = balances_before.get(settings.transfer_from)
    destination_account = balances_before.get(settings.transfer_to)

    if not source_account:
        log.error(f"Source account '{settings.transfer_from}' not found in balances")
        raise ValueError(f"Source account '{settings.transfer_from}' not found")

    if not destination_account:
        log.error(f"Destination account '{settings.transfer_to}' not found in balances")
        raise ValueError(f"Destination account '{settings.transfer_to}' not found")

    source_balance_before = source_account["total"]
    destination_balance_before = destination_account["total"]

    source_balance_after = balances_after[settings.transfer_from]["total"]
    destination_balance_after = balances_after[settings.transfer_to]["total"]

    # Verify balance changes
    log.info("Verifying balance changes...")
    source_expected = round(source_balance_before - settings.transfer_amount, 2)
    source_actual = round(source_balance_after, 2)
    destination_expected = round(
        destination_balance_before + settings.transfer_amount, 2
    )
    destination_actual = round(destination_balance_after, 2)

    source_verified = source_expected == source_actual
    destination_verified = destination_expected == destination_actual

    if source_verified:
        log.info(
            f"Source balance verified: ${source_balance_before:.2f} → ${source_balance_after:.2f}"
        )
    else:
        log.error(
            f"Source balance mismatch: "
            f"Expected ${source_expected:.2f}, Got ${source_actual:.2f}"
        )

    if destination_verified:
        log.info(
            f"Destination balance verified: ${destination_balance_before:.2f} → ${destination_balance_after:.2f}"
        )
    else:
        log.error(
            f"Destination balance mismatch: "
            f"Expected ${destination_expected:.2f}, Got ${destination_actual:.2f}"
        )

    # Assert verification (will raise if failed)
    assert source_verified, (
        f"Source balance mismatch after transfer: "
        f"expected ${source_expected:.2f}, got ${source_actual:.2f}"
    )
    assert destination_verified, (
        f"Destination balance mismatch after transfer: "
        f"expected ${destination_expected:.2f}, got ${destination_actual:.2f}"
    )

    log.info("All balance changes verified successfully")

    # Prepare Excel output
    transfer_details_df = pd.DataFrame(
        [
            {
                "Source Account": clean_account_name(settings.transfer_from),
                "Destination Account": clean_account_name(settings.transfer_to),
                "Transfer Amount": settings.transfer_amount,
                "Confirmation Message": transfer_result["confirmation_message"],
                "Transaction Timestamp": transfer_result["timestamp"],
                "Source Balance Before": source_balance_before,
                "Source Balance After": source_balance_after,
                "Destination Balance Before": destination_balance_before,
                "Destination Balance After": destination_balance_after,
            }
        ]
    )

    # Write to Excel
    output_path = Path(settings.excel_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    excel_writer = ExcelWriter(str(output_path))
    excel_writer.write_df(SHEET_TRANSFER_DETAILS, transfer_details_df)
    excel_writer.close()

    log.info(f"Transfer details written to Excel → {output_path}")
    log.info("Part 4 complete - Transfer executed and verified successfully")


if __name__ == "__main__":
    run_part4_transfer()
