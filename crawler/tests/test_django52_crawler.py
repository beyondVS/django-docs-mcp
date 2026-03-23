import argparse

import httpx
import pytest
import respx
from django52_crawler import CrawlerConfig, crawl


@pytest.mark.asyncio
async def test_crawl_integration() -> None:
    config = CrawlerConfig(
        seed_url="https://docs.djangoproject.com/en/5.2/",
        temp_dir=".temp/test-crawl",
        concurrency_limit=2,
    )

    # Mocking
    async with respx.mock:
        # Seed page
        respx.get("https://docs.djangoproject.com/en/5.2/").mock(
            return_value=httpx.Response(
                200,
                content='<article id="docs-content"><a href="topics/">Topics</a></article>',
                headers={"content-type": "text/html"},
            )
        )
        # Topics page
        respx.get("https://docs.djangoproject.com/en/5.2/topics/").mock(
            return_value=httpx.Response(
                200,
                content='<article id="docs-content"><h1>Topics</h1></article>',
                headers={"content-type": "text/html"},
            )
        )

        args = argparse.Namespace(concurrency=2, version="5.2", clear=True)
        await crawl(args, config)

        # Check files
        import os

        assert os.path.exists(".temp/test-crawl/index.html")
        assert os.path.exists(".temp/test-crawl/topics.html")

        # Cleanup
        import shutil

        shutil.rmtree(".temp/test-crawl")
