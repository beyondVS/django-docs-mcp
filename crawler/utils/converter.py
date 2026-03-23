import re
from datetime import UTC, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_content(html: str, selectors: list[str] | None = None) -> str:
    """
    HTML에서 지정된 선택자를 기반으로 본문 내용을 추출합니다.

    Args:
        html (str): 원본 HTML 문자열.
        selectors (list[str]): 본문 선택자 리스트 (우선순위 순).

    Returns:
        str: 추출된 본문 HTML 문자열. 추출에 실패할 경우 body 또는 원본 HTML을 반환합니다.
    """
    soup = BeautifulSoup(html, "html.parser")

    if not selectors:
        selectors = ['[role="main"]', "main", "article", "#content"]

    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            # 불필요한 태그 제거 (예: 링크 앵커, 내비게이션 등 - 필요 시 추가)
            return str(element)

    # 최후의 수단: body 전체
    if soup.body:
        return str(soup.body)

    return html


def fix_links(soup: BeautifulSoup, base_url: str) -> None:
    """모든 <a> 및 <img> 태그의 상대 경로를 절대 URL로 변환합니다."""
    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        a["href"] = urljoin(base_url, href)

    for img in soup.find_all("img", src=True):
        src = str(img["src"])
        img["src"] = urljoin(base_url, src)


def to_markdown(html_content: str, source_url: str, target_version: str = "5.2") -> str:
    """
    HTML을 마크다운으로 변환하고 YAML Front Matter를 상단에 추가합니다.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 제목 추출 (첫 번째 h1)
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled"

    # 링크 보정
    fix_links(soup, source_url)

    # 마크다운으로 변환합니다.
    markdown_content = md(
        str(soup),
        strip=["script", "style"],
        heading_style="ATX",
    )

    # 과도한 줄바꿈을 정리합니다.
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    # 메타데이터를 생성합니다.
    collected_at = datetime.now(UTC).isoformat()
    metadata = f"""---
source_url: {source_url}
title: "{title}"
target_version: {target_version}
collected_at: {collected_at}
---

"""
    return metadata + markdown_content.strip() + "\n"
