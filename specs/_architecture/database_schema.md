# 데이터베이스 스키마 정의서 (DB Schema Spec)

관리 편의성(정규화)과 검색 속도(비정규화)를 융합한 3단계 계층 구조를 채택합니다.

## 1. 계층 구조 요약

데이터는 `출처(Source)` -> `개별 문서(Document)` -> `파편 및 벡터(Chunk)` 의 3단계로 관리됩니다.

### 테이블 1: Source (출처 그룹)

| 필드명 (Django Model) | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | BigAutoField | PK |
| name | CharField | 출처명 (예: "Django Official Docs") |
| base_url | URLField | 루트 URL |

### 테이블 2: Document (개별 문서)

| 필드명 (Django Model) | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | BigAutoField | PK |
| source | ForeignKey(Source) | 1:N 연결 |
| title | CharField | 문서 제목 |
| original_url | URLField | 개별 원본 URL |
| uploaded_at | DateTimeField | 등록 시간 |

### 테이블 3: Chunk (문서 조각 및 벡터 - 검색 핵심 테이블)

| 필드명 (Django Model) | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | UUIDField | PK |
| document | ForeignKey(Document) | 원본 문서 연결 (JOIN 검색 지양) |
| content | TextField | 실제 텍스트 내용 |
| embedding | VectorField(dim=1024) | bge-m3 기준 벡터 데이터 |
| target_version | CharField | **[비정규화 필드]** 타겟 Django 버전 |
| document_type | CharField | **[비정규화 필드]** 문서 종류 |
| extra_meta | JSONField | 규격화되지 않은 추가 메타데이터 보관 |

## 2. 인덱스 (Index) 전략

* `embedding` 필드에 **HNSW 인덱스** 적용 (빠른 근사 최근접 이웃 검색 지원).
* `target_version`, `document_type` 필드에 **B-Tree 인덱스**를 걸어 벡터 필터링(Metadata Filtering) 속도 향상.
