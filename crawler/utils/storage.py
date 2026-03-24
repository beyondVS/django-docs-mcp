from pathlib import Path
from urllib.parse import urlparse


def get_file_path(
    base_dir: str, url: str, extension: str = ".html", strip_prefix: str = "", seed_url: str = ""
) -> Path:
    """
    URL을 기반으로 로컬 파일 경로를 생성합니다.
    seed_url과 일치하면 _root_ 파일을 사용하고, 그 외에는 경로 구조를 유지합니다.

    Args:
        base_dir (str): 파일이 저장될 기본 디렉토리 경로.
        url (str): 대상 URL.
        extension (str): 파일 확장자 (.html 또는 .md).
        strip_prefix (str): 제거할 URL 경로 접두사.
        seed_url (str): 크롤링 시작 URL (루트 판단용).

    Returns:
        Path: 생성된 로컬 파일 경로 객체.
    """
    parsed = urlparse(url)
    path = parsed.path

    # 접두사 제거
    if strip_prefix and path.startswith(strip_prefix):
        path = path[len(strip_prefix) :].lstrip("/")

    path_parts = [p for p in path.split("/") if p]

    # 루트 URL 처리 (_root_ 파일명 부여)
    if url == seed_url or not path_parts:
        filename = "_root_" + extension
    else:
        # 일반 파일 처리
        filename = "/".join(path_parts)
        # 디렉토리 주소(/로 끝남)인 경우에도 파일명으로 변환하기 위해 처리
        if path.endswith("/") and not filename.endswith(extension):
            filename += extension

        if not filename.endswith(extension):
            # 확장자 교체 로직 (.html -> .md 등)
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
