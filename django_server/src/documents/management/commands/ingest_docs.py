import logging
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from documents.models import Document
from documents.services.ingestion import get_ingestion_service

# T021: 에러 로깅 설정 (서비스 내부에서도 로깅하지만, CLI 레벨의 로그도 유지)
logger = logging.getLogger("ingestion")


class Command(BaseCommand):
    """
    기술 문서 적재를 위한 CLI 명령어 클래스.

    로컬 파일 시스템의 마크다운 문서를 파싱하고 벡터 임베딩을 생성하여
    PostgreSQL pgvector DB에 적재합니다.
    """

    help = "Ingest technical documents from a directory into the vector database."

    def add_arguments(self, parser: Any) -> None:
        """
        명령어 실행에 필요한 인자를 정의합니다.

        Args:
            parser: argparse 기반의 인자 파서 객체.
        """
        parser.add_argument("path", type=str, nargs="?", help="적재할 디렉토리 또는 파일 경로.")
        parser.add_argument(
            "--doc-version", type=str, default="5.0", help="문서의 기본 Django 버전."
        )
        parser.add_argument("--category", type=str, default="General", help="기본 카테고리.")
        parser.add_argument(
            "--force", action="store_true", help="기존 데이터가 있어도 강제로 재적재."
        )
        parser.add_argument(
            "--reindex",
            action="store_true",
            help="기존에 적재된 모든 문서를 다시 임베딩 및 리랭킹 데이터로 구축.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        명령어 실행의 주 진입점입니다.
        """
        path_str = options["path"]
        reindex = options["reindex"]

        if not path_str and not reindex:
            raise CommandError("경로(path)를 지정하거나 --reindex 옵션을 사용해야 합니다.")

        items_to_process = []
        # T011: 목차/인덱스 파일 제외 키워드 정의 (최적화)
        EXCLUDE_KEYWORDS = ["index", "latest", "toc", "genindex"]

        # 1. 경로가 제공된 경우 파일 수집
        if path_str:
            path = Path(path_str)
            if not path.exists():
                raise CommandError(f"경로 '{path}'가 존재하지 않습니다.")

            files = []
            if path.is_file():
                if path.suffix == ".md":
                    # 개별 파일 지정 시에도 필터링 규칙 적용
                    if not any(kw in path.name.lower() for kw in EXCLUDE_KEYWORDS):
                        files.append(path)
            else:
                # glob 결과에서 즉시 필터링하여 불필요한 처리 오버헤드 방지
                files.extend([
                    f for f in path.glob("**/*.md")
                    if not any(kw in f.name.lower() for kw in EXCLUDE_KEYWORDS)
                ])

            for f in files:
                items_to_process.append(
                    {
                        "path": f,
                        "version": options["doc_version"],
                        "category": options["category"],
                    }
                )

        # 2. Reindex 옵션인 경우 기존 문서 추가
        if reindex:
            existing_docs = Document.objects.filter(status="Active")
            added_count = 0
            for doc in existing_docs:
                p = Path(doc.source_path)
                # 파일이 존재하고, 필터링 대상이 아니며, 중복되지 않은 경우 추가
                if p.exists() and \
                   not any(kw in p.name.lower() for kw in EXCLUDE_KEYWORDS) and \
                   not any(item["path"] == p and item["version"] == doc.target_version for item in items_to_process):
                    items_to_process.append(
                        {"path": p, "version": doc.target_version, "category": doc.category}
                    )
                    added_count += 1

            self.stdout.write(
                self.style.SUCCESS(f"기존 문서 {added_count}개를 재인덱싱 대상으로 추가했습니다.")
            )

        if not items_to_process:
            self.stdout.write(self.style.WARNING("처리할 마크다운 파일을 찾을 수 없습니다."))
            return

        self.stdout.write(self.style.SUCCESS(f"총 {len(items_to_process)}개의 항목을 처리합니다."))

        try:
            ingestion_service = get_ingestion_service()
        except Exception as e:
            error_msg = f"서비스 초기화 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CommandError(error_msg) from e

        for item in tqdm(items_to_process, desc="문서 처리 중"):
            file_path = item["path"]
            try:
                ingestion_service.ingest_file(
                    file_path=file_path,
                    target_version=item["version"],
                    category=item["category"],
                )
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n사용자에 의해 중단되었습니다."))
                break
            except Exception as e:
                error_msg = f"파일 처리 실패 '{file_path}': {str(e)}"
                self.stderr.write(self.style.ERROR(error_msg))
                logger.error(error_msg, exc_info=True)

                if "model" in str(e).lower() or "connection" in str(e).lower():
                    self.stdout.write(self.style.ERROR("치명적인 오류로 인해 작업을 중단합니다."))
                    break
