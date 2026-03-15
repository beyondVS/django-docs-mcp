from pathlib import Path
from urllib.parse import urlparse


def get_file_path(base_dir: str, url: str) -> Path:
    """
    URL을 기반으로 로컬 파일 경로를 생성합니다.

    Args:
        base_dir (str): 파일이 저장될 기본 디렉토리 경로.
        url (str): 대상 URL.

    Returns:
        Path: 생성된 로컬 파일 경로 객체.
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        path = "index"

    if not path.endswith(".md"):
        # 확장자가 없거나 디렉토리인 경우 .md를 추가합니다.
        # .html로 끝나는 경우 .md로 대체합니다.
        if path.endswith(".html"):
            path = path[:-5] + ".md"
        else:
            path = path + ".md"

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
