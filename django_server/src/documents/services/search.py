from typing import Any

from django.db import connection
from documents.models import Chunk
from documents.services.embedding import get_embedding_service
from documents.services.reranking import get_reranking_service
from pgvector.django import CosineDistance


class SearchService:
    """
    하이브리드 검색 및 pgvector 유사도 검색을 수행하는 서비스 클래스.

    키워드 기반 BM25와 의미론적 벡터 검색을 통합하고, Rerank 전략을 적용하여
    최상의 검색 결과를 반환합니다.
    """

    def __init__(self) -> None:
        """
        SearchService를 초기화하고 필요한 하위 서비스를 로드합니다.
        """
        self.embedding_service = get_embedding_service()
        self.reranking_service = get_reranking_service()

    async def search(
        self,
        query: str,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        통합 검색 인터페이스. 하이브리드 검색 후 Rerank를 수행합니다.

        Args:
            query (str): 사용자의 자연어 검색 질의어.
            target_version (Optional[str]): 필터링할 Django 버전.
            category (Optional[str]): 필터링할 문서 카테고리.
            limit (int): 반환할 최대 결과 개수.

        Returns:
            list[dict[str, Any]]: 최종 정렬된 검색 결과 리스트.
        """
        # 1. 하이브리드 검색 수행 (상위 20개 후보군 추출)
        initial_results = await self.hybrid_search(
            query=query, target_version=target_version, category=category, limit=20
        )

        if not initial_results:
            return []

        # 2. Rerank 수행
        contents = [r["content"] for r in initial_results]
        rerank_scores = self.reranking_service.rerank(query, contents)

        # 3. 점수 업데이트 및 최종 정렬
        for res, score in zip(initial_results, rerank_scores, strict=False):
            res["similarity"] = round(score, 6)
            res["extra_meta"]["rerank_score"] = score

        # Rerank 점수 기준 내림차순 정렬 후 요청된 개수만큼 반환
        final_results = sorted(initial_results, key=lambda x: x["similarity"], reverse=True)[:limit]

        return final_results

    async def vector_search(
        self,
        query: str,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        pgvector의 코사인 유사도만을 기반으로 관련 청크를 검색합니다.
        """
        query_vector = self.embedding_service.embed_text(query)

        queryset = Chunk.objects.select_related("section", "section__document").filter(
            section__document__status="Active"
        )

        if target_version:
            queryset = queryset.filter(section__document__target_version=target_version)
        if category:
            queryset = queryset.filter(section__document__category=category)

        results = queryset.annotate(distance=CosineDistance("embedding", query_vector)).order_by(
            "distance"
        )[:limit]

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

    async def hybrid_search(
        self,
        query: str,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 20,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        """
        BM25(키워드)와 Vector(의미) 검색을 결합한 하이브리드 검색을 수행합니다.
        """
        query_vector = self.embedding_service.embed_text(query)

        clean_query = query.strip()
        use_bm25 = len(clean_query) >= 2

        where_clauses = ["d.status = 'Active'"]
        where_params: list[str] = []

        if target_version:
            where_clauses.append("d.target_version = %s")
            where_params.append(target_version)
        if category:
            where_clauses.append("d.category = %s")
            where_params.append(category)

        where_sql = " AND ".join(where_clauses)

        sql = f"""
        WITH vector_results AS (
            SELECT
                c.id,
                1.0 / ({rrf_k} + ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector)) as score
            FROM documents_chunk c
            JOIN documents_section s ON c.section_id = s.id
            JOIN documents_document d ON s.document_id = d.id
            WHERE {where_sql}
            ORDER BY c.embedding <=> %s::vector
            LIMIT {limit * 2}
        ),
        bm25_results AS (
            SELECT
                c.id,
                1.0 / ({rrf_k} + ROW_NUMBER() OVER (ORDER BY c.content @@@ %s)) as score
            FROM documents_chunk c
            JOIN documents_section s ON c.section_id = s.id
            JOIN documents_document d ON s.document_id = d.id
            WHERE {where_sql} AND {"c.content @@@ %s" if use_bm25 else "FALSE"}
            LIMIT {limit * 2}
        )
        SELECT
            COALESCE(v.id, b.id) as chunk_id,
            (COALESCE(v.score, 0) + COALESCE(b.score, 0)) as rrf_score
        FROM vector_results v
        FULL OUTER JOIN bm25_results b ON v.id = b.id
        ORDER BY rrf_score DESC
        LIMIT %s;
        """

        # SQL 파라미터 리스트 구성
        actual_sql_params: list[Any] = [query_vector] + where_params + [query_vector] + where_params
        if use_bm25:
            actual_sql_params.append(clean_query)
        actual_sql_params.append(limit)

        search_results = []
        with connection.cursor() as cursor:
            cursor.execute(sql, actual_sql_params)
            rows = cursor.fetchall()

            for row in rows:
                chunk_id, rrf_score = row
                chunk = Chunk.objects.select_related("section", "section__document").get(
                    id=chunk_id
                )
                search_results.append(
                    {
                        "id": str(chunk.id),
                        "content": str(chunk.content),
                        "similarity": round(float(rrf_score), 6),
                        "document_title": str(chunk.section.document.title),
                        "section_title": str(chunk.section.title),
                        "version": str(chunk.section.document.target_version),
                        "extra_meta": {"rrf_score": rrf_score},
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
