"""Prima (Taxitronic) cloud portal scraper."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper
from src.config import get_settings


class PrimaScraper(BaseScraper):
    """Scrape trip data from Taxitronic cloud portal."""

    def __init__(self):
        super().__init__()
        settings = get_settings()
        self.email = settings.PRIMA_EMAIL
        self.password = settings.PRIMA_PASSWORD

    def run(self):
        """Login to Taxitronic cloud portal and download shift CSV."""
        output_path = self.get_output_path("prima")

        if os.path.exists(output_path):
            print(f"Already downloaded: {output_path}")
            return output_path

        def scrape(page):
            # Navigate to Taxitronic cloud portal
            page.goto("https://cloud.taxitronic.com")
            page.wait_for_timeout(2000)

            # Login
            page.fill('input[name="username"]', self.email)
            page.fill('input[name="password"]', self.password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

            # Navigate to shift history
            page.goto("https://cloud.taxitronic.com/shifts/history")
            page.wait_for_timeout(3000)

            # Select yesterday's date range
            # Note: Taxitronic's UI may change. These selectors may need updating.
            yesterday_str = self.yesterday.isoformat()
            page.fill('input[name="dateFrom"]', yesterday_str)
            page.fill('input[name="dateTo"]', yesterday_str)
            page.click('button:has-text("Search")')
            page.wait_for_timeout(2000)

            # Download CSV
            with page.expect_download() as download_info:
                page.click('button:has-text("Download CSV")')
            download = download_info.value
            download.save_as(output_path)

            return output_path

        return self.scrape_with_browser(scrape)


if __name__ == "__main__":
    scraper = PrimaScraper()
    result = scraper.run()
    print(f"Downloaded: {result}")
