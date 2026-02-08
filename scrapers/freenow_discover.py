"""Discovery script for FreeNow booking-history page."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from src.config import get_settings

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def run():
    settings = get_settings()
    email = settings.FREENOW_EMAIL
    password = settings.FREENOW_PASSWORD

    if not email or not password:
        print("ERROR: FREENOW_EMAIL and FREENOW_PASSWORD must be set in .env")
        return

    print(f"Using email: {email}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        try:
            # Step 1: Login
            print("1. Logging in...")
            page.goto("https://portal.free-now.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector('input[name="username"]', timeout=15000)
            page.fill('input[name="username"]', email)
            page.fill('input[name="password"]', password)
            page.click('button:has-text("Sign in")')
            page.wait_for_timeout(5000)
            screenshot(page, "01_logged_in")
            print(f"   URL: {page.url}")

            # Step 2: Navigate to booking-history
            print("2. Navigating to /booking-history...")
            page.goto("https://portal.free-now.com/booking-history",
                       wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            screenshot(page, "02_booking_history")
            print(f"   URL: {page.url}")

            # Step 3: Explore date inputs
            print("3. Looking for date inputs...")
            for testid in ["start-date-input", "end-date-input"]:
                el = page.query_selector(f'[data-testid="{testid}"]')
                if el:
                    val = el.get_attribute("value") or ""
                    print(f"   Found {testid}: value='{val}'")
                else:
                    print(f"   NOT FOUND: {testid}")

            # Step 4: Explore download button
            print("4. Looking for download button...")
            dl_btn = page.query_selector('[data-testid="booking-history-download-button"]')
            if dl_btn:
                print(f"   Found download button: aria-label='{dl_btn.get_attribute('aria-label')}'")
            else:
                print("   NOT FOUND: booking-history-download-button")

            # Step 5: Get notification badge count before requesting
            notif_btn = page.query_selector('[aria-label="Open Notifications Inbox"]')
            badge_before = notif_btn.inner_text().strip() if notif_btn else "0"
            print(f"5. Notification badge before: {badge_before}")

            # Step 6: Click download button to request CSV generation
            print("6. Requesting CSV generation...")
            page.click('[data-testid="booking-history-download-button"]')
            page.wait_for_timeout(2000)
            screenshot(page, "03_after_request")

            # Step 7: Wait for notification badge to increment (file ready)
            print("7. Waiting for file to be ready...")
            for attempt in range(30):
                page.wait_for_timeout(2000)
                badge_now = notif_btn.inner_text().strip() if notif_btn else "0"
                if badge_now != badge_before:
                    print(f"   Badge changed: {badge_before} -> {badge_now} (attempt {attempt+1})")
                    break
                if attempt % 5 == 0:
                    print(f"   Still waiting... (attempt {attempt+1}, badge={badge_now})")
            else:
                print("   Timeout waiting for notification, trying anyway...")

            # Step 8: Open notifications and click first Download link
            print("8. Opening notifications...")
            notif_btn.click()
            page.wait_for_timeout(2000)
            screenshot(page, "04_notifications_open")

            # Find all Download links in the notification panel
            download_links = page.query_selector_all('a:has-text("Download"), button:has-text("Download")')
            print(f"   Found {len(download_links)} download links")
            for i, dl in enumerate(download_links):
                tag = dl.evaluate("e => e.tagName.toLowerCase()")
                href = dl.get_attribute("href") or ""
                text = dl.inner_text().strip()[:40]
                print(f"   Link {i}: <{tag}> text='{text}' href='{href}'")

            # Click first download link and capture file
            if download_links:
                print("9. Clicking first Download link...")
                import tempfile
                dl_path = os.path.join(SCREENSHOT_DIR, "test_download.csv")
                try:
                    with page.expect_download(timeout=30000) as download_info:
                        download_links[0].click()
                    download = download_info.value
                    download.save_as(dl_path)
                    print(f"   Downloaded to: {dl_path}")
                    # Show first 5 lines
                    with open(dl_path, "r") as f:
                        for i, line in enumerate(f):
                            if i >= 5:
                                break
                            print(f"   Line {i}: {line.strip()[:120]}")
                except Exception as e:
                    print(f"   Download failed: {e}")
                    # Maybe it's a direct link - try getting href
                    href = download_links[0].get_attribute("href") or ""
                    print(f"   Link href: {href}")
                    screenshot(page, "05_download_attempt")

        except Exception as e:
            print(f"ERROR: {e}")
            screenshot(page, "99_error")
        finally:
            browser.close()

    print("\nDone! Check screenshots in:", SCREENSHOT_DIR)


if __name__ == "__main__":
    run()
