"""
Part 6: REST API Integration & Data Validation

This module implements:
- Task 6.1: API Authentication & Session Management
- Task 6.2: Programmatic Account Data Retrieval (Steps A, B, C)
- Task 6.3: Date-Filtered API Queries & Cross-Validation

The reconciliation compares API-retrieved data with web-scraped data from Parts 2-3.
"""

import pandas as pd
from typing import Dict
from src.api.client import AltoroAPI
from src.core.config import settings
from src.core.excel import ExcelWriter
from src.core.logger import log
from src.core.utils import parse_money, clean_account_name
from src.core.constants import (
    SHEET_API_VALIDATION,
    VARIANCE_TOLERANCE,
    API_SOURCE_ACCOUNT_LIST,
    API_SOURCE_ACCOUNT_DETAILS,
    API_SOURCE_TRANSACTIONS_POST,
)
from src.api.exceptions import (
    APIError,
    APIAuthenticationError,
    MaxRetriesExceededError,
    APIConnectionError,
)
from src.core.dataframe_helpers import (
    normalize_column_names,
    calculate_net_amount,
    group_and_sum_by_account,
    calculate_variance,
    add_match_status,
)


def run_part6_api_validate(
    web_accounts_df: pd.DataFrame | None = None,
    web_transactions_df: pd.DataFrame | None = None,
):
    """
    Execute Part 6: REST API Integration & Data Validation.

    This function:
    1. Authenticates with the AltoroMutual REST API using admin credentials
    2. Retrieves all account and transaction data via API endpoints
    3. Compares API data with web-scraped data from Parts 2-3
    4. Generates comprehensive reconciliation report in Excel

    Args:
        web_accounts_df: DataFrame with web-scraped account data (from Part 2)
        web_transactions_df: DataFrame with web-scraped transaction data (from Part 3)
    """

    log.info("PART 6: REST API Integration & Data Validation - Starting")

    # Task 6.1: API Authentication & Session Management
    log.info("Task 6.1: Authenticating with REST API (admin credentials)")

    try:
        # Use context manager for automatic connection cleanup
        with AltoroAPI(
            settings.base_url, settings.api_user, settings.api_password
        ) as api:
            # Authenticate and obtain token
            api.authenticate()

            # Task 6.2: Programmatic Account Data Retrieval
            log.info("\nTask 6.2: Programmatic Account Data Retrieval")
            api_accounts_data = _retrieve_api_accounts(api)
            api_transactions_data = _retrieve_api_transactions(api, api_accounts_data)

            # Task 6.3: Date-Filtered API Queries & Cross-Validation
            log.info("\nTask 6.3: Cross-Validation with Web Data")
            reconciliation_report = _perform_reconciliation(
                api_accounts_data,
                api_transactions_data,
                web_accounts_df,
                web_transactions_df,
            )

        # Generate Excel Report (outside context manager)
        _write_excel_report(reconciliation_report)

        log.info(
            f"PART 6: Completed successfully - {SHEET_API_VALIDATION} sheet generated"
        )

    except APIAuthenticationError as e:
        log.error(f"API authentication failed: {e}")
        log.warning("Invalid API credentials - skipping Part 6")
        _write_api_unavailable_report()
        return

    except (APIConnectionError, MaxRetriesExceededError) as e:
        log.error(f"API connection failed after retries: {e}")
        log.warning("API service unavailable - skipping Part 6")
        _write_api_unavailable_report()
        return

    except APIError as e:
        log.error(f"API error: {e}")
        log.warning("API operation failed - skipping Part 6")
        _write_api_unavailable_report()
        return

    except Exception as e:
        log.error(f"Unexpected error during API validation: {type(e).__name__}: {e}")
        log.warning("Part 6 failed - writing error report")
        _write_api_unavailable_report()
        return


def _retrieve_api_accounts(api: AltoroAPI) -> pd.DataFrame:
    """
    Task 6.2 - Step A & B: Retrieve Account List and Detailed Account Information.

    Args:
        api: Authenticated AltoroAPI client

    Returns:
        DataFrame with all account details from API
    """
    log.info("  Step A: Retrieving account list from API...")

    try:
        accounts_list = api.accounts()
        log.info(
            f"  Retrieved {len(accounts_list)} accounts from {API_SOURCE_ACCOUNT_LIST}"
        )
    except APIAuthenticationError as e:
        log.error(f"  Authentication error retrieving accounts: {e}")
        raise  # Re-raise to be handled by main try-except
    except (APIConnectionError, MaxRetriesExceededError) as e:
        log.error(f"  Connection/retry error retrieving accounts: {e}")
        return pd.DataFrame()
    except APIError as e:
        log.error(f"  API error retrieving accounts: {e}")
        return pd.DataFrame()

    # Step B: Get detailed information for each account
    log.info("  Step B: Retrieving detailed account information...")
    detailed_accounts = []

    for account in accounts_list:
        # Handle both string and dict responses from API
        if isinstance(account, str):
            # API returns list of account ID strings: ["800002", "800003"]
            account_id = str(account)
        elif isinstance(account, dict):
            # API returns list of account objects: [{"accountId": "800002", ...}]
            account_id = str(
                account.get("accountId")
                or account.get("id")
                or account.get("account_id", "")
            )
        else:
            log.warning(f"  Unexpected account format: {type(account)} - {account}")
            continue

        if not account_id:
            log.warning(f"  Skipping account with missing ID: {account}")
            continue

        try:
            # Fetch detailed account information
            details = api.get_account_details(account_id)
            detailed_accounts.append(
                {
                    "account_id": account_id,
                    "account_name": clean_account_name(details.get("accountName", "")),
                    "account_type": details.get("accountType", ""),
                    "balance": parse_money(details.get("balance", "0")),
                    "available_balance": parse_money(
                        details.get("availableBalance", "0")
                    ),
                    "api_source": API_SOURCE_ACCOUNT_DETAILS,
                }
            )
            log.info(f"  Account {account_id}: {details.get('accountName', 'N/A')}")
        except APIAuthenticationError:
            # Don't continue if auth fails - re-raise to stop processing
            log.error(f"  Authentication error for account {account_id}")
            raise
        except (APIError, MaxRetriesExceededError) as e:
            log.warning(f"  ⚠ Failed to get details for account {account_id}: {e}")
            # Create basic entry with just the ID when details fetch fails
            detailed_accounts.append(
                {
                    "account_id": account_id,
                    "account_name": f"Account {account_id}",
                    "account_type": "Unknown",
                    "balance": 0.0,
                    "available_balance": 0.0,
                    "api_source": f"{API_SOURCE_ACCOUNT_LIST} (basic)",
                }
            )

    df_accounts = pd.DataFrame(detailed_accounts)
    log.info(
        f"  Step B completed: {len(df_accounts)} accounts with detailed information"
    )
    return df_accounts


def _retrieve_api_transactions(
    api: AltoroAPI, accounts_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Task 6.2 - Step C: Extract Transaction History via API.

    Uses date-filtered API queries as per Task 6.3 requirements.

    Args:
        api: Authenticated AltoroAPI client
        accounts_df: DataFrame with account information

    Returns:
        DataFrame with all transactions from API (date-filtered)
    """
    log.info(
        f"  Step C: Extracting transaction history (date range: {settings.api_filter_start} to {settings.api_filter_end})..."
    )

    all_transactions = []
    for _, account in accounts_df.iterrows():
        account_id = str(account["account_id"])

        try:
            # Date-filtered API query (Task 6.3)
            transactions = api.transactions(
                account_id, start=settings.api_filter_start, end=settings.api_filter_end
            )

            log.info(f"  Account {account_id}: {len(transactions)} transactions")

            for txn in transactions:
                # Handle both string and dict transaction formats
                if isinstance(txn, str):
                    log.warning(
                        f"  Transaction returned as string: {txn[:100] if len(txn) > 100 else txn}"
                    )
                    continue  # Skip string transactions
                elif not isinstance(txn, dict):
                    log.warning(f"  Unexpected transaction format: {type(txn)}")
                    continue

                all_transactions.append(
                    {
                        "account_id": account_id,
                        "transaction_id": txn.get("transactionId", txn.get("id", "")),
                        "transaction_date": txn.get(
                            "transactionDate", txn.get("date", "")
                        ),
                        "description": txn.get("description", ""),
                        "debit": parse_money(txn.get("debit", "0")),
                        "credit": parse_money(txn.get("credit", "0")),
                        "amount": parse_money(txn.get("amount", "0")),
                        "api_source": API_SOURCE_TRANSACTIONS_POST.replace(
                            "{accountNo}", str(account_id)
                        ),
                    }
                )

        except APIAuthenticationError:
            # Don't continue if auth fails - re-raise to stop processing
            log.error(
                f"  Authentication error retrieving transactions for account {account_id}"
            )
            raise
        except (APIError, MaxRetriesExceededError) as e:
            log.warning(
                f"  ⚠ Failed to retrieve transactions for account {account_id}: {e}"
            )

    df_transactions = pd.DataFrame(all_transactions)
    log.info(
        f"  Step C completed: {len(df_transactions)} total transactions retrieved from API"
    )
    return df_transactions


def _perform_reconciliation(
    api_accounts: pd.DataFrame,
    api_transactions: pd.DataFrame,
    web_accounts: pd.DataFrame | None,
    web_transactions: pd.DataFrame | None,
) -> Dict[str, pd.DataFrame]:
    """
    Task 6.3: Cross-Validation - Compare API data with web-scraped data.

    Args:
        api_accounts: Accounts retrieved from API
        api_transactions: Transactions retrieved from API
        web_accounts: Accounts scraped from web (Part 2)
        web_transactions: Transactions scraped from web (Part 3)

    Returns:
        Dictionary of DataFrames for different sections of the reconciliation report
    """
    log.info("  Performing cross-validation...")

    report = {}

    # Section 1: API Authentication Status
    report["authentication"] = pd.DataFrame(
        [
            {
                "Status": "Success",
                "Username": settings.api_user,
                "API Base URL": settings.base_url,
                "Token Obtained": "Yes",
                "Date Range": f"{settings.api_filter_start} to {settings.api_filter_end}",
            }
        ]
    )

    # Section 2: Account Reconciliation
    if web_accounts is not None and not web_accounts.empty:
        report["account_recon"] = _reconcile_accounts(api_accounts, web_accounts)
    else:
        log.warning("  No web account data provided - skipping account reconciliation")
        report["account_recon"] = api_accounts.copy()
        report["account_recon"]["web_match_status"] = "No web data for comparison"

    # Section 3: Transaction Reconciliation by Account
    if web_transactions is not None and not web_transactions.empty:
        report["transaction_recon"] = _reconcile_transactions(
            api_transactions, web_transactions
        )
    else:
        log.warning(
            "  No web transaction data provided - skipping transaction reconciliation"
        )
        # Create summary from API data only
        report["transaction_recon"] = _summarize_api_transactions(api_transactions)

    # Section 4: Variance Summary
    report["variance_summary"] = _create_variance_summary(
        report, api_accounts, api_transactions, web_accounts, web_transactions
    )

    log.info("  Cross-validation completed")
    return report


def _reconcile_accounts(api_df: pd.DataFrame, web_df: pd.DataFrame) -> pd.DataFrame:
    """Compare API account data with web-scraped account data."""
    log.info("    Reconciling account data...")

    # Normalize API data
    api_normalized = api_df.copy()
    api_normalized["account_id"] = api_normalized["account_id"].astype(str)

    # Normalize web data - handle different possible column name formats
    mapping_rules = [
        (["account", "id"], "account_id"),
        (["account", "number"], "account_id"),
        (["total", "balance"], "total"),
        (["available", "balance"], "available"),
    ]
    web_normalized = normalize_column_names(web_df, mapping_rules)

    # Ensure account_id is string type
    if "account_id" in web_normalized.columns:
        web_normalized["account_id"] = web_normalized["account_id"].astype(str)
    else:
        log.warning("    Web data missing account_id column after normalization")
        # Return API data only with a note
        api_normalized["web_match_status"] = "No web data for comparison"
        return api_normalized

    # Merge API and Web data
    merged = pd.merge(
        api_normalized[["account_id", "account_name", "balance", "available_balance"]],
        web_normalized[["account_id", "total", "available"]],
        on="account_id",
        how="outer",
        suffixes=("_api", "_web"),
    )

    # Rename web columns for clarity
    merged = merged.rename(
        columns={"total": "balance_web", "available": "available_balance_web"}
    )

    # Calculate variances
    merged = calculate_variance(
        merged, "balance", "balance_web", result_col="balance_variance"
    )
    merged = calculate_variance(
        merged,
        "available_balance",
        "available_balance_web",
        result_col="available_variance",
    )

    # Determine match status
    merged = add_match_status(merged, "balance_variance", tolerance=VARIANCE_TOLERANCE)

    log.info(f"    Reconciled {len(merged)} accounts")
    return merged


def _reconcile_transactions(api_df: pd.DataFrame, web_df: pd.DataFrame) -> pd.DataFrame:
    """Compare API transaction data with web-scraped transaction data."""
    log.info("    Reconciling transaction data...")

    # Normalize web transaction column names if needed
    # First, try exact display name mappings (from transaction.py Excel output)
    display_to_programmatic = {
        "Transaction ID": "transaction_id",
        "Transaction Time": "transaction_time",
        "Account ID": "account_id",
        "Action": "action",
        "Debit": "debit",
        "Credit": "credit",
    }
    web_normalized = web_df.rename(
        columns={
            col: display_to_programmatic[col]
            for col in web_df.columns
            if col in display_to_programmatic
        }
    )

    # Fallback: fuzzy matching for any columns not caught by exact mapping
    fuzzy_rules = [
        (["account", "id"], "account_id"),
        (["account", "number"], "account_id"),
        (["transaction", "id"], "transaction_id"),
    ]
    web_normalized = normalize_column_names(web_normalized, fuzzy_rules)
    # Ensure account_id is string type in both DataFrames for consistent merging
    if "account_id" in api_df.columns:
        api_df = api_df.copy()
        api_df["account_id"] = api_df["account_id"].astype(str)
    if "account_id" in web_normalized.columns:
        web_normalized = web_normalized.copy()
        web_normalized["account_id"] = web_normalized["account_id"].astype(str)

    # Handle empty DataFrames
    if api_df.empty:
        log.warning("    API transactions DataFrame is empty - no data to reconcile")
        if not web_normalized.empty:
            # Try to summarize web data, but return simple message if it fails
            try:
                return _summarize_api_transactions(web_normalized).assign(
                    data_source="Web Only (API Empty)"
                )
            except Exception as e:
                log.warning(f"    Could not summarize web transactions: {e}")
                return pd.DataFrame(
                    [
                        {
                            "Status": "API Empty - Web Data Available",
                            "API_Transactions": 0,
                            "Web_Transactions": len(web_normalized),
                            "Note": "Cannot reconcile - API returned no transactions",
                        }
                    ]
                )
        else:
            return pd.DataFrame(
                [{"Status": "No transaction data available from API or Web"}]
            )

    if web_normalized.empty:
        log.warning("    Web transactions DataFrame is empty - returning API-only data")
        try:
            return _summarize_api_transactions(api_df).assign(
                data_source="API Only (Web Empty)"
            )
        except Exception as e:
            log.warning(f"    Could not summarize API transactions: {e}")
            return pd.DataFrame(
                [
                    {
                        "Status": "Web Empty - API Data Available",
                        "API_Transactions": len(api_df),
                        "Web_Transactions": 0,
                        "Note": "Cannot reconcile - Web returned no transactions",
                    }
                ]
            )

    # Verify required columns exist
    if "account_id" not in api_df.columns:
        log.error("    API transactions missing 'account_id' column")
        log.error(f"    Available columns: {list(api_df.columns)}")
        return pd.DataFrame(
            [
                {
                    "Status": "Error: API data malformed",
                    "Details": "Missing account_id column",
                }
            ]
        )

    if "account_id" not in web_normalized.columns:
        log.error(
            "    Web transactions missing 'account_id' column after normalization"
        )
        log.error(f"    Available columns: {list(web_normalized.columns)}")
        return pd.DataFrame(
            [
                {
                    "Status": "Error: Web data malformed",
                    "Details": "Missing account_id column",
                }
            ]
        )

    # Group by account and calculate sums (with error handling)
    try:
        api_summary = group_and_sum_by_account(api_df, sum_cols=["debit", "credit"])
        api_summary = api_summary.rename(
            columns={
                "debit": "api_total_debits",
                "credit": "api_total_credits",
                "transaction_count": "api_txn_count",
            }
        )
    except Exception as e:
        log.error(f"    Failed to group API transactions: {e}")
        return pd.DataFrame(
            [{"Status": "Error grouping API transactions", "Error": str(e)}]
        )

    try:
        web_summary = group_and_sum_by_account(
            web_normalized, sum_cols=["debit", "credit"]
        )
        web_summary = web_summary.rename(
            columns={
                "debit": "web_total_debits",
                "credit": "web_total_credits",
                "transaction_count": "web_txn_count",
            }
        )
    except Exception as e:
        log.error(f"    Failed to group web transactions: {e}")
        return pd.DataFrame(
            [{"Status": "Error grouping web transactions", "Error": str(e)}]
        )

    # Merge summaries
    merged = pd.merge(api_summary, web_summary, on="account_id", how="outer")

    # Calculate variances
    merged = calculate_variance(
        merged, "api_total_debits", "web_total_debits", result_col="debit_variance"
    )
    merged = calculate_variance(
        merged, "api_total_credits", "web_total_credits", result_col="credit_variance"
    )
    merged = calculate_variance(
        merged, "api_txn_count", "web_txn_count", result_col="txn_count_variance"
    )

    # Calculate net amounts
    merged["api_net"] = merged["api_total_credits"] - merged["api_total_debits"]
    merged["web_net"] = merged["web_total_credits"] - merged["web_total_debits"]
    merged = calculate_variance(merged, "api_net", "web_net", result_col="net_variance")

    # Determine match status
    merged = add_match_status(merged, "net_variance", tolerance=VARIANCE_TOLERANCE)

    log.info(f"    Reconciled transactions for {len(merged)} accounts")
    return merged


def _summarize_api_transactions(api_df: pd.DataFrame) -> pd.DataFrame:
    """Create transaction summary from transaction data (API or Web)."""
    if api_df.empty:
        return pd.DataFrame()

    # Check if required columns exist
    required_cols = ["account_id", "debit", "credit", "transaction_id"]
    missing_cols = [col for col in required_cols if col not in api_df.columns]

    if missing_cols:
        log.warning(f"    Missing columns for transaction summary: {missing_cols}")
        log.warning(f"    Available columns: {list(api_df.columns)}")
        return pd.DataFrame(
            [
                {
                    "Status": "Cannot summarize transactions",
                    "Missing_Columns": ", ".join(missing_cols),
                    "Available_Columns": ", ".join(api_df.columns),
                }
            ]
        )

    try:
        summary = group_and_sum_by_account(api_df, sum_cols=["debit", "credit"])
        summary = summary.rename(
            columns={"debit": "total_debits", "credit": "total_credits"}
        )
        summary = calculate_net_amount(
            summary, credit_col="total_credits", debit_col="total_debits"
        )
        summary["data_source"] = "Transaction Summary"

        return summary
    except Exception as e:
        log.error(f"    Failed to summarize transactions: {e}")
        return pd.DataFrame(
            [{"Status": "Error summarizing transactions", "Error": str(e)}]
        )


def _create_variance_summary(
    report: Dict[str, pd.DataFrame],
    api_accounts: pd.DataFrame,
    api_transactions: pd.DataFrame,
    web_accounts: pd.DataFrame | None,
    web_transactions: pd.DataFrame | None,
) -> pd.DataFrame:
    """Create overall variance summary statistics."""

    summary_rows = []

    # API Data Summary
    summary_rows.append(
        {
            "Metric": "API Accounts Retrieved",
            "Count": len(api_accounts),
            "Details": f"From {API_SOURCE_ACCOUNT_LIST}",
        }
    )

    summary_rows.append(
        {
            "Metric": "API Transactions Retrieved",
            "Count": len(api_transactions),
            "Details": f"Date range: {settings.api_filter_start} to {settings.api_filter_end}",
        }
    )

    # Web Data Summary
    if web_accounts is not None:
        summary_rows.append(
            {
                "Metric": "Web Accounts Scraped",
                "Count": len(web_accounts),
                "Details": "From Part 2",
            }
        )

    if web_transactions is not None:
        summary_rows.append(
            {
                "Metric": "Web Transactions Scraped",
                "Count": len(web_transactions),
                "Details": "From Part 3",
            }
        )

    # Reconciliation Summary
    if "account_recon" in report:
        account_recon = report["account_recon"]
        # Only calculate matches/variances if match_status column exists (i.e., web data was available)
        if "match_status" in account_recon.columns:
            matches = len(account_recon[account_recon["match_status"] == "Match"])
            variances = len(
                account_recon[
                    account_recon["match_status"].str.contains("Variance", na=False)
                ]
            )

            summary_rows.append(
                {
                    "Metric": "Account Matches",
                    "Count": matches,
                    "Details": "Accounts with matching balances",
                }
            )

            summary_rows.append(
                {
                    "Metric": "Account Variances",
                    "Count": variances,
                    "Details": "Accounts with balance differences",
                }
            )

    if "transaction_recon" in report:
        txn_recon = report["transaction_recon"]
        # Only calculate matches/variances if match_status column exists (i.e., web data was available)
        if "match_status" in txn_recon.columns:
            txn_matches = len(txn_recon[txn_recon["match_status"] == "Match"])
            txn_variances = len(
                txn_recon[txn_recon["match_status"].str.contains("Variance", na=False)]
            )

            summary_rows.append(
                {
                    "Metric": "Transaction Matches (by account)",
                    "Count": txn_matches,
                    "Details": "Accounts with matching transaction totals",
                }
            )

            summary_rows.append(
                {
                    "Metric": "Transaction Variances (by account)",
                    "Count": txn_variances,
                    "Details": "Accounts with transaction differences",
                }
            )

    return pd.DataFrame(summary_rows)


def _write_excel_report(report: Dict[str, pd.DataFrame]):
    """Write the comprehensive reconciliation report to Excel."""
    log.info(f"  Writing {SHEET_API_VALIDATION} sheet to Excel...")

    # Open existing Excel file and add new sheet
    xw = ExcelWriter(settings.excel_path)

    # Create combined report with clear sections
    combined_sections = []

    # Section 1: Authentication Status
    if "authentication" in report:
        combined_sections.append(
            pd.DataFrame([{"SECTION": "1. API AUTHENTICATION STATUS"}])
        )
        combined_sections.append(report["authentication"])
        combined_sections.append(pd.DataFrame([{"": ""}]))  # Blank row

    # Section 2: Variance Summary
    if "variance_summary" in report:
        combined_sections.append(
            pd.DataFrame([{"SECTION": "2. RECONCILIATION SUMMARY"}])
        )
        combined_sections.append(report["variance_summary"])
        combined_sections.append(pd.DataFrame([{"": ""}]))

    # Section 3: Account Reconciliation
    if "account_recon" in report and not report["account_recon"].empty:
        combined_sections.append(
            pd.DataFrame([{"SECTION": "3. ACCOUNT RECONCILIATION (API vs Web)"}])
        )
        combined_sections.append(report["account_recon"])
        combined_sections.append(pd.DataFrame([{"": ""}]))

    # Section 4: Transaction Reconciliation
    if "transaction_recon" in report and not report["transaction_recon"].empty:
        combined_sections.append(
            pd.DataFrame(
                [{"SECTION": "4. TRANSACTION RECONCILIATION BY ACCOUNT (API vs Web)"}]
            )
        )
        combined_sections.append(report["transaction_recon"])
        combined_sections.append(pd.DataFrame([{"": ""}]))

    # Combine all sections
    if combined_sections:
        final_df = pd.concat(combined_sections, ignore_index=True)
        xw.write_df(SHEET_API_VALIDATION, final_df)
    else:
        # Fallback: write empty report
        xw.write_df(
            SHEET_API_VALIDATION, pd.DataFrame([{"Status": "No data available"}])
        )

    xw.close()
    log.info(f"  {SHEET_API_VALIDATION} sheet written to {settings.excel_path}")


def _write_api_unavailable_report():
    """Write a report indicating API is unavailable."""
    log.info("  Writing API unavailable report to Excel...")

    df = pd.DataFrame(
        [
            {
                "Status": "API Unavailable",
                "Message": "Could not authenticate with AltoroMutual REST API",
                "Attempted Endpoint": f"{settings.base_url}/api/login",
                "Username": settings.api_user,
                "Note": "Part 6 skipped - API service may be down or credentials invalid",
            }
        ]
    )

    try:
        xw = ExcelWriter(settings.excel_path)
        xw.write_df(SHEET_API_VALIDATION, df)
        xw.close()
        log.info(f"  API unavailable report written to {settings.excel_path}")
    except Exception as e:
        log.error(f"  Failed to write report: {e}")
