"""Application configuration using Pydantic settings with environment variable support."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with defaults and environment variable override support.

    Environment variables can be set with ALTORO_ prefix (e.g., ALTORO_BASE_URL).
    Settings are loaded from .env file if present.

    Attributes:
        Authentication:
            base_url: Target website URL
            user: Login username for web interface
            password: Login password for web interface
            api_user: Username for REST API authentication
            api_password: Password for REST API authentication

        Directories:
            screenshot_dir: Path for error screenshots
            trace_dir: Path for Playwright traces
            excel_path: Output path for Excel reports

        Orchestration:
            max_login_retries: Maximum login retry attempts
            date_format: Date parsing format string
            filter_start: Transaction filter start date
            filter_end: Transaction filter end date
            api_filter_start: API filter start date
            api_filter_end: API filter end date

        Transfer Scenario:
            transfer_from: Source account for transfers
            transfer_to: Destination account for transfers
            transfer_amount: Transfer amount

        Humanization:
            enable_humanized_behavior: Enable human-like interaction delays
            humanization_level: Interaction speed (fast, normal, slow)
            min_action_delay_ms: Minimum delay between actions
            max_action_delay_ms: Maximum delay between actions
            typing_speed_ms: Milliseconds per character when typing

        Session Management:
            max_session_retries: Maximum retry attempts on session timeout
            enable_session_monitoring: Enable automatic session recovery
    """

    base_url: str = "https://demo.testfire.net"
    user: str = "jsmith"
    password: str = "demo1234"
    # API credentials (for Part 6 - REST API Integration)
    api_user: str = "jsmith"
    api_password: str = "demo1234"
    screenshot_dir: str = "artifacts/screenshots"
    trace_dir: str = "artifacts/traces"
    excel_path: str = "artifacts/outputs/Altoro_Report.xlsx"

    # orchestrator knobs
    max_login_retries: int = 3
    date_format: str = "%Y-%m-%d"  # Format for transaction dates (yyyy-mm-dd)
    transaction_time_format: str = "%Y-%m-%d %H:%M"  # Format for transaction timestamps
    filter_start: str = "2025-02-01"  # Transaction filter start date (yyyy-mm-dd)
    filter_end: str = "2025-04-15"  # Transaction filter end date (yyyy-mm-dd)
    api_filter_start: str = "2025-02-01"
    api_filter_end: str = "2025-04-15"

    # transfer scenario
    transfer_from: str = "800002 Savings"
    transfer_to: str = "800003 Checking"
    transfer_amount: float = 250.00

    # humanization settings
    enable_humanized_behavior: bool = False
    humanization_level: str = "normal"  # fast, normal, slow
    min_action_delay_ms: int = 300
    max_action_delay_ms: int = 1500
    typing_speed_ms: int = 150  # milliseconds per character

    # session management settings
    max_session_retries: int = 2  # Maximum retries on session timeout
    enable_session_monitoring: bool = True  # Enable automatic session recovery

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ALTORO_")


settings = Settings()
