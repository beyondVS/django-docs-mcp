from pathlib import Path
from urllib.parse import urlparse


def get_file_path(
    base_dir: str, url: str, extension: str = ".html", strip_prefix: str = ""
) -> Path:
    """
    URL을 기반으로 로컬 파일 경로를 생성합니다.

    Args:
        base_dir (str): 파일이 저장될 기본 디렉토리 경로.
        url (str): 대상 URL.
        extension (str): 파일 확장자 (.html 또는 .md).
        strip_prefix (str): 제거할 URL 경로 접두사 (예: "/en/5.2/").

    Returns:
        Path: 생성된 로컬 파일 경로 객체.
    """
    parsed = urlparse(url)
    path = parsed.path

    # 접두사 제거 (예: /projects/django-admin-cookbook/en/latest/ -> /)
    if strip_prefix and path.startswith(strip_prefix):
        path = path[len(strip_prefix) :].lstrip("/")

    path_parts = [p for p in path.split("/") if p]

    filename = "index" if not path_parts else "/".join(path_parts)

    if not filename.endswith(extension):
        # .html로 끝나는 요청인 경우 확장자 교체 처리
        if filename.endswith(".html") and extension == ".md":
            filename = filename[:-5] + ".md"
        else:
            filename = filename + extension

    file_path = Path(base_dir) / filename
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
