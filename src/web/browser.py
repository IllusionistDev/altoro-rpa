"""Browser session management with Playwright."""

from playwright.sync_api import sync_playwright, BrowserContext
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


@contextmanager
def browser_session(trace_dir: str) -> Generator[BrowserContext, None, None]:
    """
    Context manager for Playwright browser session with tracing enabled.

    Creates a Chromium browser instance with:
    - Headless mode enabled
    - HTTPS errors ignored (for testing environments)
    - Fixed viewport size (1280x900)
    - Tracing with screenshots, snapshots, and sources

    Args:
        trace_dir: Directory path where trace.zip will be saved

    Yields:
        BrowserContext: Playwright browser context for page operations
    Note:
        - Creates trace_dir if it doesn't exist
        - Automatically closes browser and saves trace on exit
        - Trace file saved as: {trace_dir}/trace.zip
    """
    Path(trace_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        browser_context = browser.new_context(
            ignore_https_errors=True, viewport={"width": 1280, "height": 900}
        )
        browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)

        try:
            yield browser_context
        finally:
            trace_path = str(Path(trace_dir) / "trace.zip")
            browser_context.tracing.stop(path=trace_path)
            browser.close()
