"""Base scraper with shared Playwright logic."""
import os
from datetime import date, timedelta
from playwright.sync_api import sync_playwright


class BaseScraper:
    """Base class for all platform scrapers."""

    def __init__(self, imports_dir: str | None = None):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.imports_dir = imports_dir or os.path.join(base, "imports")
        self.yesterday = date.today() - timedelta(days=1)
        os.makedirs(self.imports_dir, exist_ok=True)

    def get_output_path(self, source: str, suffix: str = "") -> str:
        name = f"{source}_{self.yesterday.isoformat()}{suffix}.csv"
        return os.path.join(self.imports_dir, name)

    def run(self):
        """Override in subclass."""
        raise NotImplementedError

    def scrape_with_browser(self, callback):
        """Launch browser and execute callback with page."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                accept_downloads=True,
            )
            page = context.new_page()
            try:
                result = callback(page)
                return result
            finally:
                browser.close()
