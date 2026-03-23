import argparse
import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from tqdm import tqdm
from utils.converter import extract_content, to_markdown
from utils.logger import get_logger
from utils.scraper import Scraper
from utils.storage import get_file_path, save_file

logger = get_logger(__name__)


@dataclass
class CrawlerConfig:
    """크롤러 설정 클래스"""

    seed_url: str = "https://docs.djangoproject.com/en/5.2/"
    base_prefix: str = "https://docs.djangoproject.com/en/5.2/"
    exclusion_prefixes: list[str] = field(
        default_factory=lambda: ["https://docs.djangoproject.com/en/5.2/releases/"]
    )
    concurrency_limit: int = 5
    temp_dir: str = ".temp/django-5.2-docs"
    output_dir: str = "../data_sources/django-5.2-docs"
    target_version: str = "5.2"


@dataclass
class CrawlSession:
    """크롤링 세션 상태 관리 클래스"""

    visited_urls: set[str] = field(default_factory=set)
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    success_count: int = 0
    failure_count: int = 0


async def crawl(args: argparse.Namespace, config: CrawlerConfig) -> None:
    """HTML 수집 명령 처리"""
    logger.info(f"Starting crawl with concurrency={args.concurrency}...")

    # T007: 시작 전 폴더 비우기
    if args.clear:
        temp_path = Path(config.temp_dir)
        if temp_path.exists():
            logger.info(f"Clearing temporary directory: {config.temp_dir}")
            shutil.rmtree(temp_path)

    scraper = Scraper(concurrency_limit=args.concurrency)
    session = CrawlSession()

    # 시작 URL 추가
    normalized_seed = scraper.normalize_url(config.seed_url)
    await session.queue.put(normalized_seed)
    session.visited_urls.add(normalized_seed)

    pbar = tqdm(total=1, desc="Crawling", unit="pg")

    async def worker() -> None:
        while True:
            try:
                url = await session.queue.get()
            except asyncio.CancelledError:
                break

            try:
                html, final_url = await scraper.fetch_url(url)
                if html:
                    # T006: 항상 덮어쓰기 저장
                    # 저장 경로는 요청한 URL 구조를 따름 (일관성 유지)
                    file_path = get_file_path(config.temp_dir, url, extension=".html")
                    save_file(file_path, html)
                    session.success_count += 1

                    # 링크 추출 및 큐 추가
                    soup = BeautifulSoup(html, "html.parser")
                    for a_tag in soup.find_all("a", href=True):
                        href = str(a_tag["href"])
                        # 중요: 리다이렉션된 최종 URL을 베이스로 사용하여 상대 경로 결합
                        full_url = urljoin(final_url, href)
                        normalized_url = scraper.normalize_url(full_url)

                        if (
                            scraper.is_target_url(
                                normalized_url,
                                config.base_prefix,
                                config.exclusion_prefixes,
                            )
                            and normalized_url not in session.visited_urls
                        ):
                            session.visited_urls.add(normalized_url)
                            await session.queue.put(normalized_url)
                            pbar.total += 1
                else:
                    session.failure_count += 1
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                session.failure_count += 1
            finally:
                pbar.set_postfix(ok=session.success_count, err=session.failure_count)
                pbar.update(1)
                session.queue.task_done()

    # 동시성 제한에 따른 워커 생성
    workers = [asyncio.create_task(worker()) for _ in range(config.concurrency_limit)]

    # 큐가 비워질 때까지 대기
    try:
        await session.queue.join()
    except Exception as e:
        logger.error(f"Error during queue processing: {e}")

    # 워커 종료
    for w in workers:
        w.cancel()

    pbar.close()
    await scraper.close()
    logger.info(
        f"Crawl completed. Success: {session.success_count}, Failure: {session.failure_count}"
    )


async def convert(args: argparse.Namespace, config: CrawlerConfig) -> None:
    """마크다운 변환 명령 처리"""
    logger.info(f"Starting conversion for version {config.target_version}...")

    # T007: 시작 전 폴더 비우기
    if args.clear:
        output_path = Path(config.output_dir)
        if output_path.exists():
            logger.info(f"Clearing output directory: {config.output_dir}")
            shutil.rmtree(output_path)

    temp_path = Path(config.temp_dir)
    if not temp_path.exists():
        logger.error(f"Temporary directory not found: {config.temp_dir}. Please run 'crawl' first.")
        return

    # HTML 파일 탐색
    html_files = list(temp_path.glob("**/*.html"))
    logger.info(f"Found {len(html_files)} HTML files to convert.")

    success_count = 0
    failure_count = 0

    # 선택자 설정 (명세: <article id="docs-content"> 또는 <main id="main-content">)
    selectors = ["article#docs-content", "main#main-content"]

    for html_file in tqdm(html_files, desc="Converting", unit="file"):
        try:
            # 상대 경로를 기반으로 원본 URL 재구성
            relative_path = html_file.relative_to(temp_path)
            url_path = str(relative_path).replace("\\", "/")
            url_path = "" if url_path == "index.html" else url_path.replace(".html", "/")

            source_url = urljoin(config.base_prefix, url_path)

            html = html_file.read_text(encoding="utf-8")

            # 본문 추출
            content_html = extract_content(html, selectors=selectors)

            # 마크다운 변환
            md_content = to_markdown(content_html, source_url, target_version=config.target_version)

            # 저장
            output_file = get_file_path(config.output_dir, source_url, extension=".md")
            save_file(output_file, md_content)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to convert {html_file}: {e}")
            failure_count += 1

    logger.info(f"Conversion completed. Success: {success_count}, Failure: {failure_count}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Django 5.2 Documentation Crawler & Converter")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Common options
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-c", "--concurrency", type=int, default=5, help="Max concurrent requests"
    )
    common_parser.add_argument(
        "-v", "--version", type=str, default="5.2", help="Target Django version"
    )
    common_parser.add_argument(
        "--clear", action="store_true", help="Clear output directory before starting"
    )

    # Crawl command
    subparsers.add_parser("crawl", parents=[common_parser], help="Crawl HTML from Django docs")

    # Convert command
    subparsers.add_parser(
        "convert", parents=[common_parser], help="Convert collected HTML to Markdown"
    )

    # All command (default)
    subparsers.add_parser("all", parents=[common_parser], help="Crawl and then Convert")

    args = parser.parse_args()
    if not args.command:
        args.command = "all"

    config = CrawlerConfig(concurrency_limit=args.concurrency, target_version=args.version)

    if args.command in ["crawl", "all"]:
        await crawl(args, config)

    if args.command in ["convert", "all"]:
        await convert(args, config)


if __name__ == "__main__":
    asyncio.run(main())
