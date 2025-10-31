"""Product catalog extraction page automation for Altoro Mutual."""

from typing import List, Dict, Any, Tuple
from playwright.sync_api import Page

from src.web.pages.base_page import BasePage
from src.core.session_handler import with_session_retry
from src.core.logger import log


class ProductsPage(BasePage):
    """
    Handles product catalog extraction from Altoro Mutual.

    Provides methods for:
    - Navigating to PERSONAL and SMALL BUSINESS sections
    - Extracting category links from landing pages
    - Clicking through product categories and scraping data
    - Parsing promotional offers and terms
    - Auto-recovery from session timeouts

    Page Structure:
    - Header navigation: PERSONAL / SMALL BUSINESS links
    - Landing pages: H2 tags with links to category pages
    - Category pages: H1, description paragraphs, UL with product list items
    - Products displayed as list items (not individual detail pages)

    Navigation Flow:
    1. Click PERSONAL navigation -> Shows landing page with H2 links
    2. For each H2 > A link: Click -> Scrape category page -> Go back
    3. Click SMALL BUSINESS navigation -> Shows landing page with H2 links
    4. For each H2 > A link: Click -> Scrape category page -> Go back

    Typical category page contains:
        - H1 with category name
        - Description paragraphs
        - UL with product list items
        - Promotional text (paragraphs with "$" or special keywords)
        - Terms and conditions
        - Last updated information
    """

    def __init__(self, page: Page) -> None:
        """
        Initialize ProductsPage with Playwright page.

        Args:
            page: Playwright Page object for browser automation
        """
        super().__init__(page)

    def navigate_personal(self) -> None:
        """
        Navigate to PERSONAL section using header navigation.

        Clicks the "PERSONAL" link in the main navigation bar.
        This loads the PERSONAL landing page with H2 category links.

        Note:
            Uses .first property to handle multiple "PERSONAL" links on page
            (header navigation + sidebar links).
        """
        personal_link = self.page.get_by_role("link", name="PERSONAL").first
        if personal_link.count():
            self.click(personal_link, description="PERSONAL navigation link")
            self.page.wait_for_load_state()

    def navigate_small_business(self) -> None:
        """
        Navigate to SMALL BUSINESS section using header navigation.

        Clicks the "SMALL BUSINESS" link in the main navigation bar.
        This loads the SMALL BUSINESS landing page with H2 category links.

        Note:
            Uses .first property to handle multiple "SMALL BUSINESS" links on page
            (header navigation + sidebar links).
        """
        small_business_link = self.page.get_by_role("link", name="SMALL BUSINESS").first
        if small_business_link.count():
            self.click(
                small_business_link, description="SMALL BUSINESS navigation link"
            )
            self.page.wait_for_load_state()

    def get_category_links(self) -> List[Tuple[str, str]]:
        """
        Extract all category links from current landing page.

        Parses the landing page HTML to find all H2 tags containing links.
        These links point to individual category pages.

        Returns:
            List of tuples (category_name, href), where:
            - category_name: Text inside the H2 > A tag (e.g., "Deposit Products")
            - href: Link href attribute (e.g., "index.jsp?content=personal_deposit.htm")

        Example:
            [
                ("Deposit Products", "index.jsp?content=personal_deposit.htm"),
                ("Checking", "index.jsp?content=personal_checking.htm"),
                ...
            ]

        Note:
            Returns empty list if no H2 > A links found on page.
        """
        category_links = []

        # Find all H2 tags
        h2_elements = self.page.locator("h2").all()
        for h2_tag in h2_elements:
            # Find A tag inside H2
            link_tag = h2_tag.locator("a").first
            if link_tag.count() > 0:
                category_name = link_tag.inner_text().strip()
                href = link_tag.get_attribute("href") or ""
                if category_name and href:
                    category_links.append((category_name, href))

        return category_links

    def click_category_link(self, category_name: str) -> None:
        """
        Click a category link by its visible text.

        Finds and clicks the link inside H2 tag with the given category name.

        Args:
            category_name: Display name of the category (e.g., "Deposit Products")

        Note:
            Waits for page load after clicking.
            Uses humanized clicking behavior from BasePage.
        """
        # Find H2 containing the category name, then click its link
        category_link = self.page.locator(f"h2 >> a:has-text('{category_name}')")
        if category_link.count():
            self.click(category_link, description=f"{category_name} category link")
            self.page.wait_for_load_state()

    def _extract_promotions(self) -> str:
        """
        Extract promotional offers from page content.

        Searches for paragraphs containing monetary amounts or promotional keywords.

        Returns:
            String containing promotional text, or empty string if none found

        Note:
            Looks for paragraphs containing:
            - Dollar signs ($)
            - Keywords: "bonus", "offer", "promotion", "special", "limited time"
        """
        promotions = []
        promotional_keywords = [
            "bonus",
            "offer",
            "promotion",
            "special",
            "limited time",
        ]

        paragraphs = self.page.locator("p").all()
        for paragraph in paragraphs:
            text = paragraph.inner_text().strip()
            # Check for dollar signs or promotional keywords
            if "$" in text or any(
                keyword in text.lower() for keyword in promotional_keywords
            ):
                promotions.append(text)

        return " | ".join(promotions) if promotions else ""

    def _extract_terms(self) -> str:
        """
        Extract terms and conditions from page content.

        Searches for paragraphs starting with "Note:", "Terms:", or "Conditions:".

        Returns:
            String containing terms text, or empty string if none found
        """
        terms = []
        term_keywords = ["note:", "terms:", "conditions:", "disclaimer:"]

        paragraphs = self.page.locator("p").all()
        for paragraph in paragraphs:
            text = paragraph.inner_text().strip()
            # Check if paragraph starts with term keywords
            if any(text.lower().startswith(keyword) for keyword in term_keywords):
                terms.append(text)

        return " | ".join(terms) if terms else ""

    def extract_category_data(
        self, section: str, expected_category: str
    ) -> List[Dict[str, Any]]:
        """
        Extract all product information from current category page.

        Parses the category page to extract:
        - Category name from H1
        - Description from first paragraph(s)
        - Individual product names from UL/LI list
        - Promotional offers
        - Terms and conditions
        - Last updated date

        Args:
            section: Section name ("PERSONAL" or "SMALL BUSINESS")
            expected_category: Expected category name for validation

        Returns:
            List of product dictionaries, each containing:
            - Section: PERSONAL or SMALL BUSINESS
            - Category: Category name
            - Product Name: Individual product name from list
            - Description: Category description
            - Features: Combined features (currently same as description)
            - Promotions: Promotional offers text
            - Terms: Terms and conditions text
            - Last Updated: Last updated date

        Note:
            Returns empty list if no products found on page.
            Each list item becomes a separate product record.
            If no UL/LI found, creates single record with category info.
        """
        products = []

        # Extract category name from H1
        category_h1 = self.page.locator("h1").first
        category_name = (
            category_h1.inner_text().strip()
            if category_h1.count() > 0
            else expected_category
        )

        # Extract description from first paragraph(s)
        description = ""
        paragraphs = self.page.locator("p").all()
        for paragraph in paragraphs:
            text = paragraph.inner_text().strip()
            # Skip promotional and terms paragraphs
            if text and not any(
                keyword in text.lower()
                for keyword in [
                    "bonus",
                    "offer",
                    "note:",
                    "terms:",
                    "for more information",
                    "last updated on",
                ]
            ):
                description = text

        # Extract product list from UL/LI
        product_list = self.page.locator(".fl ul").first
        if product_list.count() > 0:
            list_items = product_list.locator("li").all()
            for list_item in list_items:
                product_name = list_item.inner_text().strip()
                if product_name:
                    products.append(
                        {
                            "Section": section,
                            "Category": category_name,
                            "Product Name": product_name,
                            "Description": description,
                            "Features": description,  # Using description as features
                            "Promotions": self._extract_promotions(),
                            "Terms": self._extract_terms(),
                        }
                    )
        return products

    @with_session_retry()
    def scrape_all_products(self) -> List[Dict[str, Any]]:
        """
        Scrape all products from all categories (PERSONAL and SMALL BUSINESS).

        Workflow:
        1. Navigate to PERSONAL section landing page
        2. Extract all H2 > A category links
        3. For each category link:
           a. Click link to navigate to category page
           b. Extract products from category page
           c. Go back to landing page
        4. Navigate to SMALL BUSINESS section landing page
        5. Extract all H2 > A category links
        6. For each category link:
           a. Click link to navigate to category page
           b. Extract products from category page
           c. Go back to landing page

        Returns:
            List of all product dictionaries from all categories

        Note:
            Decorated with @with_session_retry for automatic recovery from session timeouts.
            Maximum 2 retry attempts on session expiration.
            Logs progress for each category processed.
            Uses page.go_back() to return to landing page after each category.
        """
        all_products = []

        # Scrape PERSONAL categories
        log.info("Starting PERSONAL product extraction...")
        self.navigate_personal()

        # Extract category links from PERSONAL landing page
        personal_category_links = self.get_category_links()
        log.info(f"Found {len(personal_category_links)} PERSONAL categories")

        for category_name, href in personal_category_links:
            log.info(f"Extracting PERSONAL -> {category_name}...")

            # Click category link to navigate to category page
            self.click_category_link(category_name)

            # Extract products from category page
            category_products = self.extract_category_data("PERSONAL", category_name)
            all_products.extend(category_products)
            log.info(
                f"  Extracted {len(category_products)} products from {category_name}"
            )

            # Go back to PERSONAL landing page
            self.page.go_back()
            self.page.wait_for_load_state()

        # Scrape SMALL BUSINESS categories
        log.info("Starting SMALL BUSINESS product extraction...")
        self.navigate_small_business()

        # Extract category links from SMALL BUSINESS landing page
        small_business_category_links = self.get_category_links()
        log.info(
            f"Found {len(small_business_category_links)} SMALL BUSINESS categories"
        )

        for category_name, href in small_business_category_links:
            log.info(f"Extracting SMALL BUSINESS -> {category_name}...")

            # Click category link to navigate to category page
            self.click_category_link(category_name)

            # Extract products from category page
            category_products = self.extract_category_data(
                "SMALL BUSINESS", category_name
            )
            all_products.extend(category_products)
            log.info(
                f"  Extracted {len(category_products)} products from {category_name}"
            )

            # Go back to SMALL BUSINESS landing page
            self.page.go_back()
            self.page.wait_for_load_state()

        log.info(f"Product extraction complete - Total products: {len(all_products)}")
        return all_products
