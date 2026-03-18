import logging
from typing import Any

from asgiref.sync import sync_to_async
from django.db import connection
from documents.models import Chunk
from documents.services.embedding import get_embedding_service
from documents.services.reranking import get_reranking_service

logger = logging.getLogger(__name__)


class SearchService:
    """
    하이브리드 검색 및 pgvector 유사도 검색을 수행하는 서비스 클래스.
    """

    def __init__(self) -> None:
        self.embedding_service = get_embedding_service()
        self.reranking_service = get_reranking_service()

    async def search(
        self,
        query: str,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        # 1. 하이브리드 검색 수행
        initial_results = await self.hybrid_search(
            query=query, target_version=target_version, category=category, limit=10
        )

        if not initial_results:
            return []

        # 2. Rerank 수행
        contents = [r["content"] for r in initial_results]
        # 이벤트 루프 차단 방지를 위해 sync_to_async 사용
        rerank_scores = await sync_to_async(self.reranking_service.rerank)(query, contents)

        # 3. 점수 업데이트 및 최종 정렬
        for res, score in zip(initial_results, rerank_scores, strict=False):
            res["similarity"] = round(score, 6)
            res["extra_meta"]["rerank_score"] = score

        final_results = sorted(initial_results, key=lambda x: x["similarity"], reverse=True)[:limit]

        return final_results

    async def hybrid_search(
        self,
        query: str,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 20,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        query_vector = await sync_to_async(self.embedding_service.embed_text)(query)

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

        vector_part_sql = f"""
            SELECT
                c.id,
                1.0 / ({rrf_k} + ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector)) as score
            FROM documents_chunk c
            JOIN documents_section s ON c.section_id = s.id
            JOIN documents_document d ON s.document_id = d.id
            WHERE {where_sql}
            ORDER BY c.embedding <=> %s::vector
            LIMIT {limit * 2}
        """
        vector_part_params = [query_vector] + where_params + [query_vector]

        bm25_condition = "c.id @@@ %s" if use_bm25 else "FALSE"
        bm25_part_sql = f"""
            SELECT
                c.id,
                1.0 / ({rrf_k} + ROW_NUMBER() OVER (ORDER BY paradedb.score(c.id) DESC)) as score
            FROM documents_chunk c
            JOIN documents_section s ON c.section_id = s.id
            JOIN documents_document d ON s.document_id = d.id
            WHERE {where_sql} AND {bm25_condition}
            LIMIT {limit * 2}
        """
        bm25_part_params = where_params + [clean_query] if use_bm25 else where_params

        full_sql = f"""
        WITH vector_results AS ({vector_part_sql}),
             bm25_results AS ({bm25_part_sql})
        SELECT
            COALESCE(v.id, b.id) as chunk_id,
            (COALESCE(v.score, 0) + COALESCE(b.score, 0)) as rrf_score
        FROM vector_results v
        FULL OUTER JOIN bm25_results b ON v.id = b.id
        ORDER BY rrf_score DESC
        LIMIT %s;
        """

        full_params = vector_part_params + bm25_part_params + [limit]

        return await sync_to_async(self._execute_sql)(full_sql, full_params)

    def _execute_sql(self, sql: str, params: list[Any]) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        if not rows:
            return []

        chunk_ids = [row[0] for row in rows]
        rrf_scores = {row[0]: row[1] for row in rows}

        chunks = Chunk.objects.select_related("section", "section__document").filter(
            id__in=chunk_ids
        )
        chunk_map = {chunk.id: chunk for chunk in chunks}

        search_results = []
        for cid in chunk_ids:
            if cid in chunk_map:
                chunk = chunk_map[cid]
                search_results.append(
                    {
                        "id": str(chunk.id),
                        "content": str(chunk.content),
                        "similarity": round(float(rrf_scores[cid]), 6),
                        "document_title": str(chunk.section.document.title),
                        "section_title": str(chunk.section.title),
                        "version": str(chunk.section.document.target_version),
                        "extra_meta": {"rrf_score": rrf_scores[cid]},
                    }
                )

        return search_results


def get_search_service() -> SearchService:
    """SearchService 인스턴스를 반환합니다."""
    return SearchService()
