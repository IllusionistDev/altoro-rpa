"""Application-wide constants for AltoroMutual RPA project.

This module centralizes all magic numbers, hard-coded strings, and configuration
constants used throughout the application for easy maintenance and consistency.
"""

# Excel Sheet Names

SHEET_ACCOUNT_SUMMARY = "Account_Summary"
"""Sheet name for account summary data (Part 2)"""

SHEET_TRANSACTIONS_PREFIX = "Transactions_"
"""Prefix for per-account transaction sheets (Part 2)"""

SHEET_FILTERED_TRANSACTIONS = "Filtered_Transactions"
"""Sheet name for date-filtered transactions (Part 3)"""

SHEET_HIGH_VALUE_CREDITS = "High_Value_Credits"
"""Sheet name for high-value credit transactions (Part 3)"""

SHEET_TRANSFER_DETAILS = "Transfer_Details"
"""Sheet name for transfer confirmation and verification (Part 4)"""

SHEET_PRODUCT_CATALOG = "Product_Catalog"
"""Sheet name for product catalog data (Part 5)"""

SHEET_API_VALIDATION = "API_Data_Validation"
"""Sheet name for API vs web data reconciliation (Part 6)"""

HIGH_VALUE_CREDIT_THRESHOLD = 150.0
"""Minimum credit amount (in dollars) to be classified as high-value"""

VARIANCE_TOLERANCE = 0.01
"""Acceptable variance (in dollars) when comparing API vs web data"""


TRANSACTION_DISPLAY_COLUMNS = [
    "Transaction ID",
    "Transaction Time",
    "Account ID",
    "Action",
    "Debit",
    "Credit",
]
"""Standard column order for transaction sheets"""

ACCOUNT_SUMMARY_COLUMNS = [
    "Account ID/Number",
    "Account Name/Type",
    "Total Balance",
    "Available Balance",
]
"""Standard column order for account summary sheet"""

API_SOURCE_ACCOUNT_LIST = "GET /api/account"
"""API source identifier for account list endpoint"""

API_SOURCE_ACCOUNT_DETAILS = "GET /api/account/{accountNo}"
"""API source identifier for account details endpoint"""

API_SOURCE_TRANSACTIONS_POST = "POST /api/account/{accountNo}/transactions"
"""API source identifier for date-filtered transactions endpoint"""

# Session Management

DEFAULT_MAX_RETRIES = 2
"""Default maximum retry attempts for session recovery"""

SESSION_ERROR_KEYWORDS = [
    "target closed",
    "session",
    "timeout",
    "navigation",
    "detached",
    "not found",
]
"""Keywords in error messages that indicate a session/timeout issue"""


# HTML Selectors
# Note: These are kept as reference. Actual selectors are in page classes
# following Page Object Model pattern.

SELECTOR_ACCOUNT_DROPDOWN = "#listAccounts"
"""Selector for account dropdown (reference)"""

SELECTOR_GET_ACCOUNT_BUTTON = "#btnGetAccount"
"""Selector for get account button (reference)"""

SELECTOR_TRANSACTIONS_TABLE = "#_ctl0__ctl0_Content_Main_MyTransactions"
"""Selector for transactions table (reference)"""
