# 데이터베이스 스키마 정의서 (DB Schema Spec)

> 💡 **스키마 설계 원칙**
> 관리의 편의성을 위한 **정규화**와 검색 속도를 극대화하기 위한 **비정규화**를 융합하여,
> 유연하고 빠른 3단계 계층 구조를 채택했습니다.
> 백엔드 인프라는 ParadeDB를 기반으로 `pgvector`와 `pg_search`를 적극 활용합니다.

---

## 1. 계층 구조 요약

시스템 데이터는 논리적 크기에 따라 `개별 문서(Document)` → `섹션(Section)` → `청크(Chunk)`의 3단계로 관리됩니다.

### 1.1 테이블 1: Document (개별 문서)
원본 문서 전체의 메타데이터를 관리하는 최상위 테이블입니다.

| 필드명 (Django Model) | 데이터 타입 | 설명 및 제약 사항 |
| :--- | :--- | :--- |
| `id` | UUIDField | PK (자동 생성) |
| `title` | CharField | 문서 제목 (YAML Front Matter 또는 파일명 추출) |
| `target_version` | CharField | 대상 프레임워크 버전 (예: "5.2") |
| `category` | CharField | 문서 카테고리 (예: "Tutorials", "Reference") |
| `source_path` | CharField | 로컬 파일 시스템의 절대 경로 (**Unique Index**) |
| `source_url` | URLField | 공식 문서 웹 URL (선택 사항) |
| `status` | CharField | 검색 활성화 상태 ("Active" 또는 "Inactive") |
| `created_at` / `updated_at` | DateTimeField | 레코드 생성 및 최종 수정 시각 |

### 1.2 테이블 2: Section (문서 내 섹션)
문서 내의 논리적인 단락(헤더)을 관리하여 구조적 문맥을 유지합니다.

| 필드명 (Django Model) | 데이터 타입 | 설명 및 제약 사항 |
| :--- | :--- | :--- |
| `id` | UUIDField | PK |
| `document` | ForeignKey | `Document` 테이블과 1:N 연결 (CASCADE 삭제) |
| `title` | CharField | 섹션 제목 (마크다운 헤더 텍스트) |
| `level` | IntegerField | 헤더의 논리적 깊이 (1: H1, 2: H2, 3: H3 등) |
| `order` | IntegerField | 부모 문서 내에서의 섹션 순서 |

### 1.3 테이블 3: Chunk (텍스트 조각 및 벡터 - 검색 핵심)
실제 검색 엔진이 스캔하고 임베딩 연산을 수행하는 가장 중요한 말단 테이블입니다.

| 필드명 (Django Model) | 데이터 타입 | 설명 및 제약 사항 |
| :--- | :--- | :--- |
| `id` | UUIDField | PK |
| `section` | ForeignKey | `Section` 테이블과 N:1 연결 (문맥 정보 보존용) |
| `content` | TextField | 분할된 실제 텍스트 내용 (**BM25 인덱싱 대상**) |
| `embedding` | VectorField | 1,024차원 Dense 벡터 (**HNSW 인덱싱 대상**) |
| **`multi_vector_low_dim`** | **BinaryField** | **Late Interaction 리랭킹용 압축 벡터** (128차원 x N 토큰, int8 양자화) |
| `token_count` | IntegerField | 실제 유효 토큰 수 (바이너리 역직렬화 가이드) |
| `overlap_index` | IntegerField | 문맥 중첩(Overlap) 분할 시의 청크 순서 인덱스 |

---

## 2. 데이터베이스 인덱스 (Index) 전략

초고속 하이브리드 검색을 지원하기 위해 용도별로 최적화된 인덱스를 구성합니다.

### 2.1 벡터 인덱스 (Vector Index)
*   **유형:** HNSW (Hierarchical Navigable Small World)
*   **적용 대상:** `Chunk.embedding` 컬럼
*   **설계 목적:** 수만 개의 벡터 간 코사인 유사도(Cosine Similarity)를 밀리초 단위로 고속 검색하기 위함입니다.
*   **파라미터 튜닝:** `m=16`, `ef_construction=64`
    (데이터의 규모가 커지면 재현율 확보를 위해 상향 조정 가능)

### 2.2 하이브리드 검색 인덱스 (BM25 Index)
*   **유형:** ParadeDB 확장 모듈인 `pg_search` 기반
*   **적용 대상:** `Chunk.content` 컬럼
*   **설계 목적:** 단어 출현 빈도 기반의 정밀 키워드 검색(BM25) 및 불용어 필터링을 지원합니다.
*   **특이사항:** 애플리케이션 레벨이 아닌 SQL 레벨에서 벡터 검색 결과와 RRF(Reciprocal Rank Fusion) 쿼리를 결합하여 네트워크 지연을 최소화합니다.

### 2.3 리랭킹용 바이너리 저장 규격 (Multi-vector Packing)
`multi_vector_low_dim` 필드는 검색 시 빠른 로드와 연산을 위해 특수한 바이너리 포맷을 따릅니다.

*   **구조:** `[Token Count (2B)][Vector Data (N * 128B)]`
*   **압축 기법:**
    1.  **Matryoshka Slicing:** 1,024차원의 상위 128차원만 추출.
    2.  **Scalar Quantization:** float32 값을 -128~127 범위의 int8 정수로 캐스팅.
*   **이점:** 원본 대비 저장 용량을 **32배 압축**하여 DB I/O 부하를 최소화합니다.

### 2.4 메타데이터 필터링 및 정합성 인덱스
*   **B-Tree Index:** `Document.target_version`, `Document.category` 컬럼 등에 적용합니다.
    특정 버전이나 카테고리로 필터를 걸 때 검색 범위를 대폭 좁혀 성능을 최적화합니다.
*   **Unique 제약 조건:** `source_path`와 `target_version` 조합에 Unique 제약을 설정합니다.
    이는 수집 파이프라인 재실행 시 중복 적재를 방지하고, 안전한 `Upsert` 로직을 지원하기 위함입니다.
