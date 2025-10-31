"""Base page class with humanized browser interactions and HTML parsing utilities."""

import random
import time
from typing import Optional, Union

from playwright.sync_api import Page, Locator

from src.core.config import settings


class BasePage:
    """Base page with humanized behaviors and common parsing utilities."""

    def __init__(self, page: Page):
        self.page = page
        self.config = settings

    def click(self, locator: Union[str, Locator], description: str = "element") -> None:
        """
        Click an element with humanized behavior: scroll into view, delay, then click.

        Args:
            locator: CSS selector string or Playwright Locator object
            description: Human-readable description for logging
        """
        if not self.config.enable_humanized_behavior:
            # Fast path: direct click without humanization
            if isinstance(locator, str):
                self.page.locator(locator).click()
            else:
                locator.click()
            return

        # Get the locator object
        elem = self.page.locator(locator) if isinstance(locator, str) else locator

        # Humanized behavior
        self._smooth_scroll_to_element(elem)
        self._random_delay()
        elem.click()
        self._random_delay(min_ms=100, max_ms=500)  # Post-click delay

    def fill(
        self, locator: Union[str, Locator], text: str, description: str = "field"
    ) -> None:
        """
        Fill a text field with typing simulation (character-by-character).

        Args:
            locator: CSS selector string or Playwright Locator object
            text: Text to type
            description: Human-readable description for logging
        """
        if not self.config.enable_humanized_behavior:
            # Fast path: instant fill
            if isinstance(locator, str):
                self.page.locator(locator).fill(text)
            else:
                locator.fill(text)
            return

        # Get the locator object
        elem = self.page.locator(locator) if isinstance(locator, str) else locator

        # Humanized typing
        self._smooth_scroll_to_element(elem)
        self._random_delay(min_ms=200, max_ms=600)
        elem.click()  # Focus the field
        self._simulate_typing(elem, text)

    def select_option(
        self,
        locator: Union[str, Locator],
        value: Optional[str] = None,
        label: Optional[str] = None,
        description: str = "dropdown",
    ) -> None:
        """
        Select an option from a dropdown with humanized behavior.

        Args:
            locator: CSS selector string or Playwright Locator object
            value: Option value to select (provide either value or label)
            label: Option label to select (provide either value or label)
            description: Human-readable description for logging
        """
        if not self.config.enable_humanized_behavior:
            # Fast path
            if isinstance(locator, str):
                # For string selectors, use page.select_option
                if value:
                    self.page.select_option(locator, value=value)
                elif label:
                    self.page.select_option(locator, label=label)
            else:
                # For Locator objects, call select_option on the locator itself
                if value:
                    locator.select_option(value=value)
                elif label:
                    locator.select_option(label=label)
            return

        # Get the locator object
        elem = self.page.locator(locator) if isinstance(locator, str) else locator

        # Humanized selection
        self._smooth_scroll_to_element(elem)
        self._random_delay()

        # Select the option
        if isinstance(locator, str):
            # For string selectors, use page.select_option
            if value:
                self.page.select_option(locator, value=value)
            elif label:
                self.page.select_option(locator, label=label)
        else:
            # For Locator objects, call select_option on the locator itself
            if value:
                locator.select_option(value=value)
            elif label:
                locator.select_option(label=label)

        self._random_delay(min_ms=100, max_ms=400)

    def wait_for_selector(
        self, selector: str, timeout: int = 5000, state: str = "visible"
    ) -> None:
        """
        Wait for a selector with optional humanized random delays.

        Args:
            selector: CSS selector to wait for
            timeout: Maximum wait time in milliseconds
            state: Element state to wait for (visible, attached, hidden, detached)
        """
        self.page.wait_for_selector(selector, timeout=timeout, state=state)

        if self.config.enable_humanized_behavior:
            # Add a small delay after element appears (simulating human perception time)
            self._random_delay(min_ms=150, max_ms=400)

    def _random_delay(
        self, min_ms: Optional[int] = None, max_ms: Optional[int] = None
    ) -> None:
        """
        Sleep for a random duration based on configuration.

        Args:
            min_ms: Minimum delay in milliseconds (overrides config)
            max_ms: Maximum delay in milliseconds (overrides config)
        """
        if not self.config.enable_humanized_behavior:
            return

        min_delay = min_ms if min_ms is not None else self.config.min_action_delay_ms
        max_delay = max_ms if max_ms is not None else self.config.max_action_delay_ms

        delay_seconds = random.uniform(min_delay / 1000, max_delay / 1000)
        time.sleep(delay_seconds)

    def _simulate_typing(self, element: Locator, text: str) -> None:
        """
        Type text character-by-character with variable speed.

        Args:
            element: Playwright Locator object to type into
            text: Text to type
        """
        for char in text:
            element.type(char)

            # Variable typing speed
            base_speed = self.config.typing_speed_ms / 1000
            variance = random.uniform(0.5, 1.5)  # 50% slower to 50% faster
            char_delay = base_speed * variance

            # Occasional longer pauses (simulating thinking)
            if random.random() < 0.1:  # 10% chance
                char_delay *= random.uniform(2, 4)

            time.sleep(char_delay)

    def _smooth_scroll_to_element(self, element: Locator) -> None:
        """
        Scroll to element gradually (if enabled).

        Args:
            element: Playwright Locator to scroll to
        """
        if not self.config.enable_humanized_behavior:
            element.scroll_into_view_if_needed()
            return

        # For now, use standard scroll but add a delay
        # Future enhancement: implement actual smooth scrolling with JavaScript
        element.scroll_into_view_if_needed()
        self._random_delay(min_ms=200, max_ms=500)

    def set_session_context(self, login_page, credentials: dict):
        """
        Set session context for automatic session recovery.

        Args:
            login_page: LoginPage instance for re-authentication
            credentials: dict with 'username', 'password', and 'base_url' keys

        This enables the @with_session_retry decorator to automatically
        re-authenticate if the session expires.
        """
        self.login_page = login_page
        self.credentials = credentials
