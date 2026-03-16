# Ingestion CLI Contract

데이터 적재를 위한 Django Custom Management Command의 규격을 정의합니다.

## 1. 명령어 개요
- **명령어**: `python src/manage.py ingest_docs`
- **목적**: `data_sources/` 폴더 내의 마크다운 파일을 파싱하여 DB에 적재.

## 2. Arguments & Options (입력 규격)

### Positional Arguments
- `source_path`: 적재할 마크다운 파일 또는 디렉토리 경로 (필수).

### Optional Flags
- `--version`: 대상 Django 버전 명시 (예: `--version 5.0`). 기본값: 파일 내 YAML Front Matter 우선.
- `--category`: 문서 유형 명시 (예: `--category Tutorial`).
- `--clear`: 적재 전 기존 문서(및 관련 Chunk) 삭제 여부. (Boolean)
- `--batch-size`: 임베딩 생성 시 한 번에 처리할 Chunk 수 (기본값: 16).

## 3. Execution Flow (실행 흐름)
1. **File Scanning**: 지정된 경로에서 `.md` 파일을 재귀적으로 검색.
2. **Metadata Parsing**: YAML Front Matter 추출 (Title, URL 등).
3. **Chunking**: `MarkdownHeaderTextSplitter`를 사용한 논리적 분할.
4. **Embedding**: `BAAI/bge-m3` 모델을 통한 벡터화 (Batch 처리).
5. **DB Insertion**: `transaction.atomic`을 적용하여 문서 단위 Upsert 수행.
6. **Logging**: 성공/실패 통계 출력 및 오류 발생 시 실패 문서 경로 로깅.

## 4. Output (출력 예시)
```text
[Processing] docs/tutorial/part1.md ... Success (12 chunks)
[Processing] docs/ref/models.md ... Success (45 chunks)
---
Summary:
Total Files: 102
Successful: 101
Failed: 1 (docs/corrupted.md)
Error Log: logs/ingest_error_20260316.log
```
