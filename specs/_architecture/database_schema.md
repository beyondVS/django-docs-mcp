# 데이터베이스 스키마 정의서 (DB Schema Spec)

관리 편의성(정규화)과 검색 속도(비정규화)를 융합한 3단계 계층 구조를 채택하여 구현되었습니다.

## 1. 계층 구조 요약

데이터는 `개별 문서(Document)` -> `섹션(Section)` -> `청크(Chunk)` 의 3단계로 관리됩니다.

### 테이블 1: Document (개별 문서)

| 필드명 (Django Model) | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | UUIDField | PK (자동 생성) |
| title | CharField | 문서 제목 (YAML Front Matter 또는 파일명) |
| target_version | CharField | 대상 Django 버전 (예: "5.2") |
| category | CharField | 문서 카테고리 (예: "Tutorials", "Reference") |
| source_path | CharField | 로컬 파일 시스템의 절대 경로 (Unique Index) |
| source_url | URLField | 공식 Django 문서 웹 URL (선택 사항) |
| status | CharField | 검색 활성화 상태 ("Active", "Inactive") |
| created_at / updated_at | DateTimeField | 생성 및 수정 시각 |

### 테이블 2: Section (문서 내 섹션)

| 필드명 (Django Model) | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | UUIDField | PK |
| document | ForeignKey(Document) | 1:N 연결 (CASCADE 삭제) |
| title | CharField | 섹션 제목 (헤더 텍스트) |
| level | IntegerField | 헤더 깊이 (1: H1, 2: H2, 3: H3 등) |
| order | IntegerField | 문서 내 섹션 순서 |

### 테이블 3: Chunk (텍스트 조각 및 벡터 - 검색 핵심 테이블)

| 필드명 (Django Model) | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | UUIDField | PK |
| section | ForeignKey(Section) | N:1 연결 (섹션 정보 포함) |
| content | TextField | 실제 텍스트 내용 (문맥 주입 포함) |
| embedding | VectorField(dim=1024) | BGE-M3 기준 1024차원 벡터 데이터 |
| token_count | IntegerField | 대략적인 토큰 수 |
| overlap_index | IntegerField | 중첩 분할 시의 인덱스 |

## 2. 인덱스 (Index) 전략

*   **벡터 검색**: `Chunk.embedding` 필드에 **HNSW 인덱스**(`chunk_embedding_hnsw_idx`)를 적용하여 코사인 유사도 기반 고속 검색을 지원합니다.
*   **메타데이터 필터링**: `Document.target_version`, `Document.category` 등에 인덱스를 설정하여 특정 버전/카테고리에 국한된 검색 성능을 최적화합니다.
*   **Unique 제약**: `source_path`와 `target_version` 조합에 Unique 제약을 걸어 중복 적재를 방지(Upsert 로직 지원)합니다.
