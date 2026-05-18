"""Prima (Taxitronic) portal scraper - downloads Servicios CSV via Playwright."""
import argparse
import os
import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper
from src.config import get_settings

# Real user-agent required — Prima portal rejects default headless UA
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


class PrimaScraper(BaseScraper):
    """Scrape trip CSV from prima.taxitronic.com/pantallas/ConsultaTurnos.aspx.

    Flow: login → ConsultaTurnos → set date range → select all vehicles/drivers
    → click Buscar → click "Exportar Servicios" → download CSV.
    """

    PORTAL_URL = "https://prima.taxitronic.com"
    LOGIN_URL = f"{PORTAL_URL}/Login.aspx"
    SERVICES_URL = f"{PORTAL_URL}/pantallas/ConsultaTurnos.aspx"

    def __init__(self, start_date: date | None = None, end_date: date | None = None):
        super().__init__()
        settings = get_settings()
        self.email = settings.PRIMA_EMAIL
        self.password = settings.PRIMA_PASSWORD
        self.start_date = start_date or self.yesterday
        self.end_date = end_date or self.yesterday

    def scrape_with_browser(self, callback):
        """Override base to add user-agent (Prima rejects default headless UA)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                accept_downloads=True,
                locale="es-ES",
                user_agent=_USER_AGENT,
            )
            page = context.new_page()
            try:
                return callback(page)
            finally:
                browser.close()

    def run(self) -> str | None:
        """Login, set date range, download Servicios CSV. Returns path or None."""
        if not self.email or not self.password:
            print("ERROR: PRIMA_EMAIL and PRIMA_PASSWORD must be set in .env")
            return None

        tag = (f"{self.start_date.isoformat()}_to_{self.end_date.isoformat()}"
               if self.start_date != self.end_date
               else self.start_date.isoformat())
        output_path = os.path.join(self.imports_dir, f"prima_{tag}.csv")

        # Always re-download (no file cache) to get fresh data
        if os.path.exists(output_path):
            os.remove(output_path)

        def scrape(page):
            # 1) Login
            print("1. Logging in to Prima...")
            page.goto(self.LOGIN_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_selector('#txtUsuario', timeout=15000)
            page.fill('#txtUsuario', self.email)
            page.fill('#txtPassword', self.password)
            page.click('#btnLogin')
            page.wait_for_timeout(5000)
            print(f"   Logged in -> {page.url}")

            # Verify login succeeded (should redirect away from Login.aspx)
            if 'Login.aspx' in page.url:
                print("   ERROR: Login failed — still on Login.aspx")
                return None

            # 2) Navigate to ConsultaTurnos
            print("2. Opening ConsultaTurnos...")
            page.goto(self.SERVICES_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_selector('#ctl00_ContentPlaceHolder1_txTurnoDesde', timeout=15000)

            # 3) Set vehicle range to full (first → last option)
            print("3. Setting filters to all vehicles/drivers...")
            veh_desde = page.locator('#ctl00_ContentPlaceHolder1_dlVehiculoDesde')
            veh_hasta = page.locator('#ctl00_ContentPlaceHolder1_dlVehiculoHasta')
            veh_options = veh_desde.locator('option').all()
            if veh_options:
                first_val = veh_options[0].get_attribute('value')
                last_val = veh_options[-1].get_attribute('value')
                veh_desde.select_option(value=first_val)
                veh_hasta.select_option(value=last_val)

            # Set conductor range to full (first → last option)
            cond_desde = page.locator('#ctl00_ContentPlaceHolder1_dlConductorDesde')
            cond_hasta = page.locator('#ctl00_ContentPlaceHolder1_dlConductorHasta')
            cond_options = cond_desde.locator('option').all()
            if cond_options:
                first_val = cond_options[0].get_attribute('value')
                last_val = cond_options[-1].get_attribute('value')
                cond_desde.select_option(value=first_val)
                cond_hasta.select_option(value=last_val)

            # 4) Set date range (DD/MM/YYYY text inputs)
            #    ASP.NET AJAX CalendarExtender intercepts clicks — clear field,
            #    fill with Playwright, then trigger change events.
            start_str = self.start_date.strftime("%d/%m/%Y")
            end_str = self.end_date.strftime("%d/%m/%Y")
            print(f"4. Setting date range: {start_str} - {end_str}")

            # Clear and fill start date
            start_input = page.locator('#ctl00_ContentPlaceHolder1_txTurnoDesde')
            start_input.click()
            start_input.fill('')
            start_input.fill(start_str)
            start_input.dispatch_event('change')
            start_input.dispatch_event('blur')

            # Clear and fill end date
            end_input = page.locator('#ctl00_ContentPlaceHolder1_txTurnoHasta')
            end_input.click()
            end_input.fill('')
            end_input.fill(end_str)
            end_input.dispatch_event('change')
            end_input.dispatch_event('blur')

            # Wait for any ASP.NET postback
            page.wait_for_timeout(1000)

            # Verify values were set correctly
            actual_start = start_input.input_value()
            actual_end = end_input.input_value()
            print(f"   Verified: {actual_start} - {actual_end}")

            # 5) Click search (Buscar)
            print("5. Clicking Buscar...")
            page.click('#ctl00_ContentPlaceHolder1_btConsultar')
            page.wait_for_timeout(5000)

            # 6) Download Servicios CSV
            print("6. Downloading Servicios CSV...")
            with page.expect_download(timeout=30000) as download_info:
                page.click('#ctl00_ContentPlaceHolder1_ButtonExportServicios')
            download = download_info.value
            download.save_as(output_path)
            print(f"   Downloaded CSV: {output_path}")
            return output_path

        try:
            result = self.scrape_with_browser(scrape)
        except Exception as e:
            print(f"ERROR: Scrape failed: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None
        return result


def main():
    parser = argparse.ArgumentParser(description="Download Prima/Taxitronic trip CSV")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: same as start)")
    args = parser.parse_args()

    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None
    if start and not end:
        end = start

    scraper = PrimaScraper(start_date=start, end_date=end)
    result = scraper.run()
    if result:
        print(f"\nDone! CSV at: {result}")
    else:
        print("\nFailed to download CSV")
        sys.exit(1)


if __name__ == "__main__":
    main()
