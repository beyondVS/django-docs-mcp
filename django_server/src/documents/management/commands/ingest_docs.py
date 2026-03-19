import logging
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

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
        parser.add_argument("path", type=str, help="적재할 디렉토리 또는 파일 경로.")
        parser.add_argument(
            "--doc-version", type=str, default="5.0", help="문서의 기본 Django 버전."
        )
        parser.add_argument("--category", type=str, default="General", help="기본 카테고리.")
        parser.add_argument(
            "--force", action="store_true", help="기존 데이터가 있어도 강제로 재적재."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        명령어 실행의 주 진입점입니다.

        Args:
            *args: 가변 인자.
            **options: CLI 옵션 딕셔너리.

        Raises:
            CommandError: 경로가 존재하지 않거나 치명적 오류 발생 시.
        """
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"경로 '{path}'가 존재하지 않습니다.")

        # 마크다운 파일 목록 수집
        files = []
        if path.is_file():
            if path.suffix == ".md":
                files.append(path)
        else:
            files.extend(list(path.glob("**/*.md")))

        if not files:
            self.stdout.write(self.style.WARNING("마크다운 파일을 찾을 수 없습니다."))
            return

        self.stdout.write(self.style.SUCCESS(f"총 {len(files)}개의 파일을 적재합니다."))

        try:
            ingestion_service = get_ingestion_service()
        except Exception as e:
            error_msg = f"서비스 초기화 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CommandError(error_msg) from e

        for file_path in tqdm(files, desc="문서 적재 중"):
            try:
                ingestion_service.ingest_file(
                    file_path=file_path,
                    target_version=str(options["doc_version"]),
                    category=str(options["category"]),
                )
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n사용자에 의해 중단되었습니다."))
                break
            except Exception as e:
                error_msg = f"파일 적재 실패 '{file_path}': {str(e)}"
                self.stderr.write(self.style.ERROR(error_msg))
                # T021: 에러 기록은 서비스 내부에서도 수행되나, CLI 에러 출력을 위해 유지

                logger.error(error_msg, exc_info=True)

                # 임베딩 모델 Timeout 등 치명적 오류 시 프로세스 중단
                if "model" in str(e).lower() or "connection" in str(e).lower():
                    self.stdout.write(self.style.ERROR("치명적인 오류로 인해 작업을 중단합니다."))
                    break
