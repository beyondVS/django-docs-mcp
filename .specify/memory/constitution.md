<!--
Sync Impact Report:
- 헌법 버전: 1.7.0 (uv 워크스페이스 의존성 관리 전략 추가)
- 수정 내용:
  - 2026-03-17: IV. 엔지니어링 표준에 'uv 워크스페이스 의존성 관리(Dependency Management)' 원칙 추가.
  - 2026-03-15: II. 아키텍처 원칙에 '아키텍처 충돌 해결 정책 (Conflict Resolution)' 추가 (Top-Down 기본, Bottom-Up 예외 원칙 명시).
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
5. **문서 단일 진실 공급원 (SSOT) 및 폴더 구조**: 프로젝트의 주요 데이터와 설계는 다음과 같이 관리되며, 모든 에이전트는 이를 엄격히 준수해야 합니다.
   - **`data_sources/`**: 크롤링된 마크다운 원본 및 벡터 데이터베이스. (대량의 데이터가 존재하므로, 에이전트는 전체 검색 시 이 폴더를 피하고 테스트나 로직 검증 시에만 명시적으로 접근해야 합니다.)
   - **`specs/_architecture/` (SSOT)**: 시스템 전체 아키텍처와 기획의 기준이 되는 단일 진실 공급원입니다. 주요 문서는 다음과 같습니다:
     - `project_proposal.md` (프로젝트 방향성 및 요구사항)
     - `architecture_design.md` (시스템 구조 및 데이터 흐름)
     - `embedding_strategy.md` (데이터 청킹 및 임베딩 전략)
     - `database_schema.md` (데이터베이스 구조)
     - `mcp_tools_contract.md` (외부 에이전트/서비스와의 API 규약 및 인터페이스 계약)
   - **`specs/###-title/`**: 개별 구현 작업(Task)을 위한 임시/진행형 명세 공간입니다.
   - **[아키텍처 충돌 해결 정책 및 동기화 의무]**
     - **Top-Down (기본 원칙)**: `specs/_architecture/`에 정의된 전체 시스템 아키텍처가 상위(Top) 기준입니다. 개별 기능(`specs/###-feature/`) 설계 중 충돌이 발생하면, 개별 기능 설계를 기본 아키텍처에 맞게 수정(Adapt)해야 합니다.
     - **Bottom-Up (예외 원칙)**: 기능 구현을 위해 기본 아키텍처의 확장이 불가피하거나 기존 설계의 결함이 발견된 경우, 무분별하게 아키텍처를 덮어쓰지 말고 명시적인 승인/검토를 거친 후 `specs/_architecture/` 문서를 선행 업데이트해야 합니다.

## III. 기술 표준 (Technical Standards)
1. **기술 스택**:
   - Language: Python 3.14 (Type 준수 의무)
   - Framework: Django (Backend), FastMCP (Serving)
   - Database: PostgreSQL + pgvector (HNSW 인덱스)
   - Embedding: BAAI/bge-m3 (1024차원)
2. **테스트 관리 원칙**:
   - 모든 서비스/패키지(`crawler`, `django_server` 등)는 자체 가상환경(`pyproject.toml`)을 소유하며, 관련 테스트 파일 역시 해당 디렉토리 내부의 `tests/` 폴더에서 독립적으로 관리한다. (루트 `tests/` 사용 금지)
3. **명시적 계약 (Explicit Contracts)**:
   - MCP 도구의 구체적인 입출력 규격은 분리된 API 계약서(`specs/_architecture/mcp_tools_contract.md`)를 엄격히 준수해야 합니다.

## IV. 엔지니어링 표준 (Engineering Excellence)
1. **Lint & Format**: **Ruff**를 사용하여 코드 스타일과 품질을 강제하며, 설정된 규칙을 반드시 통과해야 합니다.
2. **Type Safety**: 모든 함수의 인자와 반환값에 Type Hints를 반드시 적용합니다. (`mypy` 통과 권장)
3. **uv 워크스페이스 의존성 관리 (Dependency Management)**:
   - **중앙 집중식 개발 환경**: 모든 워크스페이스 멤버와 공통 개발 도구(Ruff, MyPy 등)는 루트 디렉토리에서 `uv sync --all-packages` 명령어를 통해 하나의 통합된 가상환경(`.venv`)으로 관리한다.
   - **역할 분리 (Root vs Members)**:
     - **프로젝트 루트 (`/pyproject.toml`)**: 모든 멤버가 공유하는 개발용 도구(`dev` 그룹)와 워크스페이스 전체에 공통으로 필요한 패키지만 선언한다.
     - **워크스페이스 멤버 (`/crawler/`, `/django_server/` 등)**: 각 서비스 실행에 필요한 최소한의 런타임 의존성만 해당 디렉토리의 `pyproject.toml`에 독립적으로 선언한다.
   - **배포 최적화**: Docker 빌드 및 프로덕션 배포 시에는 각 멤버 디렉토리에서 `uv sync`를 실행하여 해당 서비스에 필요한 최소 패키지만 설치함으로써 컨테이너 크기를 최적화하고 보안 노출을 줄인다.
4. **Documentation (문서화 및 주석 표준)**:
   - 내부/외부 공개 여부와 무관하게 **모든 클래스, 메서드, 함수**에는 기능의 목적, 인자(Args), 반환값(Returns), 예외(Raises)를 명시하는 **Google Style Docstring**을 반드시 작성합니다.
   - 코드 내의 **모든 주석과 Docstring은 반드시 한국어**로 작성하여 프로젝트의 한국어 최우선 원칙을 엄격히 준수합니다.
4. **Practical Async**: FastMCP 도구는 **비동기(`async`)**로 구현하며, Django는 프레임워크가 지원하는 범위 내에서 최대한 비동기(Async Views/ORM)를 활용합니다.

## V. 품질 및 보안 (Quality & Security)
1. **RAG 품질 보증**: 모든 검색 로직 변경 시 골든 데이터셋(정답셋)을 통한 검색 정확도(Recall/MRR)를 검증해야 합니다.
2. **데이터 수집 및 메타데이터 표준**:
   - 모든 외부 데이터 소스는 원본 출처(`source_url`)와 대상 버전(`target_version`)을 메타데이터로 포함하여 `data_sources/`에 마크다운 형태로 저장한다.
   - 수집된 마크다운 파일 상단에는 반드시 YAML Front Matter 형식을 사용하여 정형화된 메타데이터 블록을 삽입한다.
3. **관측 가능성 (Observability)**: 모든 MCP 도구 호출은 입력, 반환된 청크 ID, 검색 점수를 포함하여 구조화된 로그(JSON)를 남깁니다.
4. **최소 권한 및 보안**: 데이터베이스 및 API 접근은 최소 권한 원칙을 따르며, 사용자 입력 쿼리에 대한 살균(Sanitization)을 수행합니다.

## 거버넌스(Governance)
본 헌법은 Django Docs MCP 프로젝트의 근간이며, 모든 PR 및 코드 리뷰의 기준이 됩니다.
에이전트의 구체적인 행동 지침과 Git 워크플로우는 `AGENTS.md`를 따릅니다.

**버전**: 1.7.0 | **비준일**: 2026-03-12 | **최종 수정일**: 2026-03-17
