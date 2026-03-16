from datetime import UTC, datetime

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from readability import Document
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_content(html: str) -> str:
    """
    HTML에서 본문 내용을 추출합니다.
    기술 문서에 특화된 BeautifulSoup 선택자 기반 로직을 우선 사용하며,
    실패할 경우 Readability-lxml을 폴백으로 사용합니다.

    Args:
        html (str): 원본 HTML 문자열.

    Returns:
        str: 추출된 본문 HTML 문자열. 추출에 실패할 경우 body 또는 원본 HTML을 반환합니다.
    """
    soup = BeautifulSoup(html, "lxml")

    # 1. 명시적인 본문 선택자 시도 (최우선)
    # 노이즈 제거 (네비게이션, 푸터 등)
    for noise in soup.select("nav, footer, header, .sidebar, .related, .footer"):
        noise.decompose()

    # 본문 선택자 후보 (우선순위 순)
    selectors = [
        '[role="main"]',
        '[itemprop="articleBody"]',
        ".document",
        "article",
        "main",
        ".body",
        ".section",
        "#content",
        ".content",
    ]

    for selector in selectors:
        element = soup.select_one(selector)
        # 충분한 내용이 있는지 확인
        if element and len(element.get_text(strip=True)) > 200:
            return str(element)

    # 2. Readability 폴백 (구조적 선택자가 실패한 경우)
    try:
        doc = Document(html)
        content = doc.summary()
        content_soup = BeautifulSoup(content, "lxml")
        if len(content_soup.get_text(strip=True)) > 200:
            return content
    except Exception as e:
        logger.warning(f"Readability 폴백 추출 실패: {e}")

    # 3. 최후의 수단: body 전체
    if soup.body:
        return str(soup.body)

    return html


def to_markdown(html_content: str, source_url: str) -> str:
    """
    HTML을 마크다운으로 변환하고 YAML Front Matter를 상단에 추가합니다.

    Args:
        html_content (str): 변환할 HTML 문자열.
        source_url (str): 원본 출처 URL.

    Returns:
        str: YAML 메타데이터가 포함된 마크다운 문자열.
    """

    # markdownify를 위한 커스텀 코드 언어 콜백 함수
    def code_language_callback(el):
        # markdownify가 기본적으로 표준 코드 블록을 처리하지만,
        # 'language-' 클래스를 감지하여 언어 힌트를 추출할 수 있습니다.
        pass

    # 마크다운으로 변환합니다.
    markdown_content = md(
        html_content,
        strip=["script", "style"],
        heading_style="ATX",
        code_language_callback=lambda el: (
            el.get("class")[0].replace("language-", "")
            if el.get("class") and el.get("class")[0].startswith("language-")
            else None
        ),
    )

    # 과도한 줄바꿈을 정리합니다.
    import re

    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    # 메타데이터를 생성합니다.
    collected_at = datetime.now(UTC).isoformat()
    metadata = f"""---
source_url: {source_url}
target_version: 2.x
collected_at: {collected_at}
---

"""
    return metadata + markdown_content.strip() + "\n"
