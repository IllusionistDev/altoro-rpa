"""Common DataFrame manipulation utilities for data transformation and analysis.

This module provides reusable DataFrame operations used across orchestration files,
including column normalization, aggregation, and summary calculations.
"""

from typing import List, Tuple
import pandas as pd

from src.core.logger import log
from src.core.constants import VARIANCE_TOLERANCE


def normalize_column_names(
    df: pd.DataFrame, mapping_rules: List[Tuple[List[str], str]]
) -> pd.DataFrame:
    """
    Normalize DataFrame column names based on keyword matching rules.

    Searches column names for keywords and renames them to standardized names.
    Useful for reconciling data from different sources with inconsistent naming.

    Args:
        df: DataFrame to normalize
        mapping_rules: List of (keywords, target_name) tuples.
            Each tuple contains a list of keywords that must ALL be present
            in the column name (case-insensitive) and the target column name.

    Returns:
        DataFrame with normalized column names

    Example:
        >>> rules = [
        ...     (["account", "id"], "account_id"),
        ...     (["total", "balance"], "total_balance")
        ... ]
        >>> df = normalize_column_names(df, rules)
        # "Account ID/Number" → "account_id"
        # "Total Balance" → "total_balance"
    """
    column_mapping = {}

    for col in df.columns:
        col_lower = col.lower()
        for keywords, target_name in mapping_rules:
            # Check if ALL keywords are present in column name
            if all(keyword in col_lower for keyword in keywords):
                column_mapping[col] = target_name
                break  # Use first matching rule

    if column_mapping:
        df = df.rename(columns=column_mapping)
        log.info(f"    Normalized columns: {column_mapping}")

    return df


def calculate_net_amount(
    df: pd.DataFrame,
    credit_col: str = "credit",
    debit_col: str = "debit",
    result_col: str = "net_amount",
) -> pd.DataFrame:
    """
    Calculate net amount (credits - debits) and add as new column.

    Args:
        df: DataFrame with credit and debit columns
        credit_col: Name of credit column (default: "credit")
        debit_col: Name of debit column (default: "debit")
        result_col: Name for result column (default: "net_amount")

    Returns:
        DataFrame with net_amount column added

    Example:
        >>> df = calculate_net_amount(transactions_df)
        # Adds column: net_amount = credit - debit
    """
    df = df.copy()
    df[result_col] = df[credit_col] - df[debit_col]
    return df


def group_and_sum_by_account(
    df: pd.DataFrame,
    group_col: str = "account_id",
    sum_cols: List[str] = None,
    count_col: str = "transaction_id",
) -> pd.DataFrame:
    """
    Group transactions by account and calculate sums.

    Aggregates transaction data by account, summing specified columns
    and counting transactions.

    Args:
        df: Transactions DataFrame
        group_col: Column to group by (default: "account_id")
        sum_cols: Columns to sum (default: ["debit", "credit"])
        count_col: Column to count for transaction count (default: "transaction_id")

    Returns:
        Grouped DataFrame with totals and transaction count

    Example:
        >>> summary = group_and_sum_by_account(
        ...     transactions_df,
        ...     sum_cols=["debit", "credit"]
        ... )
        # Returns: account_id, debit (sum), credit (sum), transaction_count
    """
    if sum_cols is None:
        sum_cols = ["debit", "credit"]

    # Build aggregation dictionary
    agg_dict = {col: "sum" for col in sum_cols}
    agg_dict[count_col] = "count"

    result = df.groupby(group_col).agg(agg_dict).reset_index()

    # Rename count column to transaction_count
    col_names = list(result.columns)
    for i, col in enumerate(col_names):
        if col == count_col:
            col_names[i] = "transaction_count"
    result.columns = col_names

    return result


def calculate_variance(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    result_col: str = "variance",
    tolerance: float = 0.0,
) -> pd.DataFrame:
    """
    Calculate variance between two columns.

    Computes col1 - col2 for each row, handling None/NaN values gracefully.

    Args:
        df: Source DataFrame
        col1: First column name
        col2: Second column name
        result_col: Name for variance column (default: "variance")
        tolerance: Not used currently, reserved for future threshold flagging

    Returns:
        DataFrame with variance column added

    Example:
        >>> df = calculate_variance(
        ...     reconciliation_df,
        ...     "api_balance",
        ...     "web_balance",
        ...     result_col="balance_variance"
        ... )
    """
    df = df.copy()

    df[result_col] = df.apply(
        lambda row: (
            row.get(col1, 0) - row.get(col2, 0)
            if pd.notna(row.get(col1)) and pd.notna(row.get(col2))
            else None
        ),
        axis=1,
    )

    return df


def add_match_status(
    df: pd.DataFrame,
    variance_col: str,
    status_col: str = "match_status",
    tolerance: float = VARIANCE_TOLERANCE,
    match_label: str = "Match",
    variance_label: str = "Variance",
    missing_label: str = "Data Missing",
) -> pd.DataFrame:
    """
    Add match status based on variance column.

    Categorizes each row as matching, having variance, or missing data
    based on the variance value and tolerance threshold.

    Args:
        df: DataFrame with variance column
        variance_col: Name of variance column
        status_col: Name for status column (default: "match_status")
        tolerance: Acceptable variance threshold (default: 0.01)
        match_label: Label for matching rows (default: "Match")
        variance_label: Label for rows with variance (default: "Variance")
        missing_label: Label for rows with missing data (default: "Data Missing")

    Returns:
        DataFrame with status column added

    Example:
        >>> df = add_match_status(
        ...     df,
        ...     "balance_variance",
        ...     tolerance=0.01
        ... )
    """
    df = df.copy()

    def determine_status(variance):
        if variance is None or pd.isna(variance):
            return missing_label
        elif abs(variance) < tolerance:
            return match_label
        else:
            return variance_label

    df[status_col] = df[variance_col].apply(determine_status)

    return df
