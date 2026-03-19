import logging
from pathlib import Path

import frontmatter
from django.db import transaction

from ..models import Chunk, Document, Section
from .chunking import get_chunking_service
from .embedding import get_embedding_service

# T021: 에러 로깅 설정
logger = logging.getLogger("ingestion")


class IngestionService:
    """
    마크다운 문서 데이터를 벡터 데이터베이스에 적재하는 서비스 클래스.

    파일 파싱, 청킹, 임베딩 생성 및 DB 적재(Upsert) 프로세스를 총괄합니다.
    """

    def __init__(self) -> None:
        """
        IngestionService를 초기화하고 필요한 하위 서비스를 로드합니다.
        """
        self.embedding_service = get_embedding_service()
        self.chunking_service = get_chunking_service()

    def ingest_file(
        self, file_path: Path, target_version: str = "5.0", category: str = "General"
    ) -> Document | None:
        """
        개별 마크다운 파일을 파싱하고 벡터 DB에 적재합니다.

        Args:
            file_path (Path): 적재할 마크다운 파일의 절대 경로.
            target_version (str): 대상 Django 버전. 기본값 "5.0".
            category (str): 문서 카테고리. 기본값 "General".

        Returns:
            Document | None: 적재된 Document 객체. 목차 파일인 경우 None 반환.

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때.
            Exception: 임베딩 생성 또는 DB 적재 중 오류 발생 시.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 파일 내용 및 프론트매터 로드
        with open(file_path, encoding="utf-8") as f:
            post = frontmatter.load(f)
            content = str(post.content)
            metadata = dict(post.metadata)

        # 메타데이터 추출 (YAML Front Matter 우선)
        title: str = str(metadata.get("title", file_path.stem))
        version: str = str(metadata.get("target_version", target_version))
        doc_category: str = str(metadata.get("category", category))
        source_url: str = str(metadata.get("source_url", ""))

        # 1. 목차/인덱스 파일 제외 필터링 (최적화)
        exclude_keywords = ["index", "latest", "toc", "genindex"]
        filename_lower = file_path.name.lower()
        if any(kw in filename_lower for kw in exclude_keywords):
            logger.info(f"Skipping index/meta file: {file_path.name}")
            # 필터링되어 스킵하더라도, DB에 해당 파일/버전이 이미 있다면
            # 삭제하여 찌꺼기가 남지 않게 함
            Document.objects.filter(
                source_path=str(file_path.absolute()), target_version=version
            ).delete()
            return None

        with transaction.atomic():
            # T011: 기존 동일 경로/버전 문서 삭제 (Upsert 효과)
            Document.objects.filter(
                source_path=str(file_path.absolute()), target_version=version
            ).delete()

            # 1. 문서(Document) 객체 생성
            doc = Document.objects.create(
                title=title,
                target_version=version,
                category=doc_category,
                source_path=str(file_path.absolute()),
                source_url=source_url,
                status="Active",
            )

            # 2. 문서 분할(Chunking) 및 문맥 주입
            doc_metadata: dict[str, str] = {"title": title}
            chunks_data = self.chunking_service.split_markdown(content, metadata=doc_metadata)

            sections_cache: dict[str, Section] = {}

            for chunk_info in chunks_data:
                header_context: str = str(chunk_info["metadata"].get("header_context", "Main"))

                # 3. 섹션(Section) 객체 생성 또는 캐시 조회
                if header_context not in sections_cache:
                    level: int = 1
                    if " > " in header_context:
                        level = header_context.count(" > ") + 1

                    section = Section.objects.create(
                        document=doc, title=header_context, level=level, order=len(sections_cache)
                    )
                    sections_cache[header_context] = section

                section = sections_cache[header_context]

                # 4. 임베딩 생성 및 청크(Chunk) 저장
                try:
                    # dense_vector, multi_vector_bytes, token_count 포함 dict 반환
                    emb_data = self.embedding_service.embed_text(chunk_info["content"])
                except Exception as e:
                    # T021: 임베딩 실패 시 에러 로깅 후 전파 (트랜잭션 롤백됨)
                    logger.error(f"임베딩 생성 중 치명적 오류 발생: {str(e)}", exc_info=True)
                    raise e

                Chunk.objects.create(
                    section=section,
                    content=chunk_info["content"],
                    section_title=section.title,
                    embedding=emb_data["dense_vector"],
                    multi_vector_low_dim=emb_data["multi_vector_bytes"],
                    token_count=emb_data["token_count"],
                    overlap_index=int(chunk_info["metadata"].get("chunk_index", 0)),
                )

        return doc


def get_ingestion_service() -> IngestionService:
    """
    IngestionService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        IngestionService: 초기화된 적재 서비스.
    """
    return IngestionService()
