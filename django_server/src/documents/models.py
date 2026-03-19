import uuid
from typing import TYPE_CHECKING

from django.db import models
from paradedb import BM25Index
from pgvector.django import HnswIndex, VectorField

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class Document(models.Model):
    """
    기술 문서의 원본 정보를 저장하는 최상위 모델.

    하나의 마크다운 파일과 1:1 대응하며, 버전 및 상태 정보를 관리합니다.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=255, help_text="문서의 제목 (YAML Front Matter 또는 파일명)"
    )
    target_version = models.CharField(max_length=50, help_text="대상 Django 버전 (예: 5.2)")
    category = models.CharField(
        max_length=100, help_text="문서 카테고리 (예: Tutorials, Reference)"
    )
    source_path = models.CharField(max_length=1024, help_text="로컬 파일 시스템의 절대 경로")
    source_url = models.URLField(
        max_length=1024, blank=True, null=True, help_text="공식 Django 문서 웹 URL"
    )
    status = models.CharField(
        max_length=20,
        choices=[("Active", "Active"), ("Inactive", "Inactive")],
        default="Active",
        help_text="검색 활성화 상태",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    if TYPE_CHECKING:
        objects: Manager[Document]
    else:
        objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_path", "target_version"], name="unique_document_source_version"
            )
        ]
        indexes = [
            models.Index(fields=["target_version"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{str(self.title)} ({str(self.target_version)})"


class Section(models.Model):
    """
    문서 내의 개별 섹션을 나타내는 모델.

    마크다운의 헤더(H1, H2, H3 등)를 기준으로 구분됩니다.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=512, help_text="섹션 제목 (헤더 텍스트)")
    level = models.IntegerField(help_text="헤더 깊이 (1: H1, 2: H2, 3: H3)")
    order = models.IntegerField(help_text="문서 내 섹션 순서")

    if TYPE_CHECKING:
        objects: Manager[Section]
    else:
        objects = models.Manager()

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{str(self.document.title)} - {str(self.title)}"


class Chunk(models.Model):
    """
    검색 및 임베딩의 최소 단위인 텍스트 청크 모델.

    섹션 내의 텍스트를 일정 크기로 분할하여 저장하며, 벡터 임베딩을 포함합니다.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField(help_text="분할된 텍스트 본문")
    section_title = models.CharField(
        max_length=512, blank=True, help_text="검색 성능 향상을 위한 섹션 제목 데이타 (비정규화)"
    )
    embedding = VectorField(dimensions=1024, help_text="BGE-M3 1024차원 벡터 임베딩")
    token_count = models.IntegerField(help_text="대략적인 토큰 수")
    overlap_index = models.IntegerField(default=0, help_text="중첩 분할 시의 인덱스")
    created_at = models.DateTimeField(auto_now_add=True)

    if TYPE_CHECKING:
        objects: Manager[Chunk]
    else:
        objects = models.Manager()

    class Meta:
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            BM25Index(
                name="chunk_bm25_idx",
                fields={
                    "id": {},
                    "content": {},
                    "section_title": {},
                },
                key_field="id",
            ),
        ]

    def __str__(self) -> str:
        return f"Chunk {self.id} (Section: {str(self.section.title)})"
