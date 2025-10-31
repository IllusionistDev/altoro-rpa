"""API endpoint constants for AltoroMutual REST API.

Centralized endpoint definitions matching the Swagger specification.
"""

# Authentication
API_LOGIN = "/api/login"
"""
POST /api/login
Authenticate and obtain Bearer token.

Request body:
    {
        "username": "admin",
        "password": "admin"
    }

Response:
    {
        "Authorization": "Bearer TOKEN_VALUE"
    }
"""

# Account endpoints
API_ACCOUNTS = "/api/account"
"""
GET /api/account
Retrieve list of all accounts for authenticated user.

Response:
    {
        "Accounts": [
            {
                "Name": "800002 Savings",
                "id": "800002"
            },
            ...
        ]
    }
"""

API_ACCOUNT_DETAILS = "/api/account/{accountNo}"
"""
GET /api/account/{accountNo}
Retrieve detailed information for a specific account.

Path parameters:
    accountNo: Account number (e.g., "800002")

Response:
    {
        "accountId": "800002",
        "accountName": "800002 Savings",
        "accountType": "Savings",
        "balance": "$15,000.00",
        "availableBalance": "$15,000.00"
    }
"""

# Transaction endpoints
API_TRANSACTIONS_GET = "/api/account/{accountNo}/transactions"
"""
GET /api/account/{accountNo}/transactions
Retrieve last 10 transactions for an account.

Path parameters:
    accountNo: Account number (e.g., "800002")

Response:
    {
        "lastTenTransactions": [
            {
                "transactionId": "...",
                "date": "...",
                "description": "...",
                "debit": "...",
                "credit": "..."
            },
            ...
        ]
    }
"""

API_TRANSACTIONS_POST = "/api/account/{accountNo}/transactions"
"""
POST /api/account/{accountNo}/transactions
Retrieve date-filtered transactions for an account.

Path parameters:
    accountNo: Account number (e.g., "800002")

Request body:
    {
        "startDate": "2025-02-01",
        "endDate": "2025-04-15"
    }

Response:
    {
        "transactions": [
            {
                "transactionId": "...",
                "date": "...",
                "description": "...",
                "debit": "...",
                "credit": "..."
            },
            ...
        ]
    }
"""
