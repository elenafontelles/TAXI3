"""Discovery script for Prima (Taxitronic) portal - ASP.NET WebForms app."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from src.config import get_settings

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

PORTAL_URL = "https://prima.taxitronic.com"
LOGIN_PAGE = f"{PORTAL_URL}/Login.aspx"
SERVICES_PAGE = f"{PORTAL_URL}/pantallas/ConsultaTurnos.aspx"


def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"prima_{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")


def dump_inputs(page):
    """Print all input elements on the page."""
    inputs = page.query_selector_all("input")
    for inp in inputs:
        name = inp.get_attribute("name") or ""
        type_ = inp.get_attribute("type") or ""
        id_ = inp.get_attribute("id") or ""
        value = inp.get_attribute("value") or ""
        if type_ == "hidden" and len(value) > 50:
            value = value[:50] + "..."
        print(f"   <input name='{name}' type='{type_}' id='{id_}' value='{value}'>")

    for tag in ["button", "input[type='submit']", "input[type='image']"]:
        els = page.query_selector_all(tag)
        for el in els:
            name = el.get_attribute("name") or ""
            id_ = el.get_attribute("id") or ""
            title = el.get_attribute("title") or ""
            src = el.get_attribute("src") or ""
            print(f"   <{tag} name='{name}' id='{id_}' title='{title}' src='{src}'>")

    selects = page.query_selector_all("select")
    for sel in selects:
        name = sel.get_attribute("name") or ""
        id_ = sel.get_attribute("id") or ""
        options = sel.query_selector_all("option")
        opt_texts = [o.inner_text().strip()[:30] for o in options[:10]]
        print(f"   <select name='{name}' id='{id_}'> options={opt_texts}")


def run():
    settings = get_settings()
    email = settings.PRIMA_EMAIL
    password = settings.PRIMA_PASSWORD

    if not email or not password:
        print("ERROR: PRIMA_EMAIL and PRIMA_PASSWORD must be set in .env")
        return

    print(f"Using email: {email}")

    with sync_playwright() as p:
        # Launch headed (visible) browser with real user-agent
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            accept_downloads=True,
        )
        page = context.new_page()

        try:
            # Step 1: Load login page directly
            print("1. Loading Login.aspx...")
            page.goto(LOGIN_PAGE, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            screenshot(page, "01_login_page")
            print(f"   URL: {page.url}")
            print(f"   Title: {page.title()}")

            # Dump all form elements
            print("   Form elements:")
            dump_inputs(page)

            # Step 2: Try to login
            print("2. Logging in...")
            # Fill first text input and first password input found
            text_input = page.query_selector('input[type="text"]')
            pw_input = page.query_selector('input[type="password"]')
            if text_input:
                print(f"   Filling text input: name='{text_input.get_attribute('name')}' id='{text_input.get_attribute('id')}'")
                text_input.fill(email)
            else:
                print("   WARNING: No text input found!")
            if pw_input:
                print(f"   Filling password input: name='{pw_input.get_attribute('name')}' id='{pw_input.get_attribute('id')}'")
                pw_input.fill(password)
            else:
                print("   WARNING: No password input found!")

            # Click "Entrar" link button (ASP.NET LinkButton: <a id="btnLogin">)
            print("   Clicking #btnLogin...")
            page.click('#btnLogin', timeout=10000)

            page.wait_for_timeout(5000)
            screenshot(page, "02_after_login")
            print(f"   URL after login: {page.url}")
            print(f"   Title: {page.title()}")

            # Step 3: Navigate to ConsultaTurnos
            print("3. Navigating to ConsultaTurnos...")
            page.goto(SERVICES_PAGE, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            screenshot(page, "03_consulta_turnos")
            print(f"   URL: {page.url}")
            print(f"   Title: {page.title()}")

            # Step 4: Dump all form elements on services page
            print("4. ConsultaTurnos form elements:")
            dump_inputs(page)

            # Step 5: Check for the known export button
            export_btn = page.query_selector('#ctl00_ContentPlaceHolder1_ButtonExportServicios')
            if export_btn:
                print("5. FOUND export button: #ctl00_ContentPlaceHolder1_ButtonExportServicios")
            else:
                print("5. Export button NOT FOUND - listing all image inputs:")
                img_btns = page.query_selector_all("input[type='image']")
                for btn in img_btns:
                    name = btn.get_attribute("name") or ""
                    title = btn.get_attribute("title") or ""
                    src = btn.get_attribute("src") or ""
                    print(f"   <input type='image' name='{name}' title='{title}' src='{src}'>")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            screenshot(page, "99_error")
        finally:
            browser.close()

    print("\nDone! Check screenshots in:", SCREENSHOT_DIR)


if __name__ == "__main__":
    run()
