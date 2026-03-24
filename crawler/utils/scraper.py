import asyncio
import logging
from urllib.parse import urlparse

import httpx
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class Scraper:
    def __init__(self, concurrency_limit: int = 5):
        """
        Scraper 초기화 메서드.

        Args:
            concurrency_limit (int): 동시 요청 수 제한. 기본값은 5.
        """
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    @staticmethod
    def normalize_url(url: str) -> str:
        """URL을 정규화합니다. (Fragment/Query 제거)"""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        # 스키마, 도메인, 경로만 유지하여 반환 (슬래시 강제 추가 제거)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def is_target_url(self, url: str, base_prefix: str, exclusion_prefixes: list[str]) -> bool:
        """크롤링 대상 도메인 및 경로인지 확인합니다."""
        clean_base = base_prefix.rstrip("/")
        if not url.startswith(clean_base):
            return False

        return all(not url.startswith(exclusion) for exclusion in exclusion_prefixes)

    async def close(self) -> None:
        """HTTP 클라이언트 자원을 정리합니다."""
        await self.client.aclose()

    async def fetch_url(self, url: str) -> tuple[str, str]:
        """
        URL의 내용을 가져오고 최종 응답 URL을 반환합니다.

        Returns:
            tuple[str, str]: (HTML 텍스트, 최종 응답 URL). 실패 시 ("", "") 반환.
        """
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(5),
                wait=wait_exponential(multiplier=1, min=2, max=30),
                retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
                before_sleep=before_sleep_log(logger, logging.WARNING),
            ):
                with attempt:
                    async with self.semaphore:
                        logger.info(f"Fetching: {url}")
                        response = await self.client.get(url)
                        response.raise_for_status()

                        final_url = str(response.url)
                        content_type = response.headers.get("content-type", "")
                        if "text/html" not in content_type:
                            return "", final_url

                        return response.text, final_url
        except Exception as e:
            logger.error(f"Failed to fetch {url} after retries: {e}")
        return "", ""
