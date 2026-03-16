# 데이터 모델 정의 (Data Model)

`django_server`에서 관리하는 기술 문서의 계층 구조와 벡터 저장 방식을 정의합니다.

## 1. 개요
프로젝트 헌법의 '데이터 계층화' 원칙을 준수하며, 검색의 정밀도를 위해 `Section` 단위를 추가로 포함한 3.5단계 구조를 제안합니다.

- **Document (문서)**: 하나의 완전한 마크다운 파일 (예: Django Tutorial Part 1).
- **Section (섹션)**: 문서 내의 H2, H3 헤더 기반 논리적 구분.
- **Chunk (조각)**: 실제 벡터 검색의 최소 단위 (500~800 토큰).

## 2. 엔티티 상세 (Entity Details)

### 2.1 Document
- `id`: UUID (Primary Key)
- `title`: String (문서 제목)
- `target_version`: String (Django 대상 버전, 예: "5.0", "4.2")
- `category`: String (문서 유형, 예: "Tutorial", "Reference")
- `source_path`: String (로컬 파일 시스템 경로)
- `source_url`: String (원본 공식 문서 URL)
- `status`: String (Enum: "Active", "Inactive")
- `created_at`: DateTime
- `updated_at`: DateTime

### 2.2 Section
- `id`: UUID (Primary Key)
- `document`: ForeignKey (Document)
- `title`: String (섹션 헤더 제목)
- `level`: Integer (헤더 레벨, 2 또는 3)
- `order`: Integer (문서 내 순서)

### 2.3 Chunk
- `id`: UUID (Primary Key)
- `section`: ForeignKey (Section)
- `content`: Text (실제 텍스트 본문)
- `embedding`: Vector(1024) (bge-m3 모델을 통한 벡터 표현)
- `token_count`: Integer (토큰 수)
- `overlap_index`: Integer (오버랩 여부 및 순서)
- `created_at`: DateTime

## 3. 관계 및 제약 조건 (Relationships & Constraints)
- **일대다 관계**: Document(1) -> Section(N), Section(1) -> Chunk(N).
- **고유성**: `Document`는 `source_path`와 `target_version` 조합으로 유니크해야 함 (Upsert 기준).
- **인덱스**:
  - `Chunk.embedding`: `pgvector`의 **HNSW (Hierarchical Navigable Small World)** 인덱스 적용 (코사인 유사도 검색 최적화).
  - `Document.target_version`, `Document.category`: 빠른 필터링을 위한 B-Tree 인덱스 적용.

## 4. 유효성 검사 규칙 (Validation Rules)
- **청킹 사이즈**: `token_count`는 최대 1000을 넘지 않도록 제한 (오버랩 포함).
- **코드 블록**: `content` 내에 ` ``` ` 쌍이 일치하는지 확인 (잘린 코드 블록 방지).
- **버전 형식**: Semantic Versioning 또는 "X.Y" 형식 준수.
