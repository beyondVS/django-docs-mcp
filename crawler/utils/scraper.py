import asyncio
import logging

import httpx
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from crawler.utils.logger import get_logger

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

    async def close(self):
        """HTTP 클라이언트 자원을 정리합니다."""
        await self.client.aclose()

    async def fetch_url(self, url: str) -> str:
        """
        지수 백오프 기반의 재시도 로직을 사용하여 URL의 내용을 가져옵니다.

        Args:
            url (str): 가져올 웹페이지의 URL.

        Returns:
            str: 응답받은 HTML 텍스트. 실패 시 빈 문자열을 반환합니다.
        """
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
                    return response.text
        return ""
