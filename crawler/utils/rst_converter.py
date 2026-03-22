"""
RST 문서 변환 유틸리티 모듈

Django 5.2 문서를 마크다운으로 파싱하고 메타데이터를 추가하는 기능을 제공합니다.
이 모듈은 하위 호환성을 유지하기 위해 기존 converter.py와 별도로 분리되었습니다.
"""

import re
from datetime import UTC, datetime

from docutils import nodes
from docutils.core import publish_parts
from docutils.parsers.rst import directives, roles
from markdownify import markdownify as md


def _generic_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Sphinx 전용 롤을 일반 텍스트로 처리하여 파싱 오류를 방지합니다."""
    return [nodes.Text(text)], []


def _generic_directive(
    name, arguments, options, content, lineno, content_offset, block_text, state, state_machine
):
    """Sphinx 전용 디렉티브의 내용을 일반 컨테이너로 파싱하여 내용을 보존합니다."""
    node = nodes.container(block_text)
    node["classes"].append(name)
    state.nested_parse(content, content_offset, node)
    return [node]


# 디렉티브가 본문 내용을 가질 수 있도록 설정
_generic_directive.content = True
_generic_directive.arguments = (0, 1, True)  # 인자 허용
_generic_directive.options = {"class": directives.class_option}


# Sphinx 전용 롤 및 디렉티브 등록 (docutils 파싱 오류 방지)
COMMON_SPHINX_ROLES = [
    "doc",
    "ref",
    "setting",
    "mod",
    "func",
    "class",
    "attr",
    "meth",
    "djadmin",
    "term",
    "commit",
    "issue",
    "ticket",
    "source",
    "file",
    "envvar",
    "program",
    "option",
    "command",
]
for role in COMMON_SPHINX_ROLES:
    roles.register_local_role(role, _generic_role)

COMMON_SPHINX_DIRECTIVES = [
    "versionadded",
    "versionchanged",
    "deprecated",
    "seealso",
    "note",
    "warning",
    "code-block",
    "highlight",
    "admonition",
    "toctree",
    "index",
    "glossary",
]
for directive in COMMON_SPHINX_DIRECTIVES:
    directives.register_directive(directive, _generic_directive)


def rst_to_markdown(rst_content: str) -> str:
    """RST 문자열을 마크다운 문자열로 변환합니다.

    docutils를 사용하여 먼저 HTML로 파싱한 후, markdownify를 통해 마크다운으로 변환합니다.
    Sphinx 전용 구문으로 인한 파싱 오류 메시지가 포함되지 않도록 설정을 최적화했습니다.

    Args:
        rst_content (str): 원본 RST 문자열.

    Returns:
        str: 변환된 마크다운 문자열.
    """
    # 1. docutils를 통해 RST를 HTML 구조로 변환
    # 'report_level': 5 (Hidden) 설정을 통해 파싱 오류 메시지가 HTML에 포함되는 것을 방지합니다.
    settings_overrides = {
        "report_level": 5,
        "halt_level": 5,
    }
    parts = publish_parts(source=rst_content, writer_name="html", settings_overrides=settings_overrides)
    html_content = parts.get("html_body", "")

    # 2. HTML을 마크다운으로 변환
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

    # 3. 과도한 줄바꿈 등 후처리 정제
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    return markdown_content.strip()


def add_metadata(markdown_content: str, file_path: str) -> str:
    """파일 경로 기반으로 메타데이터(source_url 및 target_version: 5.2)를 추가하여 최종 마크다운을 반환합니다.

    Args:
        markdown_content (str): 메타데이터를 추가할 마크다운 문자열.
        file_path (str): 원본 RST 파일의 디렉터리 기반 상대 경로 (예: intro/overview.txt).

    Returns:
        str: 메타데이터가 포함된 마크다운 문자열.
    """
    # Windows 경로 지원을 위해 백슬래시를 슬래시로 변경
    normalized_path = file_path.replace("\\", "/")

    # .txt 확장자 제거
    if normalized_path.endswith(".txt"):
        normalized_path = normalized_path[:-4]

    # URL의 마지막에 슬래시 추가
    if not normalized_path.endswith("/"):
        normalized_path += "/"

    source_url = f"https://docs.djangoproject.com/en/5.2/{normalized_path}"
    collected_at = datetime.now(UTC).isoformat()

    metadata = f"""---
source_url: {source_url}
target_version: 5.2
collected_at: {collected_at}
---

"""
    return metadata + markdown_content
