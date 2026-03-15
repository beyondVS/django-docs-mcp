import httpx
import pytest
import respx

from crawler.utils.scraper import Scraper


@pytest.mark.asyncio
async def test_scraper_success():
    scraper = Scraper()
    url = "https://example.com"
    with respx.mock:
        respx.get(url).respond(200, text="Success")
        result = await scraper.fetch_url(url)
        assert result == "Success"
    await scraper.close()


@pytest.mark.asyncio
async def test_scraper_retry_on_error():
    scraper = Scraper()
    url = "https://example.com/error"
    with respx.mock:
        route = respx.get(url)
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, text="Recovered"),
        ]
        result = await scraper.fetch_url(url)
        assert result == "Recovered"
        assert route.call_count == 3
    await scraper.close()
