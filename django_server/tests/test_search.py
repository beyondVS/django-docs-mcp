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

    # "Hello"와 유사한 내용의 청크 생성
    # 실제 임베딩 모델 대신 더미 벡터 사용
    # pgvector는 코사인 유사도 계산 시 차원이 맞아야 함 (1024)
    hello_vector = [0.1] * 1024
    hello_vector[0] = 1.0  # 특징값 부여

    await Chunk.objects.acreate(
        section=section,
        content="This section is about saying hello to Django.",
        embedding=hello_vector,
        token_count=10,
    )

    # 2. 검색 서비스 호출
    search_service = get_search_service()

    # 3. 결과 검증
    # 실제 bge-m3 모델이 로드되므로 임베딩 생성 결과에 따라 달라질 수 있음
    # 여기서는 검색 기능의 흐름(Flow) 위주로 테스트
    results = await search_service.search("hello")
    assert len(results) >= 1
    assert results[0]["document_title"] == "Django Tutorial"
    assert "similarity" in results[0]
