"""Part 5: Product information extraction automation orchestration."""

import pandas as pd
from pathlib import Path
from src.web.browser import browser_session
from src.web.pages.products_page import ProductsPage
from src.core.config import settings
from src.core.excel import ExcelWriter
from src.core.logger import log
from src.core.constants import SHEET_PRODUCT_CATALOG
from src.core.auth_helpers import authenticate_and_setup


def run_part5_products() -> None:
    """
    Execute Part 5: Product catalog extraction from PERSONAL and SMALL BUSINESS sections.

    Workflow:
    2. Navigate to PERSONAL section in header navigation
    3. Extract products from all 6 PERSONAL categories:
       - Deposit Product
       - Checking
       - Loan Products
       - Cards
       - Investments & Insurance
       - Other Services
    4. Navigate to SMALL BUSINESS section in header navigation
    5. Extract products from all 6 SMALL BUSINESS categories:
       - Deposit Products
       - Lending Services
       - Cards
       - Insurance
       - Retirement
       - Other Services
    6. Save comprehensive product catalog to Excel:
       - "Product_Catalog" sheet with all products
       - Columns: Section, Category, Product Name, Description, Features,
                 Promotions, Terms, Last Updated

    Features:
    - Automatic extraction from all 12 product categories
    - Promotional offer detection (paragraphs with "$" or special keywords)
    - Terms and conditions extraction (paragraphs starting with "Note:", "Terms:", etc.)
    - Last updated date extraction
    - Session recovery on timeout
    - Overwrites existing Excel file

    Note:
        Uses configuration from settings:
        - base_url, user, password: Authentication
        - excel_path: Output file path
        - trace_dir: Browser trace directory
        - screenshot_dir: Screenshot directory

        Products are extracted from category pages (not individual detail pages).
        Each product in the category's UL/LI list becomes a separate Excel row.
        All products from one category share the same description, features,
        promotions, and terms.
    """
    with browser_session(settings.trace_dir) as browser_context:
        page = browser_context.new_page()

        # Authenticate user and setup session context
        products_page = ProductsPage(page)
        authenticate_and_setup(page, settings.screenshot_dir, products_page)

        # Scrape all products from all categories
        log.info("Starting product catalog extraction...")
        all_products = products_page.scrape_all_products()
        log.info(
            f"Product extraction complete - Total products extracted: {len(all_products)}"
        )

    # Convert to DataFrame for Excel output
    products_df = pd.DataFrame(all_products)

    # Prepare Excel output
    output_path = Path(settings.excel_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    excel_writer = ExcelWriter(str(output_path))
    excel_writer.write_df(SHEET_PRODUCT_CATALOG, products_df)
    excel_writer.close()

    log.info(f"Product catalog written to Excel → {output_path}")
    log.info(
        f"Part 5 complete - {len(all_products)} products saved to {SHEET_PRODUCT_CATALOG} sheet"
    )


if __name__ == "__main__":
    run_part5_products()
