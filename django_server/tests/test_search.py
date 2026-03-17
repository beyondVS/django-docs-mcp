import pytest
from documents.models import Chunk, Document, Section
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
    results = await search_service.vector_search("hello")
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
async def test_search_with_rerank() -> None:
    """Rerank 프로세스를 포함한 통합 검색 테스트"""
    # 1. 테스트 데이터 준비
    doc = await Document.objects.acreate(
        title="Django Models",
        target_version="5.0",
        category="Tutorial",
        source_path="/models.md",
    )
    section = await Section.objects.acreate(document=doc, title="Intro", level=1, order=0)

    dummy_vector = [0.0] * 1024

    await Chunk.objects.acreate(
        section=section,
        content="General information about Django models.",
        section_title=section.title,
        embedding=dummy_vector,
        token_count=5,
    )

    await Chunk.objects.acreate(
        section=section,
        content="To define a model, use a class inheriting from django.db.models.Model.",
        section_title=section.title,
        embedding=dummy_vector,
        token_count=15,
    )

    search_service = get_search_service()

    # 2. 통합 검색(Hybrid + Rerank) 실행
    try:
        results = await search_service.search("how to define a model")

        # 3. 결과 검증
        assert len(results) >= 1
        assert "Model" in results[0]["content"]
        assert "rerank_score" in results[0]["extra_meta"]
    except Exception as e:
        if 'extension "pg_search" does not exist' in str(e):
            pytest.skip("pg_search 확장이 없어 통합 검색 테스트를 건너뜁니다.")
        else:
            raise e
