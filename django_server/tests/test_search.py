import time

import pytest
from documents.models import Chunk, Document, Section
from documents.services.embedding import get_embedding_service
from documents.services.search import get_search_service


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_vector_search() -> None:
    """pgvector를 이용한 벡터 검색 정확도 테스트"""
    # 1. 테스트 데이터 준비
    doc = await Document.objects.acreate(
        title="Django Tutorial",
        target_version="5.0",
        category="Tutorial",
        source_path="/tutorial.md",
    )
    section = await Section.objects.acreate(document=doc, title="Intro", level=1, order=0)

    hello_vector = [0.1] * 1024
    hello_vector[0] = 1.0

    await Chunk.objects.acreate(
        section=section,
        content="This section is about saying hello to Django.",
        section_title=section.title,
        embedding=hello_vector,
        token_count=10,
    )

    # 2. 검색 서비스 호출
    search_service = get_search_service()

    # 3. 결과 검증
    # SearchService에 vector_search 메서드가 없으므로 hybrid_search로 테스트
    results = await search_service.hybrid_search("hello")
    assert len(results) >= 1
    assert results[0]["document_title"] == "Django Tutorial"
    assert "similarity" in results[0]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_hybrid_search() -> None:
    """BM25와 벡터 검색이 결합된 하이브리드 검색 테스트"""
    # 1. 테스트 데이터 준비
    doc = await Document.objects.acreate(
        title="Django Advanced",
        target_version="5.0",
        category="Reference",
        source_path="/advanced.md",
    )
    section = await Section.objects.acreate(document=doc, title="Filtering", level=1, order=0)

    # 키워드 'filter'가 포함된 본문
    filter_vector = [0.0] * 1024
    await Chunk.objects.acreate(
        section=section,
        content="This document explains how to use the filter method in QuerySets.",
        section_title=section.title,
        embedding=filter_vector,
        token_count=15,
    )

    search_service = get_search_service()

    # 2. 하이브리드 검색 실행
    try:
        results = await search_service.hybrid_search("filter")

        # 3. 결과 검증
        assert len(results) >= 1
        assert "filter" in results[0]["content"].lower()
        assert "rrf_score" in results[0]["extra_meta"]
    except Exception as e:
        if 'extension "pg_search" does not exist' in str(e):
            pytest.skip("pg_search 확장이 없어 하이브리드 검색 테스트를 건너뜁니다.")
        else:
            raise e


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_performance_and_format() -> None:
    """통합 검색 성능 및 응답 규격 준수 테스트 (US1, SYS-001, SYS-002)"""
    embedding_service = get_embedding_service()
    search_service = get_search_service()

    # 1. 테스트 데이터 준비 (실제 모델 연산 결과 포함)
    text = "To filter querysets in Django, use the filter() method."
    emb_data = embedding_service.embed_text(text)

    doc = await Document.objects.acreate(
        title="Django QuerySets",
        target_version="5.2",
        category="Tutorials",
        source_path="/qs.md",
        source_url="https://docs.djangoproject.com/en/5.2/ref/models/querysets/",
    )
    section = await Section.objects.acreate(document=doc, title="Filtering", level=1, order=0)

    await Chunk.objects.acreate(
        section=section,
        content=text,
        section_title=section.title,
        embedding=emb_data["dense_vector"],
        multi_vector_low_dim=emb_data["multi_vector_bytes"],
        token_count=emb_data["token_count"],
    )

    # 2. 검색 실행 및 시간 측정
    start_time = time.time()
    results = await search_service.search("how to filter querysets")
    end_time = time.time()
    latency = (end_time - start_time) * 1000

    # 3. 결과 검증
    # 3.1 성능 검증 (SYS-001: 1,000ms 이하)
    assert latency < 1000, f"Search latency is too high: {latency}ms"

    # 3.2 응답 규격 검증 (SYS-002)
    assert len(results) > 0
    res = results[0]
    required_fields = [
        "content",
        "similarity",
        "document_title",
        "section_title",
        "version",
        "extra_meta",
    ]
    for field in required_fields:
        assert field in res, f"Missing required field in response: {field}"

    assert "rerank_score" in res.get("extra_meta", {}), "Rerank score missing in extra_meta"
    assert "source_url" in res.get("extra_meta", {}), "Source URL missing in extra_meta"
    assert "category" in res.get("extra_meta", {}), "Category missing in extra_meta"

    # 3.3 리랭킹 정밀도 검증
    assert res["rerank_score"] >= 0.3, f"Rerank score {res['rerank_score']} is below threshold 0.3"
    assert res["similarity"] == res["rerank_score"], (
        "Final similarity score should be the rerank score"
    )
