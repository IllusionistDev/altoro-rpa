"""Altoro Mutual API client with robust error handling and automatic retry.

This module provides a production-ready API client with:
- Automatic token refresh on expiration
- Connection pooling for performance
- Exponential backoff retry on transient failures
- Comprehensive error handling with custom exceptions
- Structured logging for debugging
"""

import httpx
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from src.api.retry_handler import with_api_retry
from src.api.exceptions import APIAuthenticationError
from src.core.logger import log


# Token expiration buffer - refresh token this many seconds before it expires
TOKEN_REFRESH_BUFFER = 300  # 5 minutes


class Token(BaseModel):
    """API authentication token with expiration tracking."""

    value: str
    exp: float


class AltoroAPI:
    """
    Altoro Mutual REST API client with automatic retry and token management.

    Features:
    - Connection pooling via persistent httpx.Client
    - Automatic token refresh before expiration
    - Exponential backoff retry on transient failures (500, 503, timeouts)
    - Custom exception hierarchy for precise error handling
    - Context manager support for proper resource cleanup

    Usage:
        with AltoroAPI(base_url, username, password) as api:
            api.authenticate()
            accounts = api.accounts()
            transactions = api.transactions(account_id, start_date, end_date)
    """

    def __init__(self, base_url: str, user: str, pwd: str, timeout: float = 20.0):
        """
        Initialize API client with credentials and connection settings.

        Args:
            base_url: Base URL of the Altoro Mutual API
            user: API username
            pwd: API password
            timeout: Request timeout in seconds (default: 20.0)
        """
        self.base = base_url.rstrip("/")
        self.user = user
        self.pwd = pwd
        self.timeout = timeout
        self._tok: Optional[Token] = None
        self._client: Optional[httpx.Client] = None

    def __enter__(self):
        """Context manager entry - create persistent HTTP client."""
        self._client = httpx.Client(timeout=self.timeout)
        log.debug(f"API client initialized for {self.base}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client and cleanup resources."""
        if self._client:
            self._client.close()
            log.debug("API client connection closed")
        self._client = None
        return False

    def _get_client(self) -> httpx.Client:
        """
        Get the HTTP client, creating one if needed.

        Returns:
            httpx.Client instance

        Note:
            If not using context manager, creates a client on-demand.
            Recommended to use context manager for connection pooling.
        """
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _headers(self) -> Dict[str, str]:
        """
        Get HTTP headers including authorization token.

        Returns:
            Dictionary of HTTP headers

        Note:
            Returns empty dict if no token available.
        """
        if self._tok:
            return {"Authorization": f"{self._tok.value}"}
        return {}

    def _is_token_expired(self) -> bool:
        """
        Check if the current token is expired or about to expire.

        Returns:
            True if token is None, expired, or within refresh buffer

        Note:
            Uses TOKEN_REFRESH_BUFFER to proactively refresh before expiration.
        """
        if not self._tok:
            return True

        time_until_expiry = self._tok.exp - time.time()
        return time_until_expiry < TOKEN_REFRESH_BUFFER

    def _ensure_valid_token(self):
        """
        Ensure a valid authentication token exists, refreshing if needed.

        Raises:
            APIAuthenticationError: If authentication fails
        """
        if self._is_token_expired():
            log.debug("Token expired or missing, re-authenticating...")
            self.authenticate()

    @with_api_retry(max_retries=2, backoff_factor=2.0)
    def authenticate(self):
        """
        Authenticate with the AltoroMutual API and obtain Bearer token.

        Automatically retries on transient failures (network errors, 5xx responses).
        Does NOT retry on authentication failures (401, 403).

        Raises:
            APIAuthenticationError: If credentials are invalid
            MaxRetriesExceededError: If retry attempts exhausted
            APIConnectionError: If connection fails after retries

        Note:
            Token is valid for 3600 seconds (1 hour).
            Automatically refreshed when needed by _ensure_valid_token().
        """
        client = self._get_client()

        try:
            log.info(f"Authenticating to {self.base}/api/login as {self.user}...")
            r = client.post(
                f"{self.base}/api/login",
                json={"username": self.user, "password": self.pwd},
            )
            r.raise_for_status()

            # API returns "Authorization: Bearer TOKEN" in response
            auth_header = r.json().get("Authorization", "")
            if not auth_header:
                raise APIAuthenticationError(
                    "No Authorization header in login response"
                )

            token_value = (
                auth_header.replace("Bearer ", "")
                if auth_header.startswith("Bearer ")
                else auth_header
            )
            self._tok = Token(value=token_value, exp=time.time() + 3600)

            log.info("Authentication successful (token expires in 1 hour)")

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                log.error(
                    f"Authentication failed: Invalid credentials for user {self.user}"
                )
                raise APIAuthenticationError(
                    f"Invalid credentials for user {self.user}",
                    status_code=e.response.status_code,
                    response_body=e.response.text[:500],
                ) from e
            # Let retry decorator handle other status codes
            raise

    @with_api_retry(max_retries=3, backoff_factor=2.0)
    def accounts(self) -> List[Dict[str, Any]]:
        """
        Retrieve all accounts for the authenticated user.

        Automatically:
        - Checks and refreshes token if needed
        - Retries on transient failures (500, 503, timeouts)
        - Logs request details for debugging

        Returns:
            List of account dictionaries from the API response.
            API returns: {"Accounts": [{"Name": "...", "id": "..."}, ...]}
            This method extracts and returns the accounts array.

        Raises:
            APIAuthenticationError: If authentication token is invalid
            MaxRetriesExceededError: If retry attempts exhausted
            APIConnectionError: If connection fails after retries

        Example:
            accounts = api.accounts()
            # [{"Name": "Savings", "id": "800002"}, ...]
        """
        self._ensure_valid_token()
        client = self._get_client()

        log.debug(f"Fetching accounts from {self.base}/api/account")
        r = client.get(f"{self.base}/api/account", headers=self._headers())
        r.raise_for_status()

        response = r.json()
        accounts_list = response.get("Accounts", [])
        log.info(f"Retrieved {len(accounts_list)} accounts from API")
        return accounts_list

    @with_api_retry(max_retries=3, backoff_factor=2.0)
    def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information for a specific account.

        Automatically:
        - Checks and refreshes token if needed
        - Retries on transient failures (500, 503, timeouts)
        - Logs request details for debugging

        Args:
            account_id: Account number/identifier

        Returns:
            Dictionary with account details including balance, type, etc.

        Raises:
            APIAuthenticationError: If authentication token is invalid
            APIError: If account not found (404) or other client error
            MaxRetriesExceededError: If retry attempts exhausted
            APIConnectionError: If connection fails after retries

        Example:
            details = api.get_account_details("800002")
            # {"accountName": "Savings", "balance": "1000.00", ...}
        """
        self._ensure_valid_token()
        client = self._get_client()

        log.debug(f"Fetching account details for {account_id}")
        r = client.get(f"{self.base}/api/account/{account_id}", headers=self._headers())
        r.raise_for_status()

        details = r.json()
        log.debug(f"Retrieved details for account {account_id}")

        return details

    @with_api_retry(max_retries=3, backoff_factor=2.0)
    def transactions(
        self, account_id: str, start: Optional[str] = None, end: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve transactions for a specific account.

        Automatically:
        - Checks and refreshes token if needed
        - Retries on transient failures (500, 503, timeouts)
        - Logs request details for debugging

        Args:
            account_id: Account number
            start: Start date in YYYY-MM-DD format (optional)
            end: End date in YYYY-MM-DD format (optional)

        Returns:
            List of transaction dictionaries.
            - With dates: Returns all transactions in date range (via POST)
            - Without dates: Returns last 10 transactions (via GET)
            API returns: {"transactions": [...]} or {"lastTenTransactions": [...]}
            This method extracts and returns the transaction array.

        Raises:
            APIAuthenticationError: If authentication token is invalid
            APIError: If account not found (404) or other client error
            MaxRetriesExceededError: If retry attempts exhausted
            APIConnectionError: If connection fails after retries

        Example:
            # Last 10 transactions
            txns = api.transactions("800002")

            # Date-filtered transactions
            txns = api.transactions("800002", "2025-01-01", "2025-03-31")
        """
        self._ensure_valid_token()
        client = self._get_client()

        if start and end:
            # Use POST with date range body for filtered transactions
            log.debug(f"Fetching transactions for {account_id} from {start} to {end}")
            body = {"startDate": start, "endDate": end}
            r = client.post(
                f"{self.base}/api/account/{account_id}/transactions",
                json=body,
                headers=self._headers(),
            )
        else:
            # Use GET for last 10 transactions
            log.debug(f"Fetching last 10 transactions for {account_id}")
            r = client.get(
                f"{self.base}/api/account/{account_id}/transactions",
                headers=self._headers(),
            )

        r.raise_for_status()
        response = r.json()

        # API returns different keys based on endpoint:
        # POST with dates: {"transactions": [...]}
        # GET without dates: {"lastTenTransactions": [...]} or similar
        # Extract the transaction array from the response
        if isinstance(response, dict):
            # Try common keys in order of likelihood
            transactions = (
                response.get("transactions")
                or response.get("lastTenTransactions")
                or response.get("Transactions")
                or []
            )
        elif isinstance(response, list):
            # Already a list, return as-is
            transactions = response
        else:
            transactions = []

        log.info(f"Retrieved {len(transactions)} transactions for account {account_id}")
        return transactions
