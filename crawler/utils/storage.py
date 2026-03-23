from pathlib import Path
from urllib.parse import urlparse


def get_file_path(base_dir: str, url: str, extension: str = ".html") -> Path:
    """
    URL을 기반으로 로컬 파일 경로를 생성합니다.

    Args:
        base_dir (str): 파일이 저장될 기본 디렉토리 경로.
        url (str): 대상 URL.
        extension (str): 파일 확장자 (.html 또는 .md). 기본값은 .html.

    Returns:
        Path: 생성된 로컬 파일 경로 객체.
    """
    parsed = urlparse(url)
    # /en/5.2/ 접두사 이후의 경로만 추출 (정규화된 URL 가정)
    path_parts = [p for p in parsed.path.split("/") if p]

    # Django 문서 구조 특화 처리: /en/5.2/ 부분을 건너뜀
    if len(path_parts) >= 2 and path_parts[0] == "en" and path_parts[1] == "5.2":
        path_parts = path_parts[2:]

    path = "index" if not path_parts else "/".join(path_parts)

    if not path.endswith(extension):
        path = path + extension

    # base_dir 하위에 URL 경로 구조를 그대로 유지하여 반환합니다.
    file_path = Path(base_dir) / path
    return file_path


def save_file(file_path: str | Path, content: str) -> None:
    """
    내용을 파일로 저장하며, 부모 디렉토리가 없는 경우 생성합니다.

    Args:
        file_path (str | Path): 저장할 파일의 경로.
        content (str): 저장할 텍스트 내용.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
