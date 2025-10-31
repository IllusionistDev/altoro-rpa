"""Logging configuration using loguru with file rotation and detailed error tracking."""

from loguru import logger
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("artifacts/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger with rotation, async writing, and full error diagnostics
logger.add(
    LOG_DIR / "run.log", rotation="1 MB", enqueue=True, backtrace=True, diagnose=True
)

# Export logger instance for use across the application
log = logger
