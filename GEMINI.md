# django-docs-mcp 개발 가이드라인 (Gemini Context)

모든 기능 계획서에서 자동 생성되었습니다. 최종 업데이트: 2026-03-24

## 1. 전역 지침 및 핵심 규칙 (수동 관리)

### 전역 지침 참조 (필수)
작업 시작 전, 다음 공통 문서들을 반드시 읽고 컨텍스트를 확보하십시오.
1. **원칙 및 표준:** [.specify/memory/constitution.md](.specify/memory/constitution.md)
2. **에이전트 역할 및 지침:** [AGENTS.md](AGENTS.md)

### 우선순위 및 Gemini 특화 규칙
- **우선순위:** `constitution.md` > `AGENTS.md` > `GEMINI.md`
- **컨텍스트 최적화:** `data_sources/` 디렉터리에는 대량의 데이터가 포함될 수 있습니다. 전체 프로젝트 대상 검색(`grep`, `glob`) 시 불필요한 토큰 낭비를 막기 위해 이 폴더는 가급적 검색 대상에서 제외하고, 테스트 데이터 생성 등 **필요한 경우에만 특정 파일을 명시적으로 지정하여 읽으십시오.**

---

## 2. 프로젝트 현황 (자동 생성)

## 활성 기술 스택
- Python 3.13 + `django-paradedb~=0.4.0`, `onnxruntime`, `optimum`, `numpy` (005-optimize-search-rerank)
- PostgreSQL (ParadeDB: pg_search + pgvector), `bytea` 필드를 통한 멀티벡터 저장 (005-optimize-search-rerank)
- Python 3.13 + `docutils` (RST 파싱 및 Markdown 변환), `git` CLI (저장소 클론) (006-crawl-django-52-docs)
- 로컬 파일 시스템 (`data_sources/django-5.2-docs/`) (006-crawl-django-52-docs)
- Python 3.13 + `httpx` (Async HTTP), `beautifulsoup4` (HTML Parsing), `markdownify` (MD Conversion), `tqdm` (UI), `tenacity` (Retry) (007-crawl-django-web)
- 로컬 파일 시스템 (Temporary HTML & Final Markdown) (007-crawl-django-web)

- Python 3.13 + Django 5.2 (004-hybrid-search-rerank)
- PostgreSQL + pgvector & pg_search (004-hybrid-search-rerank)
- FastMCP (004-hybrid-search-rerank)
- BAAI/bge-m3 Embedding & Reranker (004-hybrid-search-rerank)

## 프로젝트 구조

```text
D:\Projects\Private\django-docs-mcp\
├── crawler/                # Django 문서 크롤러 (Readability-lxml)
├── django_server/          # Django 검색 서버 및 관리 도구
│   ├── src/                # 소스 코드 (Core, Documents)
│   └── tests/              # 단위 및 통합 테스트
├── mcp_server/             # AI 에이전트 서빙용 FastMCP 서버
├── data_sources/           # 크롤링된 마크다운 원본 데이터
└── specs/                  # 프로젝트 설계 및 피처별 작업 문서
```

## 명령어

- **워크스페이스 전체 동기화**: `uv sync --all-packages` (루트에서 실행)
- **전체 품질 검사 (Lint/Type)**: `uv run ruff check .` 및 `uv run mypy .` (루트에서 실행)
- **Django 서버 실행**: `cd django_server && uv run python src/manage.py runserver`
- **마이그레이션 생성**: `cd django_server && uv run python src/manage.py makemigrations`
- **테스트 실행 (Django)**: `cd django_server && uv run pytest`
- **크롤러 실행**: `cd crawler && uv run python orm_cookbook.py`
- **검색 품질 평가**: `cd django_server && uv run python scripts/evaluate_search.py`
- **MCP 서버 실행 (Serving)**: `cd mcp_server && uv run python -m mcp_server`

## 코드 스타일

- **Python**: Google Style Docstring 준수 및 모든 주석/문서 한국어 작성.
- **Linting**: Ruff를 통한 코드 품질 및 스타일 체크.
- **Type Safety**: 모든 함수와 메서드에 명시적인 Type Hints 적용.

## 최근 변경 사항
- 007-crawl-django-web: Added Python 3.13 + `httpx` (Async HTTP), `beautifulsoup4` (HTML Parsing), `markdownify` (MD Conversion), `tqdm` (UI), `tenacity` (Retry)
- 006-crawl-django-52-docs: Added Python 3.13 + `docutils` (RST 파싱 및 Markdown 변환), `git` CLI (저장소 클론)
- 005-optimize-search-rerank: Added Python 3.13 + `django-paradedb~=0.4.0`, `onnxruntime`, `optimum`, `numpy`


---
