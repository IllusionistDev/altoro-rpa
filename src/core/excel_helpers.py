"""Excel writing helper utilities for simplified Excel operations.

This module provides context managers and convenience functions to eliminate
the repetitive pattern of creating ExcelWriter, writing DataFrames, and closing.
"""

from contextlib import contextmanager
from typing import Generator
from pathlib import Path
import pandas as pd

from src.core.excel import ExcelWriter
from src.core.logger import log


@contextmanager
def excel_writer_context(
    file_path: str, ensure_dir: bool = True
) -> Generator[ExcelWriter, None, None]:
    """
    Context manager for Excel writing with automatic cleanup.

    Automatically handles:
    - Creating parent directories if needed
    - Opening ExcelWriter
    - Closing ExcelWriter after use
    - Logging completion

    Args:
        file_path: Path to Excel file
        ensure_dir: Create parent directory if it doesn't exist (default: True)

    Yields:
        ExcelWriter instance ready for use

    Example:
        >>> with excel_writer_context(settings.excel_path) as writer:
        ...     writer.write_df("Sheet1", df1)
        ...     writer.write_df("Sheet2", df2)
    """
    if ensure_dir:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    writer = ExcelWriter(file_path)
    try:
        yield writer
    finally:
        writer.close()
        log.info(f"Excel file written: {file_path}")


def write_single_sheet(
    file_path: str,
    sheet_name: str,
    dataframe: pd.DataFrame,
    ensure_dir: bool = True,
    log_details: bool = True,
) -> None:
    """
    Convenience function to write a single DataFrame to Excel.

    This is a simplified wrapper for the common case of writing one sheet.

    Args:
        file_path: Path to Excel file
        sheet_name: Name of the Excel sheet
        dataframe: pandas DataFrame to write
        ensure_dir: Create parent directory if needed (default: True)
        log_details: Log row count in addition to file path (default: True)

    Example:
        >>> write_single_sheet(
        ...     settings.excel_path,
        ...     "Account_Summary",
        ...     summary_df
        ... )
    """
    with excel_writer_context(file_path, ensure_dir) as writer:
        writer.write_df(sheet_name, dataframe)
        if log_details:
            log.info(f"Wrote {sheet_name} sheet ({len(dataframe)} rows)")


def write_multiple_sheets(
    file_path: str, sheets: dict[str, pd.DataFrame], ensure_dir: bool = True
) -> None:
    """
    Write multiple DataFrames to different sheets in one Excel file.

    Args:
        file_path: Path to Excel file
        sheets: Dictionary mapping sheet names to DataFrames
        ensure_dir: Create parent directory if needed (default: True)

    Example:
        >>> write_multiple_sheets(
        ...     settings.excel_path,
        ...     {
        ...         "Account_Summary": accounts_df,
        ...         "Transactions": transactions_df,
        ...         "Summary": summary_df
        ...     }
        ... )
    """
    with excel_writer_context(file_path, ensure_dir) as writer:
        for sheet_name, dataframe in sheets.items():
            writer.write_df(sheet_name, dataframe)
            log.info(f"Wrote {sheet_name} sheet ({len(dataframe)} rows)")
