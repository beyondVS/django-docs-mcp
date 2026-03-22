"""
Django 5.2 문서 크롤러 스크립트

GitHub 저장소에서 문서를 가져와서 마크다운으로 변환 후 로컬 파일 시스템에 저장합니다.
"""

import os
import shutil
import subprocess
from pathlib import Path

from utils.logger import get_logger
from utils.rst_converter import add_metadata, rst_to_markdown

logger = get_logger(__name__)

REPO_URL = "https://github.com/django/django.git"
BRANCH = "stable/5.2.x"
# 스크립트 파일 위치 기준 절대 경로 계산
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / ".temp/django_src"
OUTPUT_DIR = BASE_DIR.parent / "data_sources/django-5.2-docs"


def clone_docs():
    """GitHub에서 Django 문서 저장소의 docs 폴더만 sparse-checkout으로 클론합니다.

    기존에 임시 디렉터리가 존재할 경우 삭제 후 새로 클론을 시도합니다.
    sparse-checkout을 통해 전체 저장소 대신 docs 폴더의 내용만 효율적으로 가져옵니다.

    Raises:
        subprocess.CalledProcessError: Git 명령어 실행 중 오류가 발생한 경우.
    """
    if TEMP_DIR.exists():
        logger.info(f"기존 임시 디렉터리 삭제 중: {TEMP_DIR}")
        import stat

        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        shutil.rmtree(TEMP_DIR, onerror=remove_readonly)

    TEMP_DIR.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Django 5.2 문서를 {TEMP_DIR}에 클론 중...")

    try:
        # Git Sparse Checkout 초기화 (객체 없는 얕은 클론)
        subprocess.run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                "--depth",
                "1",
                "--sparse",
                "-b",
                BRANCH,
                REPO_URL,
                str(TEMP_DIR),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # docs 디렉터리만 sparse-checkout 설정 및 체크아웃
        subprocess.run(
            ["git", "sparse-checkout", "set", "docs"],
            cwd=str(TEMP_DIR),
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "checkout"], cwd=str(TEMP_DIR), check=True, capture_output=True)

        logger.info("문서 클론이 성공적으로 완료되었습니다.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git 클론 중 오류 발생: {e.stderr}")
        raise


def discover_rst_files() -> list[Path]:
    """클론된 임시 디렉터리 내의 모든 RST(.txt) 파일을 재귀적으로 탐색합니다.
    'docs/releases/' 디렉터리는 릴리즈 히스토리 노이즈 방지를 위해 제외합니다.

    Returns:
        list[Path]: 탐색된 .txt 파일의 Path 객체 리스트.
    """
    docs_dir = TEMP_DIR / "docs"
    if not docs_dir.exists():
        logger.error(f"문서 디렉터리를 찾을 수 없습니다: {docs_dir}")
        return []

    # releases/ 디렉터리를 제외하고 탐색
    rst_files = [
        p
        for p in docs_dir.rglob("*.txt")
        if "releases" + os.sep not in str(p.relative_to(docs_dir))
    ]
    logger.info(f"총 {len(rst_files)}개의 RST(.txt) 파일을 발견했습니다. (releases/ 제외)")
    return rst_files


def process_and_save_files(file_paths: list[Path]):
    """탐색된 RST 파일들을 마크다운으로 변환하고 메타데이터를 추가하여 저장합니다.

    원본 docs/ 폴더 내의 계층 구조를 유지하면서 data_sources/django-5.2-docs/ 하위에
    .md 확장자로 결과물을 저장합니다.

    Args:
        file_paths (list[Path]): 변환할 RST 파일들의 경로 리스트.
    """
    docs_base_dir = TEMP_DIR / "docs"

    success_count = 0
    error_count = 0

    for rst_path in file_paths:
        try:
            # 1. 파일 읽기
            with open(rst_path, encoding="utf-8") as f:
                rst_content = f.read()

            # 2. 상대 경로 계산 (docs/ 이후의 경로)
            relative_path = rst_path.relative_to(docs_base_dir)

            # 3. 변환 및 메타데이터 추가
            markdown_content = rst_to_markdown(rst_content)
            final_content = add_metadata(markdown_content, str(relative_path))

            # 4. 저장 경로 계산 및 디렉터리 생성
            # .txt 확장자를 .md로 변경
            save_rel_path = relative_path.with_suffix(".md")
            save_path = OUTPUT_DIR / save_rel_path

            save_path.parent.mkdir(parents=True, exist_ok=True)

            # 5. 저장
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(final_content)

            success_count += 1
            if success_count % 100 == 0:
                logger.info(f"{success_count}개 파일 변환 완료...")

        except Exception as e:
            logger.error(f"파일 변환 실패 ({rst_path}): {e}")
            error_count += 1

    logger.info(f"변환 작업 완료: 성공 {success_count}개, 실패 {error_count}개")


def main():
    """Django 5.2 문서 크롤링 및 변환 파이프라인의 메인 진입점입니다.

    클론, 탐색, 변환 및 저장 과정을 순차적으로 수행합니다.
    """
    logger.info("Django 5.2 문서 크롤링을 시작합니다.")

    try:
        # 1. 문서 클론
        clone_docs()

        # 2. 파일 탐색
        rst_files = discover_rst_files()

        if not rst_files:
            logger.warning("변환할 파일을 찾지 못했습니다. 작업을 종료합니다.")
            return

        # 3. 변환 및 저장
        process_and_save_files(rst_files)

        logger.info("Django 5.2 문서 크롤링 및 변환 파이프라인이 성공적으로 완료되었습니다.")

    except Exception as e:
        logger.error(f"크롤링 파이프라인 실행 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
