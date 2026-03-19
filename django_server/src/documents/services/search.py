import logging
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Q
from documents.models import Chunk
from documents.services.embedding import get_embedding_service
from documents.services.reranking import get_reranking_service

logger = logging.getLogger(__name__)


class SearchService:
    """
    하이브리드 검색 및 Late Interaction 리랭킹을 수행하는 서비스 클래스.
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
        """
        통합 검색(Hybrid + Rerank)을 실행합니다.
        """
        try:
            # 1. 질문 임베딩 (Dense + Multi-vector 동시 생성)
            embedding_data = await sync_to_async(self.embedding_service.embed_text)(query)
            query_dense = embedding_data["dense_vector"]
            query_multi = embedding_data["multi_vector_bytes"]

            # 2. 1차 하이브리드 검색 (Retrieval)
            rerank_top_n = getattr(settings, "RERANK_TOP_N", 50)
            initial_results = await self.hybrid_search(
                query=query,
                query_dense_vector=query_dense,
                target_version=target_version,
                category=category,
                limit=rerank_top_n,
            )

            if not initial_results:
                return []

            # 3. 2차 리랭킹 (Late Interaction / MaxSim)
            try:
                reranked_results: list[dict[str, Any]] = await sync_to_async(
                    self.reranking_service.rerank
                )(query_multi, initial_results)

                if not reranked_results:
                    return []

                return reranked_results[:limit]

            except Exception as rerank_error:
                # 리랭킹 단계 실패 시 하이브리드 결과로 폴백 (FR-004)
                logger.error(f"Reranking failed, fallback to hybrid: {str(rerank_error)}")
                for res in initial_results:
                    res["extra_meta"]["rerank_failed"] = True
                return initial_results[:limit]

        except Exception as e:
            logger.error(f"Search process failed: {str(e)}")
            return []

    async def hybrid_search(
        self,
        query: str,
        query_dense_vector: list[float] | None = None,
        target_version: str | None = None,
        category: str | None = None,
        limit: int = 50,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        """
        ORM 스타일로 BM25와 벡터 검색을 통합한 하이브리드 검색을 수행합니다.
        """
        from paradedb import Match, ParadeDB, Score
        from pgvector.django import CosineDistance

        if query_dense_vector is None:
            embedding_data = await sync_to_async(self.embedding_service.embed_text)(query)
            query_dense_vector = embedding_data["dense_vector"]

        # 공통 필터 (Pre-filtering)
        base_filter = Q(section__document__status="Active")
        if target_version:
            base_filter &= Q(section__document__target_version=target_version)
        if category:
            base_filter &= Q(section__document__category=category)

        # 1. BM25 검색 (ParadeDB)
        def get_bm25() -> list[Chunk]:
            return list(
                Chunk.objects.filter(base_filter)
                .filter(content=ParadeDB(Match(query, operator="OR")))
                .annotate(bm25_score=Score())
                .select_related("section", "section__document")
                .order_by("-bm25_score")[:limit]
            )

        # 2. 벡터 검색 (pgvector)
        def get_vector() -> list[Chunk]:
            return list(
                Chunk.objects.filter(base_filter)
                .annotate(distance=CosineDistance("embedding", query_dense_vector))
                .select_related("section", "section__document")
                .order_by("distance")[:limit]
            )

        bm25_hits = await sync_to_async(get_bm25)()
        vector_hits = await sync_to_async(get_vector)()

        # 3. RRF (Reciprocal Rank Fusion) 통합 (Python 레벨)
        rrf_scores: dict[Any, float] = {}

        for rank, chunk in enumerate(bm25_hits, 1):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (rrf_k + rank))

        for rank, chunk in enumerate(vector_hits, 1):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (rrf_k + rank))

        # 모든 히트 병합 (중복 제거)
        all_hits = {chunk.id: chunk for chunk in bm25_hits + vector_hits}

        # RRF 점수 순으로 정렬된 ID 목록
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # 결과 리스트 생성
        search_results = []
        for cid in sorted_ids:
            chunk = all_hits[cid]
            search_results.append(
                {
                    "id": str(chunk.id),
                    "content": str(chunk.content),
                    "similarity": float(rrf_scores[cid]),
                    "document_title": str(chunk.section.document.title),
                    "section_title": str(chunk.section.title),
                    "version": str(chunk.section.document.target_version),
                    "multi_vector_low_dim": chunk.multi_vector_low_dim,
                    "extra_meta": {
                        "rrf_score": float(rrf_scores[cid]),
                        "source_url": chunk.section.document.source_url,
                        "category": chunk.section.document.category,
                    },
                }
            )

        return search_results[:limit]


def get_search_service() -> SearchService:
    """SearchService 인스턴스를 반환합니다."""
    return SearchService()
