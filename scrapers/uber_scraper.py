"""Uber driver portal scraper."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper
from src.config import get_settings


class UberScraper(BaseScraper):
    """Scrape trip data from driver.uber.com."""

    def __init__(self):
        super().__init__()
        settings = get_settings()
        self.email = settings.UBER_EMAIL
        self.password = settings.UBER_PASSWORD

    def run(self):
        """Login to Uber driver portal and download trip CSV."""
        output_path = self.get_output_path("uber")

        if os.path.exists(output_path):
            print(f"Already downloaded: {output_path}")
            return output_path

        def scrape(page):
            # Navigate to Uber driver portal
            page.goto("https://drivers.uber.com")
            page.wait_for_timeout(2000)

            # Login
            page.fill('input[name="email"]', self.email)
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

            # Password step (Uber uses multi-step login)
            page.fill('input[name="password"]', self.password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

            # Navigate to earnings/trip history
            page.goto("https://drivers.uber.com/p3/payments/statements")
            page.wait_for_timeout(3000)

            # Look for CSV/download button
            # Note: Uber's UI changes frequently. This selector may need updating.
            with page.expect_download() as download_info:
                page.click('button:has-text("Download")')
            download = download_info.value
            download.save_as(output_path)

            return output_path

        return self.scrape_with_browser(scrape)


if __name__ == "__main__":
    scraper = UberScraper()
    result = scraper.run()
    print(f"Downloaded: {result}")
