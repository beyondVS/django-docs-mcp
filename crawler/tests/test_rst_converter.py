"""
RST 문서 변환 유틸리티 모듈에 대한 단위 테스트
"""

from utils.rst_converter import add_metadata, rst_to_markdown


def test_rst_to_markdown_basic():
    """RST가 정상적으로 마크다운으로 파싱/변환되는지 확인합니다."""
    rst_input = """
제목
====

이것은 **강조된** 텍스트와 *기울임* 텍스트입니다.

- 항목 1
- 항목 2
    """

    markdown_output = rst_to_markdown(rst_input)

    assert "# 제목" in markdown_output
    assert "**강조된**" in markdown_output
    assert "*기울임*" in markdown_output
    assert "* 항목 1" in markdown_output
    assert "* 항목 2" in markdown_output


def test_add_metadata_basic():
    """파일 경로를 기반으로 정상적으로 source_url이 생성되고 front matter가 추가되는지 확인합니다."""
    markdown_input = "# 제목\n\n내용입니다."
    file_path = "intro/overview.txt"

    result = add_metadata(markdown_input, file_path)

    assert "---" in result
    assert "source_url: https://docs.djangoproject.com/en/5.2/intro/overview/" in result
    assert "target_version: 5.2" in result
    assert "collected_at:" in result
    assert "# 제목\n\n내용입니다." in result


def test_add_metadata_windows_path():
    """Windows 스타일 경로도 올바르게 URL로 변환되는지 확인합니다."""
    markdown_input = "내용"
    file_path = "topics\\settings.txt"

    result = add_metadata(markdown_input, file_path)

    assert "source_url: https://docs.djangoproject.com/en/5.2/topics/settings/" in result
