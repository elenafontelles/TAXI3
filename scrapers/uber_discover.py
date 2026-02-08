"""Discovery script for Uber Supplier portal - uses existing Chrome profile."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Start at home page, navigate via menu
HOME_URL = "https://supplier.uber.com/"

# Path to Chrome user data (where your session cookies are)
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")


def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"uber_{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def dump_elements(page):
    """Print interactive elements on the page."""
    # Buttons
    buttons = page.query_selector_all("button")
    print(f"  Buttons ({len(buttons)}):")
    for btn in buttons[:15]:
        text = btn.inner_text().strip()[:50] if btn.inner_text() else ""
        aria = btn.get_attribute("aria-label") or ""
        data_baseweb = btn.get_attribute("data-baseweb") or ""
        print(f"    <button> '{text}' | aria='{aria}' | baseweb='{data_baseweb}'")

    # Inputs
    inputs = page.query_selector_all("input")
    print(f"  Inputs ({len(inputs)}):")
    for inp in inputs[:10]:
        type_ = inp.get_attribute("type") or ""
        name = inp.get_attribute("name") or ""
        placeholder = inp.get_attribute("placeholder") or ""
        value = inp.get_attribute("value") or ""
        print(f"    <input type='{type_}' name='{name}' placeholder='{placeholder}' value='{value[:30]}'>")

    # Links
    links = page.query_selector_all("a")
    print(f"  Links ({len(links)}):")
    for link in links[:20]:
        text = link.inner_text().strip()[:40] if link.inner_text() else ""
        href = link.get_attribute("href") or ""
        print(f"    <a> '{text}' href='{href[:60]}'")

    # Date-like divs
    date_divs = page.query_selector_all("[data-baseweb='typo-labelmedium'], [data-baseweb='typo-labelsmall']")
    print(f"  Date-like divs ({len(date_divs)}):")
    for div in date_divs[:10]:
        text = div.inner_text().strip()[:60] if div.inner_text() else ""
        print(f"    '{text}'")


def run():
    print("=" * 60)
    print("UBER SUPPLIER PORTAL DISCOVERY")
    print("Using your existing Chrome profile (with session)")
    print("=" * 60)
    print("\nIMPORTANT: Close Chrome completely before running this!")
    print("(Playwright needs exclusive access to the profile)\n")

    with sync_playwright() as p:
        # Launch Chrome using your existing profile
        browser = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_USER_DATA,
            channel="chrome",  # Use installed Chrome
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="es-ES",
        )

        # Get the first page or create one
        if browser.pages:
            page = browser.pages[0]
        else:
            page = browser.new_page()

        try:
            # Step 1: Go to supplier home page
            print("1. Opening Uber Supplier home page...")
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            screenshot(page, "01_home")
            print(f"   URL: {page.url}")

            # Check if we're logged in
            if "auth.uber.com" in page.url:
                print("\n   NOT LOGGED IN - you need to login in Chrome first")
                print("   Open Chrome manually, go to supplier.uber.com, login")
                print("   Then close Chrome and run this script again")
                return

            # Step 2: Click on "Ganancias" in navigation
            print("\n2. Looking for 'Ganancias' link...")
            ganancias_link = page.query_selector("a:has-text('Ganancias')")
            if ganancias_link:
                print("   Found 'Ganancias' link - clicking...")
                ganancias_link.click()
                page.wait_for_timeout(5000)
                screenshot(page, "02_ganancias")
                print(f"   URL after click: {page.url}")
            else:
                print("   Ganancias link not found, trying direct navigation...")
                # Try clicking on navigation items
                dump_elements(page)

            # Step 3: Analyze the Ganancias page
            print("\n3. Analyzing Ganancias page elements...")
            dump_elements(page)

            # Step 4: Look for date range selector
            print("\n4. Looking for date range selector...")
            # Look for date-related elements
            date_elements = page.query_selector_all("[data-testid*='date'], [class*='date'], input[type='date']")
            print(f"   Found {len(date_elements)} date-related elements")

            # Look for any clickable date display
            date_display = page.query_selector("[data-baseweb='typo-labelmedium']")
            if date_display:
                date_text = date_display.inner_text()
                print(f"   Date display: '{date_text}'")
                print("   Clicking on date display...")
                date_display.click()
                page.wait_for_timeout(2000)
                screenshot(page, "03_date_picker_open")
                dump_elements(page)

            # Step 5: Look for driver earnings table/rows
            print("\n5. Looking for driver earnings data...")
            # Find rows with amounts or driver names
            rows = page.query_selector_all("tr, [role='row'], [data-testid*='row']")
            print(f"   Found {len(rows)} table rows")

            # Look for specific driver
            ivan_elements = page.query_selector_all("text=Ivan")
            print(f"   Found {len(ivan_elements)} elements containing 'Ivan'")
            for el in ivan_elements[:5]:
                text = el.inner_text().strip()[:80] if el.inner_text() else ""
                print(f"     '{text}'")

            # Step 6: Try to find expandable rows
            print("\n6. Looking for expandable rows or details...")
            expandable = page.query_selector_all("[aria-expanded], [data-expanded], svg[class*='chevron'], svg[class*='arrow']")
            print(f"   Found {len(expandable)} expandable elements")

            # Click on first driver row if visible
            driver_row = page.query_selector("text=IVAN ALSINA")
            if driver_row:
                print("   Found 'IVAN ALSINA' - clicking...")
                driver_row.click()
                page.wait_for_timeout(2000)
                screenshot(page, "04_driver_expanded")
                dump_elements(page)

            # Step 7: Look for download/export button
            print("\n7. Looking for export/download options...")
            export_btns = page.query_selector_all("button:has-text('Descargar'), button:has-text('Exportar'), button:has-text('CSV'), a:has-text('Descargar')")
            print(f"   Found {len(export_btns)} export buttons")
            for btn in export_btns:
                text = btn.inner_text().strip() if btn.inner_text() else ""
                print(f"     '{text}'")

            # Step 8: Final screenshot
            print("\n8. Taking final screenshot...")
            page.wait_for_timeout(2000)
            screenshot(page, "05_final")

            # Print page HTML structure for debugging
            print("\n9. Page structure (first 2000 chars of body)...")
            body_html = page.inner_html("body")[:2000]
            print(body_html)

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            screenshot(page, "99_error")
        finally:
            print("\nClosing browser...")
            browser.close()

    print(f"\nDone! Check screenshots in: {SCREENSHOT_DIR}")


if __name__ == "__main__":
    run()
