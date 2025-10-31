"""Utility functions for parsing and data conversion."""

import re
import datetime


def parse_money(amount_str: str) -> float:
    """
    Parse a monetary string into a float value.

    Handles various formats:
    - Negative amounts in parentheses: ($1,234.56) → -1234.56
    - Negative amounts with minus sign: -$1,234.56 → -1234.56
    - Positive amounts: $1,234.56 → 1234.56
    - Removes currency symbols and thousands separators

    Args:
        amount_str: String representation of money (e.g., "$1,234.56" or "($100.00)")

    Returns:
        Float value of the amount, negative if in parentheses or prefixed with minus

    Example:
        >>> parse_money("$1,234.56")
        1234.56
        >>> parse_money("($100.00)")
        -100.0
    """
    if not amount_str:
        return 0.0

    amount_str = amount_str.strip()

    # Check if negative (accounting format with parentheses)
    is_negative = amount_str.startswith("(") and amount_str.endswith(")")

    # Remove all non-numeric characters except decimal point and minus sign
    numeric_only = re.sub(r"[^0-9.\-]", "", amount_str)

    # Convert to float, handle empty string
    amount = float(numeric_only) if numeric_only else 0.0

    return -amount if is_negative else amount


def parse_date(date_str: str, date_format: str = "%m/%d/%Y") -> datetime.date:
    """
    Parse a date string into a datetime.date object.

    Args:
        date_str: String representation of date
        date_format: Format string for strptime (default: MM/DD/YYYY)

    Returns:
        datetime.date object

    Raises:
        ValueError: If date_str doesn't match date_format

    Example:
        >>> parse_date("12/31/2024")
        datetime.date(2024, 12, 31)
    """
    return datetime.datetime.strptime(date_str.strip(), date_format).date()


def clean_account_name(account_name: str) -> str:
    """
    Extract the descriptive part of an account name, removing the account number prefix.

    Handles formats like:
    - "800002 Savings" → "Savings"
    - "800003 Checking" → "Checking"
    - "4539082039396288 Credit Card" → "Credit Card"

    Args:
        account_name: Full account name with number prefix

    Returns:
        Cleaned account name with only the descriptive part

    Example:
        >>> clean_account_name("800002 Savings")
        "Savings"
        >>> clean_account_name("800003 Checking")
        "Checking"
    """
    if not account_name:
        return ""

    parts = account_name.strip().split(maxsplit=1)

    if len(parts) > 1:
        return parts[1]

    return account_name
