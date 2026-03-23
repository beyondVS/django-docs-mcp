import asyncio

from utils.base_crawler import BaseCrawler, CrawlerConfig


async def main() -> None:
    config = CrawlerConfig(
        name="ORM Cookbook",
        seed_url="https://books.agiliq.com/projects/django-orm-cookbook/en/latest/",
        base_prefix="https://books.agiliq.com/projects/django-orm-cookbook/en/latest/",
        temp_dir=".temp/django-orm-cookbook",
        output_dir="../data_sources/django-orm-cookbook",
        target_version="2.x",
        selectors=['[role="main"]', ".document", "article", ".section"],
    )
    await BaseCrawler.main_entry(config, "Django ORM Cookbook Crawler & Converter")


if __name__ == "__main__":
    asyncio.run(main())
