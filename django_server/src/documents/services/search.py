from typing import Any

from documents.models import Chunk
from documents.services.embedding import get_embedding_service
from pgvector.django import CosineDistance


class SearchService:
    """
    pgvector를 활용하여 자연어 질의에 대한 유사 문서 검색을 수행하는 서비스 클래스.

    코사인 유사도(Cosine Similarity)를 기반으로 질의어와 가장 관련성이 높은 문서 청크를 찾아냅니다.
    """

    def __init__(self) -> None:
        """
        SearchService를 초기화하고 임베딩 서비스를 로드합니다.
        """
        self.embedding_service = get_embedding_service()

    async def search(
        self,
        query: str,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        코사인 유사도를 기반으로 관련 문서 청크를 검색합니다.

        Args:
            query (str): 사용자의 자연어 검색 질의어.
            target_version (Optional[str]): 특정 Django 버전으로 필터링 (예: "5.0").
            category (Optional[str]): 특정 문서 카테고리로 필터링 (예: "Tutorials").
            limit (int): 반환할 최대 결과 개수. 기본값 5.

        Returns:
            list[dict[str, Any]]: 검색 결과 리스트.
                각 요소는 'content', 'similarity', 'document_title' 등을 포함합니다.
        """
        # 질의어를 벡터로 변환
        query_vector = self.embedding_service.embed_text(query)

        # 쿼리셋 구성 및 연관 객체 최적화 (Select Related)
        queryset = Chunk.objects.select_related("section", "section__document")

        # 필터링 적용
        if target_version:
            queryset = queryset.filter(section__document__target_version=target_version)
        if category:
            queryset = queryset.filter(section__document__category=category)

        # 활성화된 문서만 검색 대상으로 설정
        queryset = queryset.filter(section__document__status="Active")

        # 유사도(1 - 거리) 기준 정렬 및 상위 결과 추출
        # pgvector의 CosineDistance는 0(완전 일치)에서 2(반대) 사이의 값을 가짐
        results = queryset.annotate(distance=CosineDistance("embedding", query_vector)).order_by(
            "distance"
        )[:limit]

        # 비동기 이터레이션을 통해 결과 리스트 생성
        search_results: list[dict[str, Any]] = []
        async for chunk in results:
            search_results.append(
                {
                    "id": str(chunk.id),
                    "content": str(chunk.content),
                    "similarity": round(1 - float(chunk.distance), 4),
                    "document_title": str(chunk.section.document.title),
                    "section_title": str(chunk.section.title),
                    "version": str(chunk.section.document.target_version),
                }
            )

        return search_results


def get_search_service() -> SearchService:
    """
    SearchService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        SearchService: 초기화된 검색 서비스.
    """
    return SearchService()
