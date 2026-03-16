# 조사 보고서: django-server-core (Outline & Research)

**기능 브랜치**: `002-django-server-core`
**일자**: 2026-03-16
**상태**: 완료

## 1. 기술적 미지수 및 조사 작업 (Technical Unknowns)

### 1.1 Django + pgvector 연동 라이브러리
- **조사 목적**: Django ORM과 `pgvector`를 가장 깔끔하게 연동할 수 있는 라이브러리 선정.
- **결정(Decision)**: `pgvector-python`의 Django 통합 라이브러리(`pgvector.django.VectorField`) 사용.
- **근거(Rationale)**:
  - `pgvector` 공식 메인테이너가 관리하는 라이브러리로 신뢰성이 높음.
  - Django의 `Field` 클래스를 상속받아 마이그레이션과 쿼리셋 연동이 매우 자연스러움.
  - L2 거리, 코사인 유사도, 내적(Inner Product) 검색을 내장 함수로 지원함.
- **고려된 대안**: `django-pgvector` (업데이트가 정체되어 최신 pgvector 버전 기능 지원이 미흡함).

### 1.2 BAAI/bge-m3 임베딩 모델 서빙 전략
- **조사 목적**: Django 컨테이너 내에서 1024차원의 bge-m3 모델을 효율적으로 로드하고 추론하는 방법.
- **결정(Decision)**: `sentence-transformers` 라이브러리를 사용하여 Django 실행 시 모델을 로컬(컨테이너 내 볼륨)에 캐싱하고 싱글톤(Singleton) 패턴으로 메모리에 로드.
- **근거(Rationale)**:
  - 외부 API 호출 지연 없이 로컬에서 고속 추론 가능.
  - GPU가 없는 로컬/테스트 환경에서도 CPU 추론 속도가 준수함.
  - 1024차원 벡터 생성 및 한국어 처리 성능이 검증됨.
- **고려된 대안**: 별도의 Embedding Microservice (Phase 1에서는 오버엔지니어링으로 판단하여 제외).

### 1.3 마크다운 청킹(Chunking) 로직 구현
- **조사 목적**: H2/H3 헤더를 존중하고 파이썬 코드 블록을 절대 자르지 않는 정교한 분할기 구현.
- **결정(Decision)**: `langchain-text-splitters`의 `MarkdownHeaderTextSplitter`를 기본으로 사용하고, 코드 블록 보존을 위한 커스텀 정규식 후처리를 추가함.
- **근거(Rationale)**:
  - 마크다운 구조(Header) 기반 분할을 기본 지원하여 문맥 보존에 유리함.
  - 500~800 토큰 범위 및 10% 오버랩 설정을 세밀하게 제어 가능.
- **고려된 대안**: 단순 Regex 기반 분할 (복잡한 마크다운 구조 대응이 어렵고 유지보수성이 낮음).

### 1.4 PostgreSQL 드라이버: psycopg3[binary]
- **조사 목적**: Django 5.2와 PostgreSQL 간의 가장 빠르고 안정적인 연결 방식 확인.
- **결정(Decision)**: `psycopg[binary] >= 3.2.x` 사용.
- **근거(Rationale)**:
  - **비동기 기본 지원**: `psycopg 3`는 Python의 `async/await`를 기본 지원하여 Django 5.x의 비동기 기능을 최대로 활용 가능함.
  - **성능 최적화**: `[binary]` 옵션은 미리 빌드된 C 확장 프로그램을 포함하여, 컴파일 과정 없이 즉시 고성능 DB 연동을 보장함.
  - **Django 5.2 호환성**: Django 5.2는 `psycopg 3`를 공식 지원하며 권장하고 있음.
- **고려된 대안**: `psycopg2` (레거시 드라이버로 비동기 지원이 미흡하고 성능이 낮음).

## 2. 베스트 프랙티스 (Best Practices)

### 2.1 Django Custom Management Command
- `manage.py ingest_docs` 구현 시 `BaseCommand`를 상속받아 구조화된 진행률 표시(tqdm 등)와 로깅을 포함함.
- 개별 문서 단위로 `transaction.atomic`을 적용하여 부분 성공(Partial Success)을 보장함.

### 2.2 Playground UI/UX
- Django Template과 HTMX를 결합하여 페이지 새로고침 없는 검색 결과 실시간 렌더링 구현.
- 검색 결과 상단에 유사도 점수(Cosine Similarity)를 시각적으로 강조함.

### 2.3 Docker Compose DB 공유
- `mcp_server`와 `django_server`가 동일한 `db` 서비스를 바라보도록 구성하고, `POSTGRES_DB` 환경변수를 통해 동일한 데이터베이스 내에서 스키마/테이블을 공유함.

## 3. 결정 요약 (Summary of Decisions)

| 항목 | 선택된 기술/방안 | 핵심 이유 |
| :--- | :--- | :--- |
| **Vector Library** | `pgvector-python` | 공식 지원, Django ORM 친화적 |
| **Embedding Engine** | `sentence-transformers` | 로컬 고속 추론, bge-m3 최적화 |
| **Parsing Logic** | `MarkdownHeaderTextSplitter` | 구조 기반 분할, 문맥 유지 탁월 |
| **Admin UI** | `Django Admin` + `HTMX` | 빠른 프로토타이핑, 인터랙티브 검색 |
