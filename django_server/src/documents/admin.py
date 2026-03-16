from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Chunk, Document, Section


class SectionInline(admin.TabularInline):
    """
    문서 상세 화면에서 하위 섹션들을 테이블 형태로 보여주는 인라인 클래스.
    """

    model = Section
    extra = 0
    show_change_link = True


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    문서(Document) 모델의 관리자 화면 구성을 정의합니다.
    """

    list_display = ("title", "target_version", "category", "status", "created_at")
    list_filter = ("target_version", "category", "status")
    search_fields = ("title", "source_path")
    inlines = [SectionInline]
    actions = ["make_active", "make_inactive", "re_ingest_documents"]

    @admin.action(description="선택된 문서 재적재 (파일에서 다시 읽기)")
    def re_ingest_documents(self, request: HttpRequest, queryset: QuerySet[Document]) -> None:
        """
        선택된 문서들을 로컬 파일 시스템에서 다시 읽어 벡터 DB에 적재합니다.

        Args:
            request (HttpRequest): 현재 요청 객체.
            queryset (QuerySet): 선택된 문서 쿼리셋.
        """
        from pathlib import Path

        from .services.ingestion import get_ingestion_service

        ingestion_service = get_ingestion_service()
        success_count = 0
        error_count = 0

        for doc in queryset:
            try:
                ingestion_service.ingest_file(
                    file_path=Path(str(doc.source_path)),
                    target_version=str(doc.target_version),
                    category=str(doc.category),
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, f"문서 '{str(doc.title)}' 적재 실패: {str(e)}", level=messages.ERROR
                )

        if success_count > 0:
            self.message_user(
                request,
                f"{success_count}개의 문서가 성공적으로 재적재되었습니다.",
                level=messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"{error_count}개의 문서 적재에 실패했습니다. 로그를 확인하십시오.",
                level=messages.WARNING,
            )

    @admin.action(description="선택된 문서를 활성 상태로 변경")
    def make_active(self, request: HttpRequest, queryset: QuerySet[Document]) -> None:
        """
        선택된 문서들의 상태를 'Active'로 변경합니다.

        Args:
            request (HttpRequest): 현재 요청 객체.
            queryset (QuerySet): 선택된 문서 쿼리셋.
        """
        queryset.update(status="Active")

    @admin.action(description="선택된 문서를 비활성 상태로 변경")
    def make_inactive(self, request: HttpRequest, queryset: QuerySet[Document]) -> None:
        """
        선택된 문서들의 상태를 'Inactive'로 변경합니다.

        Args:
            request (HttpRequest): 현재 요청 객체.
            queryset (QuerySet): 선택된 문서 쿼리셋.
        """
        queryset.update(status="Inactive")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """
    섹션(Section) 모델의 관리자 화면 구성을 정의합니다.
    """

    list_display = ("title", "document", "level", "order")
    list_filter = ("document__target_version", "document__category")
    search_fields = ("title", "document__title")


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    """
    텍스트 청크(Chunk) 모델의 관리자 화면 구성을 정의합니다.
    """

    list_display = (
        "id",
        "section_title",
        "document_title",
        "token_count",
        "created_at",
        "view_on_playground",
    )
    list_filter = ("section__document__target_version", "section__document__category")
    search_fields = ("content", "section__title", "section__document__title")
    readonly_fields = ("id", "created_at", "embedding")

    @admin.display(description="섹션 제목")
    def section_title(self, obj: Chunk) -> str:
        """섹션 제목을 반환합니다."""
        return str(obj.section.title)

    @admin.display(description="문서 제목")
    def document_title(self, obj: Chunk) -> str:
        """문서 제목을 반환합니다."""
        return str(obj.section.document.title)

    @admin.display(description="검색 결과 확인")
    def view_on_playground(self, obj: Chunk) -> str:
        """
        T018: 품질 분석을 위해 해당 청크의 내용을 검색 실험실에서 테스트하는 링크를 제공합니다.

        Args:
            obj (Chunk): 현재 청크 객체.

        Returns:
            SafeString: Playground로 연결되는 HTML 링크.
        """
        from django.urls import reverse

        # 청크 내용의 일부를 검색어로 사용하여 결과 확인
        url: str = reverse("documents:playground") + f"?q={str(obj.content)[:50]}"
        return format_html('<a href="{}" target="_blank">품질 테스트</a>', url)
