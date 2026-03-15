from datetime import UTC, datetime

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from readability import Document

from crawler.utils.logger import get_logger

logger = get_logger(__name__)


def extract_content(html: str) -> str:
    """
    readability-lxml을 사용하여 HTML에서 본문 내용을 추출합니다.
    readability가 실패할 경우 BeautifulSoup을 사용한 폴백 로직을 실행합니다.

    Args:
        html (str): 원본 HTML 문자열.

    Returns:
        str: 추출된 HTML 본문.
    """
    try:
        doc = Document(html)
        content = doc.summary()

        # 내용이 의미 있는지 확인합니다.
        soup = BeautifulSoup(content, "lxml")
        text = soup.get_text(strip=True)
        if len(text) > 100:
            return content
    except Exception as e:
        logger.warning(f"Readability 추출 실패: {e}. 폴백 로직을 시도합니다.")

    # BeautifulSoup을 사용한 폴백 로직
    soup = BeautifulSoup(html, "lxml")

    # 일반적인 본문 컨테이너를 찾습니다.
    for selector in ["article", "main", ".section", "#content", ".content"]:
        element = soup.select_one(selector)
        if element:
            return str(element)

    # 마지막 수단으로 body 태그 전체를 반환합니다.
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
