import argparse
import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from tqdm import tqdm
from utils.converter import extract_content, to_markdown
from utils.logger import get_logger
from utils.scraper import Scraper
from utils.storage import get_file_path, save_file

logger = get_logger(__name__)


@dataclass
class CrawlerConfig:
    """크롤러 고유 설정을 담는 데이터 클래스"""

    name: str
    seed_url: str
    base_prefix: str
    temp_dir: str
    output_dir: str
    target_version: str
    selectors: list[str]
    exclusion_prefixes: list[str] = field(default_factory=list)
    concurrency_limit: int = 5


@dataclass
class CrawlSession:
    """실행 중인 크롤링 세션의 상태"""

    visited_urls: set[str] = field(default_factory=set)
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    success_count: int = 0
    failure_count: int = 0


class BaseCrawler:
    """재사용 가능한 크롤링 및 변환 엔진 핵심 클래스"""

    def __init__(self, config: CrawlerConfig):
        self.config = config

    async def run_crawl(self, clear: bool = False) -> None:
        """HTML 수집 프로세스 실행"""
        logger.info(
            f"[{self.config.name}] Starting crawl (concurrency={self.config.concurrency_limit})..."
        )

        if clear:
            temp_path = Path(self.config.temp_dir)
            if temp_path.exists():
                logger.info(f"Clearing temporary directory: {self.config.temp_dir}")
                shutil.rmtree(temp_path)

        scraper = Scraper(concurrency_limit=self.config.concurrency_limit)
        session = CrawlSession()

        normalized_seed = scraper.normalize_url(self.config.seed_url)
        await session.queue.put(normalized_seed)
        session.visited_urls.add(normalized_seed)

        pbar = tqdm(total=1, desc=f"{self.config.name} Crawl", unit="pg")

        async def worker() -> None:
            while True:
                try:
                    url = await session.queue.get()
                except asyncio.CancelledError:
                    break

                try:
                    html, final_url = await scraper.fetch_url(url)
                    if html:
                        # HTML 내부에 원본 URL 메타데이터 주입
                        soup = BeautifulSoup(html, "html.parser")
                        meta_tag = soup.new_tag(
                            "meta", attrs={"name": "source-url", "content": final_url}
                        )

                        if soup.head:
                            soup.head.insert(0, meta_tag)
                        else:
                            soup.insert(0, meta_tag)

                        html_with_meta = str(soup)

                        file_path = get_file_path(
                            self.config.temp_dir,
                            url,
                            extension=".html",
                            strip_prefix=urlparse(self.config.base_prefix).path,
                            seed_url=self.config.seed_url,
                        )
                        save_file(file_path, html_with_meta)
                        session.success_count += 1

                        # 링크 추출
                        for a_tag in soup.find_all("a", href=True):
                            href = str(a_tag["href"])
                            full_url = urljoin(final_url, href)
                            normalized_url = scraper.normalize_url(full_url)

                            if (
                                scraper.is_target_url(
                                    normalized_url,
                                    self.config.base_prefix,
                                    self.config.exclusion_prefixes,
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

        workers = [asyncio.create_task(worker()) for _ in range(self.config.concurrency_limit)]

        try:
            await session.queue.join()
        except Exception as e:
            logger.error(f"Error during queue processing: {e}")

        for w in workers:
            w.cancel()

        pbar.close()
        await scraper.close()
        logger.info(
            f"[{self.config.name}] Crawl completed. "
            f"OK: {session.success_count}, ERR: {session.failure_count}"
        )

    async def run_convert(self, clear: bool = False) -> None:
        """HTML -> Markdown 변환 프로세스 실행"""
        logger.info(
            f"[{self.config.name}] Starting conversion (version={self.config.target_version})..."
        )

        if clear:
            output_path = Path(self.config.output_dir)
            if output_path.exists():
                logger.info(f"Clearing output directory: {self.config.output_dir}")
                shutil.rmtree(output_path)

        temp_path = Path(self.config.temp_dir)
        if not temp_path.exists():
            logger.error(f"Temp dir not found: {self.config.temp_dir}. Run crawl first.")
            return

        html_files = list(temp_path.glob("**/*.html"))
        logger.info(f"Found {len(html_files)} files to convert.")

        success_count = 0
        failure_count = 0

        for html_file in tqdm(html_files, desc=f"{self.config.name} Convert", unit="file"):
            try:
                html = html_file.read_text(encoding="utf-8")
                soup = BeautifulSoup(html, "html.parser")

                # HTML 메타 태그로부터 원본 URL 복원
                meta_tag = soup.find("meta", attrs={"name": "source-url"})
                if meta_tag and meta_tag.get("content"):
                    source_url = str(meta_tag.get("content"))
                else:
                    # 메타 태그가 없는 경우 기존 파일명 기반 추측 (하위 호환성)
                    relative_path = html_file.relative_to(temp_path)
                    url_path = str(relative_path).replace("\\", "/")
                    if "_root_.html" in url_path:
                        url_path = url_path.replace("_root_.html", "")
                    source_url = urljoin(self.config.base_prefix, url_path)

                content_html = extract_content(html, selectors=self.config.selectors)
                md_content = to_markdown(
                    content_html,
                    source_url,
                    target_version=self.config.target_version,
                )

                output_file = get_file_path(
                    self.config.output_dir,
                    source_url,
                    extension=".md",
                    strip_prefix=urlparse(self.config.base_prefix).path,
                    seed_url=self.config.seed_url,
                )
                save_file(output_file, md_content)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to convert {html_file}: {e}")
                failure_count += 1

        logger.info(
            f"[{self.config.name}] Conversion completed. OK: {success_count}, ERR: {failure_count}"
        )

    @classmethod
    async def main_entry(cls, default_config: CrawlerConfig, description: str) -> None:
        """CLI 진입점 통합 메서드"""
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        subparsers = parser.add_subparsers(dest="command", help="실행할 명령어를 선택하세요")

        # 공통 옵션 정의
        common_parser = argparse.ArgumentParser(add_help=False)
        common_parser.add_argument(
            "-c",
            "--concurrency",
            type=int,
            default=default_config.concurrency_limit,
            help="동시 HTTP 요청 수 제한",
        )
        common_parser.add_argument(
            "-v",
            "--version",
            type=str,
            default=default_config.target_version,
            help="대상 문서의 버전 (마크다운 메타데이터에 저장됨)",
        )
        common_parser.add_argument(
            "--clear",
            action="store_true",
            help="실행 전 출력 폴더(temp 또는 data_sources)를 삭제하여 초기화",
        )

        # 개별 명령어 등록
        subparsers.add_parser(
            "crawl",
            parents=[common_parser],
            help="웹사이트로부터 HTML 문서를 재귀적으로 수집하여 임시 폴더에 저장합니다.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        subparsers.add_parser(
            "convert",
            parents=[common_parser],
            help="수집된 HTML을 분석하여 본문을 추출하고 마크다운으로 변환합니다.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        subparsers.add_parser(
            "all",
            parents=[common_parser],
            help="수집(crawl)과 변환(convert) 과정을 순차적으로 모두 실행합니다.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        args = parser.parse_args()
        if not args.command:
            args.command = "all"

        # 명령줄 인자로 설정 업데이트
        default_config.concurrency_limit = args.concurrency
        default_config.target_version = args.version

        crawler = cls(default_config)

        if args.command in ["crawl", "all"]:
            await crawler.run_crawl(clear=args.clear)
        if args.command in ["convert", "all"]:
            await crawler.run_convert(clear=args.clear)
