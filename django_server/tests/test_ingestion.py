from pathlib import Path

import pytest
from django.core.management import call_command
from documents.models import Chunk, Document


@pytest.mark.django_db
def test_ingest_docs_command(tmp_path: Path) -> None:
    """ingest_docs CLI 명령어 통합 테스트"""
    # 임시 마크다운 파일 생성
    d = tmp_path / "docs"
    d.mkdir()
    f = d / "test.md"
    f.write_text(
        """---
title: Ingest Test
target_version: 5.0
category: Test
---

# Introduction
Hello world.

## Section 1
Content 1.
""",
        encoding="utf-8",
    )

    # 명령어 실행
    call_command("ingest_docs", str(d), doc_version="5.0", category="Test")

    # 결과 검증
    doc = Document.objects.get(title="Ingest Test")
    assert doc.target_version == "5.0"
    assert doc.sections.count() == 2  # Introduction, Section 1
    assert Chunk.objects.filter(section__document=doc).count() == 2


@pytest.mark.django_db
def test_ingest_docs_upsert(tmp_path: Path) -> None:
    """동일 문서 재적재 시 Upsert(삭제 후 재생성) 동작 테스트"""
    d = tmp_path / "docs"
    d.mkdir()
    f = d / "test.md"
    f.write_text("# Title\nContent", encoding="utf-8")

    # 1차 적재
    call_command("ingest_docs", str(d), doc_version="5.0")
    initial_id = Document.objects.get(target_version="5.0").id

    # 2차 적재
    call_command("ingest_docs", str(d), doc_version="5.0")
    new_doc = Document.objects.get(target_version="5.0")

    assert Document.objects.count() == 1
    assert new_doc.id != initial_id  # 새로운 UUID로 생성됨을 확인
