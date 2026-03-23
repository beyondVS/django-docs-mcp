import asyncio

from utils.base_crawler import BaseCrawler, CrawlerConfig


async def main() -> None:
    config = CrawlerConfig(
        name="Django 5.2 Docs",
        seed_url="https://docs.djangoproject.com/en/5.2/",
        base_prefix="https://docs.djangoproject.com/en/5.2/",
        exclusion_prefixes=["https://docs.djangoproject.com/en/5.2/releases/"],
        temp_dir=".temp/django-5.2-docs",
        output_dir="../data_sources/django-5.2-docs",
        target_version="5.2",
        selectors=["article#docs-content", "main#main-content"],
    )
    await BaseCrawler.main_entry(config, "Django 5.2 Documentation Crawler & Converter")


if __name__ == "__main__":
    asyncio.run(main())
