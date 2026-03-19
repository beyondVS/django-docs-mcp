<!--
Sync Impact Report:
- 헌법 버전: 1.9.1 (아키텍처 문서의 지속적 진화 원칙 추가)
- 수정 내용:
  - 2026-03-18: II. 아키텍처 원칙에 '아키텍처 문서의 지속적 진화' 항목 추가.
- 업데이트 확인 템플릿:
  - .specify/templates/plan-template.md (유효)
  - .specify/templates/spec-template.md (유효)
  - .specify/templates/tasks-template.md (유효)
-->

# Django Docs MCP 헌법(Constitution)

## 프로젝트 개요
AI 에이전트가 환각(Hallucination) 없이 Django 공식 가이드와 코드를 정확히 검색할 수 있도록 지원하는 RAG(검색 증강 생성) 기반 지식 통합 MCP(Model Context Protocol) 서버 구축 프로젝트.

## I. 핵심 철학 (Core Philosophy)
1. **실용주의 (Pragmatism)**: Over-engineering을 엄격히 금지하며 가장 단순하고 명확한 해결책을 우선합니다. 단, 단순함이 구조적 안정성, 패키징 정합성, 장기적인 유지보수성이라는 엔지니어링 표준을 훼손해서는 안 됩니다. (예: 단순 도구는 Flat 구조를 지향하되, 복잡한 서버 프로젝트는 정석적인 레이아웃을 채택함)
2. **한국어 최우선 (Language First)**: 모든 대화, 문서, 커밋 메시지는 한국어를 사용합니다. 단, 변수명/클래스명 등 코드 식별자는 영어를 사용합니다.

## II. 아키텍처 원칙 (Architectural Principles)
1. **컨테이너 우선 (Container-First)**: 모든 로컬 개발 환경과 인프라는 Docker 및 Docker Compose를 통해 일관되게 실행되어야 합니다.
2. **책임 및 컴포넌트 분리 (Separation of Concerns)**: 외부 데이터 수집(Crawler), 데이터 관리(Django), AI 에이전트 서빙(FastMCP) 역할을 엄격히 분리합니다.
3. **데이터 계층화 (Data Hierarchy)**: 지식 데이터는 출처(Source) > 개별 문서(Document) > 파편(Chunk)의 3단계 구조를 엄격히 준수합니다.
4. **의미론적 청킹 (Strict Semantic Chunking)**: 마크다운 구조 기반 분할을 적용하며, 파이썬 코드 블록은 절대 분할하지 않습니다.
5. **하이브리드 리트리벌 (Hybrid Retrieval & Reranking)**: 단순 벡터 검색을 넘어 BM25 키워드 검색과 Reranking 파이프라인을 필수적으로 결합하여 검색 정밀도를 확보합니다.
6. **아키텍처 문서의 지속적 진화 (Continuous Architecture Documentation)**: 시스템의 중대한 설계 결정, 신규 모듈 도입 또는 구조적 변화가 발생할 경우, 반드시 `specs/_architecture/` 디렉터리에 새로운 설계 문서를 추가하거나 기존 문서를 업데이트하여 시스템의 '살아있는 설계도'를 유지해야 합니다.

## III. 기술 표준 (Technical Standards)
1. **기술 스택**:
   - Language: Python 3.14 (Type 준수 의무)
   - Framework: Django (Backend), FastMCP (Serving)
   - Database: PostgreSQL (ParadeDB 공식 이미지: pgvector + pg_search 포함)
   - Embedding: BAAI/bge-m3 (1024차원, ONNX Runtime 가속)
   - Reranker: gpahal/bge-m3-onnx-int8 (Late Interaction / ONNX INT8)
2. **테스트 관리 원칙**:
   - 모든 서비스/패키지(`crawler`, `django_server` 등)는 자체 가상환경(`pyproject.toml`)을 소유하며, 관련 테스트 파일 역시 해당 디렉토리 내부의 `tests/` 폴더에서 독립적으로 관리한다. (루트 `tests/` 사용 금지)
3. **명시적 계약 (Explicit Contracts)**:
   - MCP 도구의 구체적인 입출력 규격은 분리된 API 계약서(`specs/_architecture/mcp_tools_contract.md`)를 엄격히 준수해야 합니다.

## IV. 엔지니어링 표준 (Engineering Excellence)
1. **Lint & Format**: **Ruff**를 사용하여 코드 스타일과 품질을 강제하며, 설정된 규칙을 반드시 통과해야 합니다.
2. **Type Safety**: 모든 함수의 인자와 반환값에 Type Hints를 반드시 적용합니다. (`mypy` 통과 권장)
3. **uv 워크스페이스 의존성 관리 (Dependency Management)**:
   - **중앙 집중식 개발 환경**: 모든 워크스페이스 멤버와 공통 개발 도구(Ruff, MyPy 등)는 루트 디렉토리에서 `uv sync --all-packages` 명령어를 통해 하나의 통합된 가상환경(`.venv`)으로 관리한다.
   - **패키지 관리 원칙**: 새로운 의존성 추가 시 `uv add` 명령어로 최신 안정 버전을 먼저 설치한다. 이후 `pyproject.toml`에서 버전 표기를 `~= x.y.z` 형식으로 수동 조정하여 호환 가능한 패치 버전만 허용함으로써 보안성과 API 안정성을 동시에 확보한다.
   - **재현성 보장**: 모든 환경의 실제 패키지 버전 일치는 `uv.lock` 파일에 전적으로 의존한다.
   - **역할 분리 (Root vs Members)**:
     - **프로젝트 루트 (`/pyproject.toml`)**: 모든 멤버가 공유하는 개발용 도구(`dev` 그룹)와 워크스페이스 전체에 공통으로 필요한 패키지만 선언한다.
     - **워크스페이스 멤버 (`/crawler/`, `/django_server/` 등)**: 각 서비스 실행에 필요한 최소한의 런타임 의존성만 해당 디렉토리의 `pyproject.toml`에 독립적으로 선언한다.
   - **배포 최적화**: Docker 빌드 및 프로덕션 배포 시에는 각 멤버 디렉토리에서 `uv sync`를 실행하여 해당 서비스에 필요한 최소 패키지만 설치함으로써 컨테이너 크기를 최적화하고 보안 노출을 줄인다.
4. **Documentation (문서화 및 주석 표준)**:
   - 내부/외부 공개 여부와 무관하게 **모든 클래, 메서드, 함수**에는 기능의 목적, 인자(Args), 반환값(Returns), 예외(Raises)를 명시하는 **Google Style Docstring**을 반드시 작성합니다.
   - 코드 내의 **모든 주석과 Docstring은 반드시 한국어**로 작성하여 프로젝트의 한국어 최우선 원칙을 엄격히 준수합니다.
4. **Practical Async**: FastMCP 도구는 **비동기(`async`)**로 구현하며, Django는 프레임워크가 지원하는 범위 내에서 최대한 비동기(Async Views/ORM)를 활용합니다.
5. **Django 마이그레이션 관리 원칙 (Migration Management)**:
   - **도구 기반 생성**: AI 에이전트는 마이그레이션 파일을 직접 작성하거나 추측하여 생성해서는 안 되며, 반드시 `manage.py makemigrations` 명령어를 실행하여 Django가 직접 파일을 생성하게 해야 합니다.
   - **ORM 우선주의**: 인덱스(BM25Index, HnswIndex 등), 제약 조건, 확장 설정 등은 가급적 `models.py`의 `Meta` 클래스나 Django 제공 클래스를 통해 정의하여 Raw SQL 사용을 최소화합니다. 이는 스키마의 투명성과 유지보수성을 확보하기 위함입니다.
   - **동기화 검증**: 마이그레이션 생성 후에는 `models.py`의 모든 세부 설정(`help_text`, `choices` 등)이 마이그레이션 파일에 정확히 반영되었는지 확인해야 합니다.
   - **데이터 마이그레이션 예외**: 단순 스키마 변경이 아닌 데이터 변환이 필요한 경우에만 빈 마이그레이션(`--empty`)을 생성한 후 수동으로 로직을 작성합니다.

## V. 품질 및 보안 (Quality & Security)
1. **RAG 품질 보증 (Hybrid Retrieval & Evaluation)**:
   - 모든 검색 서비스는 **벡터 검색(pgvector)과 키워드 검색(BM25)**을 결합하고, RRF(Reciprocal Rank Fusion)를 통해 상위 후보를 추출해야 합니다.
   - 최종 결과 반환 전, **ONNX 기반 Reranker**를 통해 문맥적 관련성을 재검증하는 과정을 필수적으로 포함합니다.
   - **평가 표준**: `evaluation_framework.md`에 정의된 **MRR(0.75 이상)** 및 **Hit Rate @5(0.90 이상)** 지표를 골든 데이터셋을 통해 주기적으로 측정하여 품질 퇴보(Regression)를 방지해야 합니다.
2. **데이터 수집 및 메타데이터 표준**:
   - 모든 외부 데이터 소스는 원본 출처(`source_url`)와 대상 버전(`target_version`)을 메타데이터로 포함하여 `data_sources/`에 마크다운 형태로 저장한다.
   - 수집된 마크다운 파일 상단에는 반드시 YAML Front Matter 형식을 사용하여 정형화된 메타데이터 블록을 삽입한다.
3. **관측 가능성 (Observability)**: 모든 MCP 도구 호출은 입력, 반환된 청크 ID, 검색 점수(Rerank Score)를 포함하여 구조화된 로그(JSON)를 남깁니다.
4. **최소 권한 및 보안**: 데이터베이스 및 API 접근은 최소 권한 원칙을 따르며, 사용자 입력 쿼리에 대한 살균(Sanitization)을 수행합니다.

## 거버넌스(Governance)
본 헌법은 Django Docs MCP 프로젝트의 근간이며, 모든 PR 및 코드 리뷰의 기준이 됩니다.
에이전트의 구체적인 행동 지침과 Git 워크플로우는 `AGENTS.md`를 따릅니다.

**버전**: 1.9.1 | **비준일**: 2026-03-12 | **최종 수정일**: 2026-03-18
