# Django Docs Search MCP Server

AI 에이전트가 Django 공식 문서를 정확하게 검색하고 에이전틱(Agentic)하게 지식을 활용할 수 있도록 지원하는 MCP 서버입니다.

## 🚀 주요 기능
- **하이브리드 검색**: ParadeDB(BM25)와 pgvector를 결합한 고정밀 검색.
- **MaxSim 리랭킹**: 문맥적 관련성을 재검증하여 최적의 결과 반환.
- **에이전틱 가이드**: LLM이 스스로 검색 전략을 최적화하도록 돕는 도구 설명 포함.
- **상세 로깅**: 헌법 V.3을 준수하는 구조화된 JSON 로그(청크 ID 포함).

## 🛠 설치 및 실행

### 전제 조건
- Python 3.13
- `uv` 패키지 관리자
- `django_server`의 DB 및 인덱싱 데이터.

### 의존성 설치
```bash
uv sync --all-packages
```

### 서버 실행
```bash
uv run python mcp_server/main.py
```

### 도구 테스트 (CLI)
```bash
uv run fastmcp call mcp_server/main.py search_django_docs query="how to use custom middleware"
```

## 🛠 MCP 도구 상세

### `search_django_docs`
Django 지식 베이스를 검색합니다.
- **입력**: `query` (필수), `django_version` (기본 "5.2"), `max_results` (기본 5)
- **출력**: 마크다운 형식의 결과 리스트.

## 📜 라이선스
이 프로젝트는 프로젝트 헌법(Constitution)을 준수합니다.
