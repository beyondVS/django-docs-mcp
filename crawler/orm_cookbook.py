import asyncio
import hashlib
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from utils.converter import extract_content, to_markdown
from utils.logger import get_logger
from utils.scraper import Scraper
from utils.storage import get_file_path, save_file

logger = get_logger(__name__)

BASE_URL = "https://books.agiliq.com/projects/django-orm-cookbook/en/latest/"
STORAGE_DIR = "../data_sources/django2-orm-cookbook"


async def crawl_book():
    """
    Django ORM Cookbook 문서를 수집하는 메인 크롤링 함수입니다.
    동시성을 제한하며 BFS(너비 우선 탐색) 방식으로 링크를 탐색합니다.
    """
    scraper = Scraper(concurrency_limit=5)
    visited = set()
    to_visit = {BASE_URL}
    content_hashes = set()

    logger.info(f"크롤링 시작: {BASE_URL}")

    while to_visit:
        # 다음 URL 배치를 가져옵니다 (최대 5개).
        current_batch = list(to_visit)[:5]
        to_visit.difference_update(current_batch)

        tasks = []
        for url in current_batch:
            if url in visited:
                continue
            visited.add(url)
            tasks.append(process_url(scraper, url, to_visit, visited, content_hashes))

        await asyncio.gather(*tasks)

    await scraper.close()
    logger.info("크롤링이 완료되었습니다.")


async def process_url(scraper, url, to_visit, visited, content_hashes):
    """
    개별 URL을 처리하여 내용을 추출, 변환 및 저장하고 새로운 링크를 발견합니다.

    Args:
        scraper (Scraper): 비동기 스크래퍼 인스턴스.
        url (str): 처리할 대상 URL.
        to_visit (set): 방문 예정인 URL 집합.
        visited (set): 이미 방문한 URL 집합.
        content_hashes (set): 중복 방지를 위한 콘텐츠 해시 집합.
    """
    try:
        html = await scraper.fetch_url(url)
        if not html:
            return

        # 중복 방지를 위해 콘텐츠의 해시값을 확인합니다.
        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        if content_hash in content_hashes:
            logger.info(f"중복된 콘텐츠가 발견되었습니다. 건너뜁니다: {url}")
            return
        content_hashes.add(content_hash)

        # 링크를 파싱합니다.
        soup = BeautifulSoup(html, "lxml")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            next_url = urljoin(url, href)
            # URL 정규화 (프래그먼트 제거)
            next_url, _ = next_url.split("#") if "#" in next_url else (next_url, "")

            # 도메인 체크 및 중복 방문 방지
            if next_url.startswith(BASE_URL) and next_url not in visited:
                to_visit.add(next_url)

        # 본문을 추출하고 마크다운으로 변환합니다.
        main_content = extract_content(html)
        markdown_content = to_markdown(main_content, url)

        # 파일로 저장합니다.
        file_path = get_file_path(STORAGE_DIR, url)
        save_file(file_path, markdown_content)
        logger.info(f"저장 완료: {file_path}")

    except Exception as e:
        logger.error(f"처리 실패: {url}, 오류: {e}")


if __name__ == "__main__":
    asyncio.run(crawl_book())
