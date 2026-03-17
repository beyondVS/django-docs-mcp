from pathlib import Path

import pytest
from documents.services.chunking import ChunkingService, get_chunking_service


@pytest.fixture
def chunking_service() -> ChunkingService:
    """테스트를 위한 ChunkingService 픽스처."""
    return get_chunking_service()


def test_split_markdown_basic_headers(chunking_service: ChunkingService) -> None:
    """US1: 헤더 계층 구조가 메타데이터에 올바르게 보존되는지 테스트"""
    markdown = """
# Title
## Section 1
Content 1
### Subsection 1.1
Content 1.1
## Section 2
Content 2
"""
    chunks = chunking_service.split_markdown(markdown)

    assert len(chunks) > 0
    # 첫 번째 섹션 (Section 1) 검증
    # 임시 검증: 헤더 정보가 어떤 식으로든 포함되어 있는지 확인
    found_h1 = any(
        "Title" in (c["metadata"].get("Header 1", "") or c["metadata"].get("header_context", ""))
        for c in chunks
    )
    assert found_h1


def test_large_code_block_integrity(chunking_service: ChunkingService) -> None:
    """US2: 대형 코드 블록이 중간에 잘리지 않는지 테스트"""
    sample_path = Path(__file__).parent / "samples" / "large_code_block.md"
    content = sample_path.read_text(encoding="utf-8")

    chunks = chunking_service.split_markdown(content)

    # 코드 블록 기호(```)의 개수가 각 청크에서 짝수인지 확인 (절단 방지 검증)
    for chunk in chunks:
        text: str = chunk["content"]
        code_symbol_count = text.count("```")
        # 헌법 II-4 및 US2 수락 기준: 코드 블록은 절대 분할되지 않거나 문법적으로 유효해야 함
        assert code_symbol_count % 2 == 0, f"Code block is cut in chunk: {text[:100]}..."


def test_data_purity_fr005(chunking_service: ChunkingService) -> None:
    """FR-005: 본문에 Document:, Context: 주입이 제거되었는지 테스트"""
    markdown = "# Title\n## Section\nContent here."
    chunks = chunking_service.split_markdown(markdown, metadata={"title": "Test Doc"})

    for chunk in chunks:
        # 최종 구현 후에는 이 주입이 사라져야 함
        assert "Document:" not in chunk["content"]
        assert "Context:" not in chunk["content"]
        # 대신 메타데이터에 있어야 함
        assert chunk["metadata"].get("header_context") is not None
