import pandas as pd
from pathlib import Path
from src.core.config import settings
from src.core.logger import log
from src.orchestration.account_login import run_part1_login
from src.orchestration.accounts_summary import run_part2_accounts
from src.orchestration.transaction import run_part3_transactions
from src.orchestration.transfer import run_part4_transfer
from src.orchestration.products import run_part5_products
from src.orchestration.api_validate import run_part6_api_validate
from src.core.constants import SHEET_ACCOUNT_SUMMARY, SHEET_FILTERED_TRANSACTIONS


def run():
    log.info("Part 1: Login")
    run_part1_login()

    log.info("Part 2: Account summary → Excel")
    run_part2_accounts()

    log.info("Part 3: Transactions + filters + high-value")
    run_part3_transactions()

    log.info("Part 4: Transfer funds + verify")
    run_part4_transfer()

    log.info("Part 5: Product catalog")
    run_part5_products()

    log.info("Part 6: API reconciliation")
    # Load web-scraped data for comparison
    xlsx = settings.excel_path
    web_acc_df = None
    web_txn_df = None

    if Path(xlsx).exists():
        try:
            with pd.ExcelFile(xlsx) as xf:
                # Load Account Summary from Part 2
                if SHEET_ACCOUNT_SUMMARY in xf.sheet_names:
                    web_acc_df = pd.read_excel(
                        xf,
                        sheet_name=SHEET_ACCOUNT_SUMMARY,
                        dtype={"Account ID/Number": str},
                    )
                    log.info(f"  Loaded {len(web_acc_df)} web accounts for comparison")

                # Load Filtered Transactions from Part 3
                if SHEET_FILTERED_TRANSACTIONS in xf.sheet_names:
                    web_txn_df = pd.read_excel(
                        xf,
                        sheet_name=SHEET_FILTERED_TRANSACTIONS,
                        dtype={"Account ID": str},
                    )
                    # Remove summary rows (check for display column name "Transaction ID")
                    if "Transaction ID" in web_txn_df.columns:
                        web_txn_df = web_txn_df[web_txn_df["Transaction ID"].notna()]
                    elif "transaction_id" in web_txn_df.columns:
                        web_txn_df = web_txn_df[web_txn_df["transaction_id"].notna()]
                    log.info(
                        f"  Loaded {len(web_txn_df)} web transactions for comparison"
                    )
        except Exception as e:
            log.warning(f"  Could not load web data for comparison: {e}")

    run_part6_api_validate(web_acc_df, web_txn_df)

    log.info(f"All parts complete. See: {settings.excel_path}")


if __name__ == "__main__":
    run()
