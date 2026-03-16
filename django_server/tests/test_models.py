import pytest
from django.db.utils import IntegrityError
from documents.models import Chunk, Document, Section


@pytest.mark.django_db
def test_document_creation() -> None:
    """Document 모델 생성 및 필드 무결성 테스트"""
    doc = Document.objects.create(
        title="Test Doc",
        target_version="5.0",
        category="Tutorial",
        source_path="/abs/path/to/doc.md",
    )
    assert Document.objects.count() == 1
    assert doc.status == "Active"
    assert str(doc) == "Test Doc (5.0)"


@pytest.mark.django_db
def test_document_unique_constraint() -> None:
    """동일 경로 및 버전의 중복 생성 방지 테스트"""
    Document.objects.create(
        title="Doc 1", target_version="5.0", category="Test", source_path="/path/1"
    )
    with pytest.raises(IntegrityError):
        Document.objects.create(
            title="Doc 2", target_version="5.0", category="Test", source_path="/path/1"
        )


@pytest.mark.django_db
def test_section_and_chunk_hierarchy() -> None:
    """문서-섹션-청크 계층 구조 생성 테스트"""
    doc = Document.objects.create(title="Doc", target_version="5.0", category="T", source_path="/p")
    section = Section.objects.create(document=doc, title="H1", level=1, order=0)
    chunk = Chunk.objects.create(
        section=section, content="Some content", embedding=[0.1] * 1024, token_count=10
    )

    assert doc.sections.count() == 1
    assert section.chunks.count() == 1
    assert chunk.section == section
