# 🏦 Altoro RPA Automation

A production-ready **RPA (Robotic Process Automation)** project built with **Python + Playwright** to automate comprehensive banking workflows on the Altoro Mutual demo banking site.

This project demonstrates:
- 🔹 Advanced browser automation with Playwright and Page Object Model (POM)
- 🔹 Robust error handling with automatic session recovery and retry logic
- 🔹 REST API integration with token management and exponential backoff
- 🔹 Comprehensive data extraction, transformation, and Excel reporting
- 🔹 Type-safe configuration management using Pydantic
- 🔹 Dockerized execution environment for reproducibility
- 🔹 Modular architecture with 6 independent automation workflows

---

## 📑 Table of Contents

- [Features](#-features)
- [Project Architecture](#-project-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#️-configuration)
- [The 6 Automation Parts](#-the-6-automation-parts)
- [Component Documentation](#-component-documentation)
- [Running the Project](#-running-the-project)
- [Output Artifacts](#-output-artifacts)
- [Design Patterns](#-design-patterns)
- [Dependencies](#-dependencies)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🚀 Features

### Complete Banking Workflow Automation

| Part | Task | Output | Key Features |
|------|------|---------|--------------|
| **1** | Login Testing | Screenshots, Logs | Happy path + negative testing, retry logic |
| **2** | Account Summary & Transactions | `Account_Summary` + per-account sheets | Session recovery, multi-account iteration |
| **3** | Transaction Filtering & Analysis | `Filtered_Transactions` + `High_Value_Credits` | Date filters, high-value detection (≥$150) |
| **4** | Fund Transfer with Verification | `Transfer_Details` + confirmation screenshot | Balance verification, assertion-based validation |
| **5** | Product Catalog Extraction | `Product_Catalog` | 12 categories across PERSONAL & BUSINESS |
| **6** | API Validation & Reconciliation | `API_Data_Validation` | Cross-validation of API vs web data |

**Consolidated Output:** Single Excel workbook → `artifacts/outputs/Altoro_Report.xlsx`

### Key Capabilities

- ✅ **Automatic Session Recovery** - Handles timeouts and re-authenticates automatically
- ✅ **API Retry Logic** - Exponential backoff for transient failures (500, timeouts)
- ✅ **Token Management** - Proactive refresh 5 minutes before expiration
- ✅ **Data Reconciliation** - Variance detection between API and web data (0.01 tolerance)
- ✅ **Comprehensive Logging** - Structured logs with Loguru (console + file)
- ✅ **Debugging Support** - Full Playwright traces exportable for inspection
- ✅ **Type Safety** - Pydantic models with validation throughout
- ✅ **Independent Execution** - Each part can run standalone or as pipeline

---

## 🏗️ Project Architecture

### Directory Structure

```
altoro_rpa/
│
├── 📄 Dockerfile                      # Container image definition
├── 📄 docker-compose.yaml             # Docker Compose service config
├── 📄 Makefile                        # Build and run automation
├── 📄 requirements.txt                # Python dependencies
├── 📄 .env.example                    # Example environment config
├── 📄 README.md                       # This file
│
├── 📁 .claude/                        # IDE settings
│   └── settings.local.json
│
├── 📁 artifacts/                      # Runtime outputs (gitignored)
│   ├── logs/                         # Application logs (run.log)
│   ├── screenshots/                  # Error & confirmation screenshots
│   ├── traces/                       # Playwright trace files (trace.zip)
│   └── outputs/                      # Excel reports (Altoro_Report.xlsx)
│
└── 📁 src/                            # Source code
    │
    ├── 📁 core/                       # Core utilities and configuration
    │   ├── auth_helpers.py           # Authentication & session setup
    │   ├── config.py                 # Pydantic settings management
    │   ├── constants.py              # Application-wide constants
    │   ├── dataframe_helpers.py      # DataFrame manipulation utilities
    │   ├── excel_helpers.py          # Single-sheet Excel writer
    │   ├── excel.py                  # Multi-sheet Excel writer with styling
    │   ├── logger.py                 # Loguru logging configuration
    │   ├── session_handler.py        # Session timeout recovery decorator
    │   └── utils.py                  # General utilities (parsing, formatting)
    │
    ├── 📁 web/                        # Browser automation (Playwright)
    │   ├── browser.py                # Browser session context manager
    │   └── pages/                    # Page Object Model (POM)
    │       ├── base_page.py          # Base page with common operations
    │       ├── login_page.py         # Login functionality
    │       ├── accounts_page.py      # Account summary & transactions
    │       ├── transactions_page.py  # Transaction filtering & extraction
    │       ├── transfer_page.py      # Fund transfer operations
    │       └── products_page.py      # Product catalog scraping
    │
    ├── 📁 api/                        # REST API integration
    │   ├── client.py                 # HTTP client with auth & retry
    │   ├── endpoints.py              # API endpoint definitions
    │   ├── exceptions.py             # Custom API exception hierarchy
    │   └── retry_handler.py          # Exponential backoff decorator
    │
    └── 📁 orchestration/              # Task orchestration (Parts 1-6)
        ├── __init__.py               # Package initialization
        ├── run_all.py                # Main entry point (full workflow)
        ├── account_login.py          # Part 1: Login testing
        ├── accounts_summary.py       # Part 2: Account summary extraction
        ├── transaction.py            # Part 3: Transaction filtering
        ├── transfer.py               # Part 4: Fund transfer
        ├── products.py               # Part 5: Product catalog
        └── api_validate.py           # Part 6: API reconciliation
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.10+ for local development

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd altoro_rpa

# Create environment configuration
cp .env.example .env

# Edit .env with your credentials (defaults work for demo site)
nano .env
```

### 2. Build Docker Image

```bash
make build
```

### 3. Run Full Automation

```bash
make up
```

This executes all 6 parts sequentially and generates the complete Excel report.

### 4. View Results

```bash
# Excel report
open artifacts/outputs/Altoro_Report.xlsx

# Logs
cat artifacts/logs/run.log

# Playwright trace (for debugging)
playwright show-trace artifacts/traces/trace.zip
```

---

## ⚙️ Configuration

### Environment Variables

All configuration is managed via `.env` file with `ALTORO_` prefix:

```bash
# Authentication
ALTORO_BASE_URL=https://demo.testfire.net
ALTORO_USER=jsmith
ALTORO_PASSWORD=demo1234
ALTORO_API_USER=admin
ALTORO_API_PASSWORD=admin

# Transaction Filters (YYYY-MM-DD)
ALTORO_FILTER_START=2025-01-01
ALTORO_FILTER_END=2025-09-20
ALTORO_API_FILTER_START=2025-01-01
ALTORO_API_FILTER_END=2025-09-20

# Transfer Scenario (Part 4)
ALTORO_TRANSFER_FROM=800002 Savings
ALTORO_TRANSFER_TO=800003 Checking
ALTORO_TRANSFER_AMOUNT=250.00

# Session Management
ALTORO_MAX_SESSION_RETRIES=2
ALTORO_ENABLE_SESSION_MONITORING=true

# Optional: Humanization (adds realistic delays)
ALTORO_ENABLE_HUMANIZED_BEHAVIOR=false
ALTORO_HUMANIZATION_LEVEL=fast
```

### Configuration Priority

1. **Environment variables** (`.env` file)
2. **Default values** (in `src/core/config.py`)

All settings are validated using **Pydantic** for type safety.

---

## 🎯 The 6 Automation Parts

### Part 1: Login Testing 🔐

**File:** `src/orchestration/account_login.py`

**Purpose:** Validate authentication with positive and negative test scenarios.

**Workflow:**
1. Navigate to login page
2. Perform successful login with retry logic (up to 3 attempts)
3. Assert login success by checking logged-in state
4. Perform negative test with incorrect password
5. Capture screenshots on failure

**Features:**
- Configurable retry attempts (`max_login_retries`)
- Error screenshot capture for debugging
- Exception handling with structured logging

**Output:**
- Screenshots: `artifacts/screenshots/login_*.png`
- Traces: `artifacts/traces/trace.zip`
- Logs: `artifacts/logs/run.log`

---

### Part 2: Account Summary & Transaction History 💰

**File:** `src/orchestration/accounts_summary.py`

**Purpose:** Extract comprehensive account balances and transaction history for all accounts.

**Workflow:**
1. Authenticate user
2. Navigate to account summary page
3. Iterate through all available accounts
4. For each account, extract:
   - Account ID/Number
   - Account Name/Type
   - Total Balance
   - Available Balance
   - Complete transaction history (credits and debits)
5. Save to Excel workbook

**Features:**
- **Automatic session recovery** on timeout (decorator-based)
- Multi-account iteration with progress tracking
- Creates output directory if missing
- Multi-sheet Excel output

**Excel Sheets Generated:**
- `Account_Summary` - All account balances
- `Transactions_800002` - Transaction history for account 800002
- `Transactions_800003` - Transaction history for account 800003
- *(Additional sheets per account)*

**Data Extracted:**
| Column | Description |
|--------|-------------|
| Account ID/Number | Unique account identifier |
| Account Name/Type | Account description (e.g., "Savings", "Checking") |
| Total Balance | Ending balance |
| Available Balance | Available balance for withdrawal |

**Transaction Columns:**
| Column | Description |
|--------|-------------|
| Transaction Date | Date of transaction |
| Transaction Description | Transaction description/memo |
| Credit Amount | Credit transactions (deposits) |
| Debit Amount | Debit transactions (withdrawals) |

**Logging Output:**
```
Account Summary Statistics:
  • Total accounts: 3
✓ Saved account summary to sheet: Account_Summary
✓ Saved 15 transactions for account 800002 to sheet: Transactions_800002
Transaction Summary:
  • Total transaction sheets created: 3
  • Total transactions extracted: 45
```

---

### Part 3: Transaction Filtering & High-Value Analysis 📊

**File:** `src/orchestration/transaction.py`

**Purpose:** Apply date range filters and identify high-value credit transactions.

**Workflow:**
1. Authenticate user
2. Navigate to "View Recent Transactions" page
3. Apply date range filter (configurable via settings)
4. Extract ALL transactions across ALL accounts from unified table
5. **Task 3.1:** Save date-filtered transactions
6. **Task 3.2:** Filter high-value credits (≥ $150), sort descending
7. Save both datasets to Excel

**Features:**
- Web-based date filtering (no programmatic iteration needed)
- Unified transaction view across all accounts
- Automatic session recovery
- Configurable high-value threshold (`HIGH_VALUE_CREDIT_THRESHOLD = 150.0`)

**Excel Sheets Generated:**
- `Filtered_Transactions` - All transactions in date range
- `High_Value_Credits` - Credits ≥ $150, sorted by amount

**Transaction Columns:**
| Column | Description |
|--------|-------------|
| Transaction ID | Unique transaction identifier |
| Transaction Time | Timestamp (YYYY-MM-DD HH:MM) |
| Account ID | Account where transaction occurred |
| Action | Transaction type (Deposit/Withdrawal) |
| Debit | Debit amount (withdrawals) |
| Credit | Credit amount (deposits) |

**Example Date Filter:**
- Start: `2025-02-01`
- End: `2025-04-15`

**Logging Output:**
```
Extracted 87 transactions from all accounts
Task 3.1 Summary - 87 transactions extracted
Task 3.2 Summary - High-value credits (>= $150.00): 12 transactions
```

---

### Part 4: Fund Transfer with Verification 💸

**File:** `src/orchestration/transfer.py`

**Purpose:** Execute automated fund transfer and verify balance changes with assertion-based validation.

**Workflow:**
1. Authenticate user
2. Navigate to account summary and capture **BEFORE** balances
3. Execute fund transfer:
   - **Source:** 800002 Savings
   - **Destination:** 800003 Checking
   - **Amount:** $250.00 (configurable)
4. Capture transfer confirmation:
   - Confirmation message
   - Reference number (if available)
   - Screenshot of confirmation page
5. Navigate to account summary and capture **AFTER** balances
6. Verify balance changes:
   - Assert: Source decreased by $250
   - Assert: Destination increased by $250
7. **Raise exception if verification fails**
8. Save comprehensive transfer details to Excel

**Features:**
- Before/after balance tracking
- **Automatic balance verification** with assertions
- Confirmation screenshot capture
- Reference number extraction
- Session recovery on timeout
- **Fails loudly** on verification mismatch

**Excel Sheet Generated:**
- `Transfer_Details` with columns:
  - Source Account
  - Destination Account
  - Transfer Amount
  - Confirmation Message
  - Transaction Timestamp
  - Source Balance Before
  - Source Balance After
  - Destination Balance Before
  - Destination Balance After
  - Verification Status

**Output Artifacts:**
- Screenshot: `artifacts/screenshots/transfer_confirmation_*.png`
- Excel: Transfer details row in `Altoro_Report.xlsx`

**Example Verification:**
```
Transfer Verification:
  ✓ Source account (800002 Savings):
    Before: $15,425.33 → After: $15,175.33 (Changed: -$250.00)
  ✓ Destination account (800003 Checking):
    Before: $6,042.25 → After: $6,292.25 (Changed: +$250.00)
✓ Transfer verified successfully
```

---

### Part 5: Product Catalog Extraction 📚

**File:** `src/orchestration/products.py`

**Purpose:** Scrape comprehensive product information from all banking product categories.

**Workflow:**
1. Navigate to **PERSONAL** section (header navigation)
2. Extract products from 6 PERSONAL categories:
   - Deposit Product
   - Checking
   - Loan Products
   - Cards
   - Investments & Insurance
   - Other Services
3. Navigate to **SMALL BUSINESS** section
4. Extract products from 6 SMALL BUSINESS categories:
   - Deposit Products
   - Lending Services
   - Cards
   - Insurance
   - Retirement
   - Other Services
5. For each category, extract:
   - Product names (from UL/LI lists)
   - Descriptions
   - Features
   - Promotional offers (paragraphs with "$" or keywords)
   - Terms and conditions (paragraphs starting with "Note:", "Terms:")
   - Last updated date
6. Save to Excel

**Features:**
- Automatic extraction from all 12 categories
- Promotional offer detection (keywords: "$", "free", "bonus", "offer")
- Terms & conditions extraction
- No authentication required (public pages)

**Excel Sheet Generated:**
- `Product_Catalog` with columns:
  - Section (PERSONAL / SMALL BUSINESS)
  - Category
  - Product Name
  - Description
  - Features
  - Promotions
  - Terms
  - Last Updated

**Example Output:**
```
Extracted 8 products from PERSONAL → Deposit Product
Extracted 5 products from PERSONAL → Checking
...
Total: 47 products extracted across 12 categories
```

---

### Part 6: API Validation & Reconciliation 🔄

**File:** `src/orchestration/api_validate.py`

**Purpose:** Retrieve data programmatically via REST API and reconcile with web-scraped data to detect discrepancies.

**Workflow:**

**Task 6.1: API Authentication**
1. Authenticate with REST API using admin credentials
2. Obtain authentication token (JWT)
3. Track token expiration with automatic refresh

**Task 6.2: Programmatic Data Retrieval**
- **Step A:** Retrieve account list
  - Endpoint: `GET /api/account`
  - Returns: Array of account IDs
- **Step B:** Get detailed account information for each account
  - Endpoint: `GET /api/account/{accountNo}`
  - Returns: Account ID, Name, Type, Balance, Available Balance
- **Step C:** Extract transaction history with date filter
  - Endpoint: `POST /api/account/{accountNo}/transactions`
  - Date range: `api_filter_start` to `api_filter_end`
  - Returns: Transaction ID, Date, Description, Debit, Credit, Amount

**Task 6.3: Cross-Validation & Reconciliation**
1. Compare API account data with web-scraped data (from Part 2)
2. Compare API transaction data with web-scraped data (from Part 3)
3. Calculate variances:
   - Account balance variance (API balance - Web balance)
   - Transaction total variance by account (API totals - Web totals)
   - Transaction count variance
4. Determine match status:
   - **"Match"** if variance < $0.01
   - **"Variance"** if variance ≥ $0.01
   - **"Data Missing"** if data unavailable from either source
5. Generate comprehensive reconciliation report

**Features:**
- **Token Management:** Automatic refresh 5 minutes before expiration
- **Exponential Backoff Retry:** Retries on 500 errors, timeouts, network failures
- **Graceful Degradation:** Handles API unavailability without crashing
- **Detailed Variance Analysis:** Account-level and transaction-level reconciliation
- **Match Status Determination:** Tolerance-based matching ($0.01)

**Error Handling:**
- **Authentication errors** → Skip Part 6 with warning, write "API Unavailable" report
- **Connection errors** → Retry with backoff, then skip if exhausted
- **Retry exhaustion** → Write error report with details
- **All other errors** → Catch and log, write generic error report

**Excel Sheet Generated:**
- `API_Data_Validation` with **4 sections:**

**Section 1: API Authentication Status**
- Status (Success / Failed)
- Username
- API Base URL
- Token Status
- Date Range

**Section 2: Reconciliation Summary**
- API Accounts Retrieved
- API Transactions Retrieved
- Web Accounts Scraped
- Web Transactions Scraped
- Account Matches
- Account Variances
- Transaction Matches
- Transaction Variances

**Section 3: Account Reconciliation (API vs Web)**
| Column | Description |
|--------|-------------|
| Account ID | Account identifier |
| Account Name | Account name/type |
| API Balance | Balance from API |
| Web Balance | Balance from web scraping |
| Variance | API - Web |
| Match Status | Match / Variance / Data Missing |

**Section 4: Transaction Reconciliation by Account (API vs Web)**
| Column | Description |
|--------|-------------|
| Account ID | Account identifier |
| API Debit Total | Sum of debits from API |
| API Credit Total | Sum of credits from API |
| API Transaction Count | Number of API transactions |
| Web Debit Total | Sum of debits from web |
| Web Credit Total | Sum of credits from web |
| Web Transaction Count | Number of web transactions |
| Debit Variance | API - Web |
| Credit Variance | API - Web |
| Count Variance | API - Web |
| Match Status | Match / Variance / Data Missing |

**Variance Tolerance:** $0.01 (configurable via `VARIANCE_TOLERANCE` constant)

**Example Output:**
```
Step A: Retrieving account list from API...
  Retrieved 3 accounts from GET /api/account
Step B: Retrieving detailed account information...
  Account 800002: Corporate Savings
  Account 800003: Corporate Checking
  ✓ Retrieved 3 accounts with details
Step C: Retrieving date-filtered transactions...
  Account 800002: Retrieved 15 transactions
  Account 800003: Retrieved 12 transactions
  ✓ Step C completed: 27 total transactions retrieved from API

Reconciliation Results:
  • API Accounts: 3 | Web Accounts: 3
  • API Transactions: 27 | Web Transactions: 27
  • Account Variances: 0 | Transaction Variances: 0
  • All data matches within tolerance ($0.01)
```

---

## 📦 Component Documentation

### Core Utilities (`src/core/`)

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `config.py` | Type-safe settings with Pydantic | `Settings` class with validation |
| `logger.py` | Structured logging configuration | `log` instance (Loguru) |
| `constants.py` | Application-wide constants | Sheet names, thresholds, selectors |
| `excel.py` | Multi-sheet Excel writer | `ExcelWriter` context manager |
| `excel_helpers.py` | Single-sheet writer | `write_single_sheet()` |
| `utils.py` | Parsing and formatting | `parse_money()`, `clean_account_name()` |
| `auth_helpers.py` | Authentication helpers | `authenticate_and_setup()` |
| `session_handler.py` | Session recovery decorator | `@with_session_retry()` |
| `dataframe_helpers.py` | DataFrame operations | `normalize_column_names()`, `group_and_sum_by_account()`, `calculate_variance()`, `add_match_status()` |

### Web Automation (`src/web/`)

**Architecture:** Page Object Model (POM)

| Module | Class | Purpose |
|--------|-------|---------|
| `browser.py` | `browser_session()` | Context manager for Playwright browser |
| `pages/base_page.py` | `BasePage` | Base class with common operations (click, fill, wait, screenshot) |
| `pages/login_page.py` | `LoginPage` | Login functionality with retry logic |
| `pages/accounts_page.py` | `AccountsPage` | Account summary iteration and transaction extraction |
| `pages/transactions_page.py` | `TransactionsPage` | Date filtering and transaction parsing |
| `pages/transfer_page.py` | `TransferPage` | Fund transfer with confirmation capture |
| `pages/products_page.py` | `ProductsPage` | Product catalog scraping from 12 categories |

**Key Design Patterns:**
- **Encapsulation:** Each page class owns its selectors and actions
- **Inheritance:** All pages extend `BasePage` for common operations
- **Humanization:** Optional realistic delays (configurable)
- **Session Context:** Pages hold reference to login page for re-authentication

### API Integration (`src/api/`)

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `client.py` | REST API client | Token management, connection pooling, retry decorators |
| `endpoints.py` | Endpoint definitions | URL builders for accounts and transactions |
| `exceptions.py` | Exception hierarchy | `APIError`, `APIAuthenticationError`, `APIConnectionError`, `MaxRetriesExceededError` |
| `retry_handler.py` | Retry decorator | Exponential backoff, max attempts, retryable status codes |

**API Client Features:**
- **Context Manager:** Automatic resource cleanup with `__enter__` / `__exit__`
- **Token Management:** Proactive refresh 5 minutes before expiration
- **Connection Pooling:** Persistent `httpx.Client` for performance
- **Retry Logic:** Decorator-based retry on 500 errors, timeouts, network failures
- **Error Handling:** Structured exceptions with status codes and response bodies

**Retry Configuration:**
- Max retries: 3 (default)
- Backoff factor: 2.0 (exponential)
- Jitter: Random 0-1s delay to prevent thundering herd
- Retryable status codes: 500 (Internal Server Error)
- Handled status codes: 200, 400, 401, 500, 501 (all others → generic `APIError`)

### Orchestration (`src/orchestration/`)

| Module | Part | Description |
|--------|------|-------------|
| `run_all.py` | All | Main entry point, executes Parts 1-6 sequentially |
| `account_login.py` | 1 | Login testing (happy + negative paths) |
| `accounts_summary.py` | 2 | Account summary and transaction history |
| `transaction.py` | 3 | Transaction filtering and high-value analysis |
| `transfer.py` | 4 | Fund transfer with verification |
| `products.py` | 5 | Product catalog extraction |
| `api_validate.py` | 6 | API data retrieval and reconciliation |

**Orchestration Design:**
- **Independent Execution:** Each part can run standalone
- **Sequential Pipeline:** `run_all.py` executes parts in order
- **Shared Data:** Parts 2-3 write Excel, Part 6 reads for reconciliation
- **Error Isolation:** Part failure doesn't crash entire pipeline
- **Comprehensive Logging:** Structured logs with progress tracking

---

## 🐳 Running the Project

### Docker Compose Commands

#### Run Full Workflow (All Parts)
```bash
make up
# Executes: Parts 1 → 2 → 3 → 4 → 5 → 6
```

#### Run Individual Parts
```bash
make part1     # Login testing
make part2     # Account summary extraction
make part3     # Transaction filtering & high-value analysis
make part4     # Fund transfer with verification
make part5     # Product catalog scraping
make part6     # API validation & reconciliation
```

#### Management Commands
```bash
make build     # Build Docker image
make down      # Stop and remove containers
make logs      # Tail container logs
make ps        # Show service status
make shell     # Open interactive container shell
make clean     # Remove all artifacts
make pyver     # Check Python version in container
```

### Local Development (Without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium

# Configure environment
cp .env.example .env
nano .env

# Run full workflow
python -m src.orchestration.run_all

# Run individual parts
python -m src.orchestration.account_login
python -m src.orchestration.accounts_summary
python -m src.orchestration.transaction
python -m src.orchestration.transfer
python -m src.orchestration.products
python -m src.orchestration.api_validate
```

---

## 📊 Output Artifacts

### 1. Excel Report (`artifacts/outputs/Altoro_Report.xlsx`)

Single consolidated workbook with multiple sheets:

| Sheet Name | Source | Description |
|------------|--------|-------------|
| `Account_Summary` | Part 2 | All account balances |
| `Transactions_800002` | Part 2 | Transaction history for account 800002 |
| `Transactions_800003` | Part 2 | Transaction history for account 800003 |
| `Transactions_...` | Part 2 | Additional per-account sheets |
| `Filtered_Transactions` | Part 3 | Date-filtered transactions |
| `High_Value_Credits` | Part 3 | Credits ≥ $150 |
| `Transfer_Details` | Part 4 | Fund transfer confirmation and verification |
| `Product_Catalog` | Part 5 | Banking product catalog (12 categories) |
| `API_Data_Validation` | Part 6 | API vs Web reconciliation report |

**Excel Features:**
- Auto-sized columns
- Styled headers (bold, light blue background)
- Formatted numbers (currency with 2 decimals)
- Date formatting
- Multi-section sheets (Part 6)

### 2. Logs (`artifacts/logs/run.log`)

- **Format:** Structured logs with timestamps, levels, and source
- **Console:** Colored output with Loguru
- **File:** Persistent log file with rotation support
- **Levels:** DEBUG, INFO, WARNING, ERROR

**Example Log Output:**
```
2025-10-31 20:09:15.234 | INFO     | src.orchestration.accounts_summary:run_part2_accounts:51 - Opening account summary page...
2025-10-31 20:09:17.123 | INFO     | src.orchestration.accounts_summary:run_part2_accounts:54 - Starting account and transaction data extraction...
2025-10-31 20:09:19.456 | INFO     | src.orchestration.accounts_summary:run_part2_accounts:57 - Extraction complete - 3 accounts processed
```

### 3. Screenshots (`artifacts/screenshots/*.png`)

- Login failures (`login_failure_*.png`)
- Transfer confirmations (`transfer_confirmation_*.png`)
- Error states (captured automatically on exceptions)

### 4. Playwright Traces (`artifacts/traces/trace.zip`)

Complete trace of browser interaction for debugging:
- Network requests/responses
- DOM snapshots
- Screenshots at each step
- Console logs
- Errors and exceptions

**View Trace:**
```bash
playwright show-trace artifacts/traces/trace.zip
```

---

## 🎨 Design Patterns

### 1. Page Object Model (POM)
- **Encapsulation:** Each page owns its selectors and actions
- **Reusability:** Common operations in `BasePage`
- **Maintainability:** Single source of truth for page structure

### 2. Dependency Injection
- Pages receive `Page` object via constructor
- Settings injected via Pydantic from environment

### 3. Context Managers
- Browser session management (`browser_session`)
- API client lifecycle (`AltoroAPI`)
- Excel writer (`ExcelWriter`)

### 4. Decorator Pattern
- Session retry: `@with_session_retry()`
- API retry: `@with_api_retry()`

### 5. Strategy Pattern
- Configurable humanization behavior
- Pluggable retry strategies

### 6. Repository Pattern
- Page classes act as repositories for page data
- Clean separation of data access and business logic

### 7. Factory Pattern
- Dynamic DataFrame creation from scraped data
- Excel sheet generation based on data structure

---

## 📚 Dependencies

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `playwright` | 1.48.0 | Browser automation framework |
| `pydantic` | 2.9.2 | Data validation and settings |
| `pydantic-settings` | 2.6.1 | Environment-based configuration |
| `python-dotenv` | 1.0.1 | .env file support |
| `httpx` | 0.27.2 | Modern async HTTP client |
| `pandas` | 2.2.2 | Data analysis and manipulation |
| `openpyxl` | 3.1.5 | Excel read/write support |
| `loguru` | 0.7.2 | Advanced logging |

### Docker Base Image
- **Image:** `mcr.microsoft.com/playwright/python:v1.48.0-jammy`
- **OS:** Ubuntu 22.04 (Jammy)
- **Browser:** Chromium (pre-installed)
- **Python:** 3.11

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Login Failures
**Symptoms:** Screenshots show login error, logs show "Login failed"

**Solutions:**
- Verify credentials in `.env` file
- Check if demo site is accessible: https://demo.testfire.net
- Increase `max_login_retries` in settings
- Check for CAPTCHA or site maintenance

#### 2. Session Timeouts
**Symptoms:** Logs show "Session expired", "Target closed", or "Navigation timeout"

**Solutions:**
- Session recovery should handle this automatically
- Increase `max_session_retries` if needed
- Check network stability
- Verify site isn't rate-limiting

#### 3. API Authentication Failures
**Symptoms:** Logs show "API authentication failed", status code 401

**Solutions:**
- Verify `ALTORO_API_USER` and `ALTORO_API_PASSWORD` in `.env`
- Check API endpoint is correct (`ALTORO_BASE_URL/api/...`)
- Review API error response in logs

#### 4. Excel File Locked
**Symptoms:** Error writing Excel file, "Permission denied"

**Solutions:**
- Close Excel file if open
- Check file permissions on `artifacts/outputs/` directory
- Run `make clean` to remove stale files

#### 5. Data Type Mismatch in Reconciliation
**Symptoms:** ValueError: "You are trying to merge on object and int64 columns"

**Solutions:**
- Already fixed via dtype specification in `run_all.py`
- If issue persists, check Excel column headers match expected names
- Verify data integrity in source sheets

#### 6. Docker Build Failures
**Symptoms:** Docker build fails, dependency errors

**Solutions:**
- Update Docker to latest version
- Clear Docker cache: `docker system prune -a`
- Check internet connectivity
- Verify `requirements.txt` syntax

### Debugging with Playwright Traces

```bash
# View trace file in Playwright UI
playwright show-trace artifacts/traces/trace.zip

# Features:
# - Inspect each action
# - View DOM snapshots
# - Check network requests
# - See console logs
# - Review errors with context
```

### Enable Verbose Logging

Set environment variable:
```bash
export ALTORO_LOG_LEVEL=DEBUG
```

Or modify `src/core/logger.py`:
```python
logger.add(sys.stdout, level="DEBUG")
```

---

## 🧾 License

This project is for **educational and evaluation purposes only**.

⚠️ **WARNING:** Do **not** use this automation against:
- Real banking systems
- Production environments
- Systems without explicit authorization

**Intended Use:**
- Learning RPA and browser automation
- Demonstrating Playwright capabilities
- Portfolio/interview showcase
- Training and workshops

**Demo Site:** https://demo.testfire.net (Altoro Mutual)
- Maintained by IBM/HCL for security testing
- Safe for automation practice

---

## 🏆 Project Highlights

- ✅ **Production-Ready:** Comprehensive error handling, retry logic, logging
- ✅ **Well-Architected:** Clean separation of concerns, Page Object Model
- ✅ **Type-Safe:** Pydantic validation throughout
- ✅ **Thoroughly Tested:** 6 independent workflows validated
- ✅ **Docker-First:** Reproducible execution environment
- ✅ **Comprehensive Reporting:** Multi-sheet Excel with reconciliation
- ✅ **Debuggable:** Full traces, structured logs, screenshots
- ✅ **Maintainable:** Modular architecture, DRY principles
- ✅ **Configurable:** Environment-driven with sensible defaults
- ✅ **Documented:** Extensive inline documentation and README

---

## 📈 Project Statistics

- **Total Python Files:** 28
- **Lines of Code:** ~4,000+
- **Dependencies:** 8 packages
- **Automation Parts:** 6 workflows
- **Excel Sheets Generated:** 8+ (varies by account count)
- **API Endpoints Used:** 3 (login, accounts, transactions)
- **Page Objects:** 6 pages
- **Docker Layers:** Multi-stage with Playwright base
- **Supported Browsers:** Chromium (extensible to Firefox/WebKit)

---

**Developed as a comprehensive RPA demonstration project**

🔗 **Demo Site:** [https://demo.testfire.net](https://demo.testfire.net)
📧 **Questions?** Open an issue on the repository

---

*Last Updated: 2025-11-01*
