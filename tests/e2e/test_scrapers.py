"""Scraper tests - skipped by default (require real credentials)."""
import pytest


def test_scrapers_importable():
    from scrapers.base_scraper import BaseScraper
    from scrapers.uber_scraper import UberScraper
    from scrapers.freenow_scraper import FreeNowScraper
    from scrapers.prima_scraper import PrimaScraper
    assert BaseScraper is not None
    assert UberScraper is not None
    assert FreeNowScraper is not None
    assert PrimaScraper is not None


@pytest.mark.skip(reason="requires real Uber credentials")
def test_uber_scraper():
    from scrapers.uber_scraper import UberScraper
    scraper = UberScraper()
    result = scraper.run()
    assert result is not None


@pytest.mark.skip(reason="requires real FreeNow credentials")
def test_freenow_scraper():
    from scrapers.freenow_scraper import FreeNowScraper
    scraper = FreeNowScraper()
    result = scraper.run()
    assert result is not None


@pytest.mark.skip(reason="requires real Prima credentials")
def test_prima_scraper():
    from scrapers.prima_scraper import PrimaScraper
    scraper = PrimaScraper()
    result = scraper.run()
    assert result is not None
