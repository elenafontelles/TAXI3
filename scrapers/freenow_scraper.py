"""FreeNow booking-history scraper - downloads CSV via Playwright."""
import argparse
import os
import sys
import zipfile
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper
from src.config import get_settings


class FreeNowScraper(BaseScraper):
    """Scrape booking CSV from portal.free-now.com/booking-history.

    Flow: login → booking-history → set dates → click "Request bookings"
    → wait for notification → click "Download" in notification → extract ZIP.
    """

    PORTAL_URL = "https://portal.free-now.com"

    def __init__(self, start_date: date | None = None, end_date: date | None = None):
        super().__init__()
        settings = get_settings()
        self.email = settings.FREENOW_EMAIL
        self.password = settings.FREENOW_PASSWORD
        self.start_date = start_date or self.yesterday
        self.end_date = end_date or self.yesterday

    def run(self) -> str | None:
        """Login, set date range, request and download CSV. Returns path or None."""
        if not self.email or not self.password:
            print("ERROR: FREENOW_EMAIL and FREENOW_PASSWORD must be set in .env")
            return None

        tag = (f"{self.start_date.isoformat()}_to_{self.end_date.isoformat()}"
               if self.start_date != self.end_date
               else self.start_date.isoformat())
        output_path = os.path.join(self.imports_dir, f"freenow_{tag}.csv")

        if os.path.exists(output_path):
            print(f"Already downloaded: {output_path}")
            return output_path

        def scrape(page):
            # 1) Login
            print("1. Logging in...")
            page.goto(self.PORTAL_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector('input[name="username"]', timeout=15000)
            page.fill('input[name="username"]', self.email)
            page.fill('input[name="password"]', self.password)
            page.click('button:has-text("Sign in")')
            page.wait_for_timeout(4000)
            print(f"   Logged in -> {page.url}")

            # 2) Dismiss cookie banner if present
            cookie_btn = page.query_selector('button:has-text("Accept All")')
            if cookie_btn:
                cookie_btn.click()
                page.wait_for_timeout(500)

            # 3) Navigate to booking history
            print("2. Opening booking history...")
            page.goto(f"{self.PORTAL_URL}/booking-history",
                      wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('[data-testid="start-date-input"]', timeout=15000)
            page.wait_for_timeout(2000)

            # 4) Set date range (DD/MM/YYYY format)
            start_str = self.start_date.strftime("%d/%m/%Y")
            end_str = self.end_date.strftime("%d/%m/%Y")
            print(f"3. Setting date range: {start_str} - {end_str}")

            start_input = page.locator('[data-testid="start-date-input"]')
            start_input.click(click_count=3)
            start_input.type(start_str, delay=50)
            page.keyboard.press("Tab")

            end_input = page.locator('[data-testid="end-date-input"]')
            end_input.click(click_count=3)
            end_input.type(end_str, delay=50)
            page.keyboard.press("Tab")

            # Wait for table data to reload after date change
            page.wait_for_timeout(3000)

            # 5) Check if download button is enabled (has data)
            dl_btn = page.locator('[data-testid="booking-history-download-button"]')
            is_disabled = dl_btn.get_attribute("disabled") is not None
            if is_disabled:
                # Wait a bit more in case still loading
                page.wait_for_timeout(5000)
                is_disabled = dl_btn.get_attribute("disabled") is not None
            if is_disabled:
                print("   No bookings found for this date range (button disabled)")
                return None

            # 6) Record notification badge count before requesting
            notif_btn = page.query_selector('[aria-label="Open Notifications Inbox"]')
            badge_before = notif_btn.inner_text().strip() if notif_btn else "0"

            # 7) Click "Request bookings" button
            print("4. Requesting CSV generation...")
            dl_btn.click()
            page.wait_for_timeout(2000)

            # 8) Wait for notification badge to change (file ready)
            print("5. Waiting for file to be ready...")
            for attempt in range(30):  # max ~60 seconds
                page.wait_for_timeout(2000)
                badge_now = notif_btn.inner_text().strip() if notif_btn else "0"
                if badge_now != badge_before:
                    print(f"   Ready! (badge {badge_before} -> {badge_now})")
                    break
            else:
                print("   Timeout waiting for notification, trying anyway...")

            # 9) Open notification inbox and click the first "Download" link
            print("6. Downloading from notifications...")
            notif_btn.click()
            page.wait_for_timeout(2000)

            # The notification panel has <a> tags with text "Download"
            download_links = page.locator('a:has-text("Download")')
            zip_path = output_path + ".zip"

            with page.expect_download(timeout=30000) as download_info:
                download_links.first.click()
            download = download_info.value
            download.save_as(zip_path)
            print(f"   Downloaded ZIP: {zip_path}")

            # 10) Extract CSV from ZIP
            with zipfile.ZipFile(zip_path, "r") as zf:
                csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
                if not csv_names:
                    print("   ERROR: No CSV found in ZIP")
                    return None
                zf.extract(csv_names[0], self.imports_dir)
                extracted = os.path.join(self.imports_dir, csv_names[0])
                os.rename(extracted, output_path)
            os.remove(zip_path)
            print(f"   Extracted CSV: {output_path}")
            return output_path

        return self.scrape_with_browser(scrape)


def main():
    parser = argparse.ArgumentParser(description="Download FreeNow booking CSV")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: same as start)")
    args = parser.parse_args()

    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None
    if start and not end:
        end = start

    scraper = FreeNowScraper(start_date=start, end_date=end)
    result = scraper.run()
    if result:
        print(f"\nDone! CSV at: {result}")
    else:
        print("\nFailed to download CSV")
        sys.exit(1)


if __name__ == "__main__":
    main()
