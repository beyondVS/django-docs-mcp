# 퀵스타트 (Quickstart): MCP 서버 구현 (mcp-server-implementation)

본 문서는 `mcp_server` 프로젝트를 설정하고 실행하기 위한 빠른 가이드를 제공합니다.

## 전제 조건 (Prerequisites)
- Python 3.13
- `uv` 패키지 관리자
- 실행 중인 `django_server` 데이터베이스 (PostgreSQL/ParadeDB) 및 인덱싱된 데이터.

## 설치 (Installation)
1. 루트 디렉토리에서 의존성을 동기화합니다.
   ```bash
   uv sync --all-packages
   ```

2. `mcp_server/` 폴더로 이동합니다. (필요한 경우)

## 실행 (Execution)
MCP 서버를 개발 모드로 실행하여 도구를 테스트합니다.

```bash
uv run python mcp_server/main.py
```

또는 MCP Inspector를 사용하여 도구 인터페이스를 직접 검증할 수 있습니다.
```bash
npx @modelcontextprotocol/inspector uv run python mcp_server/main.py
```

## 에이전틱 서치 테스트 (Testing)
MCP 클라이언트(예: Claude Desktop)에서 다음과 같이 요청하여 도구가 올바르게 작동하는지 확인합니다:
- "Django 5.2에서 새롭게 추가된 데이터베이스 백엔드는 무엇인가요?"
- "검색 결과를 바탕으로 `search_django_docs`를 한 번 더 호출해서 더 자세한 코드를 보여주세요."

서버 로그(`stdout`)에 다음과 같은 JSON이 찍히는지 확인합니다:
```json
{"event": "tool_call", "tool": "search_django_docs", "query": "...", "top_score": 0.95, ...}
```
