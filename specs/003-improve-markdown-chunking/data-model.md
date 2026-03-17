# 데이터 모델 정의: 마크다운 논리적 청킹 (003-improve-markdown-chunking)

## 데이터 구조 (Internal Schema)

### 1. Chunking Pipeline Data Flow
청킹 파이프라인을 거치는 데이터의 변환 과정은 다음과 같습니다:

1. **Input**: `str` (Raw Markdown Content)
2. **Phase 1 (MarkdownHeaderTextSplitter)**: `list[Document]`
   - 각 `Document.page_content`는 헤더로 구분된 섹션 텍스트.
   - 각 `Document.metadata`는 `Header 1`, `Header 2`, `Header 3` 필드를 포함.
3. **Phase 2 (MarkdownTextSplitter)**: `list[Document]`
   - 각 `Document.page_content`는 `chunk_size` 이하의 텍스트 (코드 블록 무결성 보존).
   - 각 `Document.metadata`는 상위 섹션의 헤더 정보를 상속받음.
4. **Output (ChunkingService.split_markdown)**: `list[dict[str, Any]]`
   - 하위 호환성을 위해 딕셔너리 리스트로 변환.
   - `content`: 순수 텍스트 (FR-005 준수).
   - `metadata`: `header_context`, `chunk_index`, `token_count` 등 포함.

### 2. Database Mapping (Metadata to Django Models)

| 메타데이터 필드 | 매핑 필드 (Django) | 설명 |
|-----------------|---------------------|------|
| `header_context`| `Section.title` | `H1 > H2 > H3` 형태의 계층 구조 문자열 |
| `Header 1` | (Section 정보 추출용) | 1단계 헤더 분할 결과 (H1) |
| `Header 2` | (Section 정보 추출용) | 1단계 헤더 분할 결과 (H2) |
| `Header 3` | (Section 정보 추출용) | 1단계 헤더 분할 결과 (H3) |
| `chunk_index` | `Chunk.overlap_index`| 세부 분할 시의 순서 인덱스 |
| `token_count` | `Chunk.token_count` | 본문 텍스트의 대략적인 토큰 수 |

## 유효성 검사 규칙 (Validation Rules)

- **코드 블록 무결성**: 청크 텍스트 내에서 ` ``` ` 기호의 개수는 짝수여야 함 (코드 블록이 닫히지 않고 잘리는 경우 방지).
- **크기 제약**: 모든 청크의 `len(content)`는 `chunk_size` (기본 2500자) 이하여야 함.
- **메타데이터 필수값**: `header_context`는 문서 시작부에 헤더가 없는 경우 최소한 "Main" 또는 문서 제목을 포함해야 함.
