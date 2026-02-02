"""FreeNow driver portal scraper."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper
from src.config import get_settings


class FreeNowScraper(BaseScraper):
    """Scrape trip data from portal.free-now.com."""

    def __init__(self):
        super().__init__()
        settings = get_settings()
        self.email = settings.FREENOW_EMAIL
        self.password = settings.FREENOW_PASSWORD

    def run(self):
        """Login to FreeNow driver portal and download trip CSV."""
        output_path = self.get_output_path("freenow")

        if os.path.exists(output_path):
            print(f"Already downloaded: {output_path}")
            return output_path

        def scrape(page):
            # Navigate to FreeNow driver portal
            page.goto("https://portal.free-now.com")
            page.wait_for_timeout(2000)

            # Login
            page.fill('input[name="email"]', self.email)
            page.fill('input[name="password"]', self.password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

            # Navigate to earnings/trip history
            page.goto("https://portal.free-now.com/driver/earnings")
            page.wait_for_timeout(3000)

            # Select yesterday's date range
            # Note: FreeNow's UI may change. These selectors may need updating.
            yesterday_str = self.yesterday.isoformat()
            page.fill('input[name="startDate"]', yesterday_str)
            page.fill('input[name="endDate"]', yesterday_str)
            page.click('button:has-text("Apply")')
            page.wait_for_timeout(2000)

            # Download CSV
            with page.expect_download() as download_info:
                page.click('button:has-text("Export")')
            download = download_info.value
            download.save_as(output_path)

            return output_path

        return self.scrape_with_browser(scrape)


if __name__ == "__main__":
    scraper = FreeNowScraper()
    result = scraper.run()
    print(f"Downloaded: {result}")
