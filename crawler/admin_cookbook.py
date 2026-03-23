import asyncio

from utils.base_crawler import BaseCrawler, CrawlerConfig


async def main() -> None:
    config = CrawlerConfig(
        name="Admin Cookbook",
        seed_url="https://books.agiliq.com/projects/django-admin-cookbook/en/latest/",
        base_prefix="https://books.agiliq.com/projects/django-admin-cookbook/en/latest/",
        temp_dir=".temp/django-admin-cookbook",
        output_dir="../data_sources/django-admin-cookbook",
        target_version="2.x",
        selectors=['[role="main"]', ".document", "article", ".section"],
    )
    await BaseCrawler.main_entry(config, "Django Admin Cookbook Crawler & Converter")


if __name__ == "__main__":
    asyncio.run(main())
