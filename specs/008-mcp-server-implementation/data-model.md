# 데이터 모델 (Data Model): MCP 서버 구현 (mcp-server-implementation)

## MCP 도구 입출력 (Tool IO)

### `search_django_docs` 입력 파라미터
- `query` (string, 필수): Django 관련 질문 또는 검색 키워드.

### `search_django_docs` 출력 (Search Result)
하이브리드 검색 및 리랭크를 거친 후 반환되는 데이터 구조입니다.

| 필드 | 타입 | 설명 |
| :--- | :--- | :--- |
| `title` | string | 문서 제목 (예: "Models | Django documentation") |
| `content` | string | 검색된 마크다운 문서 파편 (Chunk) |
| `url` | string | 원본 문서 URL (있는 경우) |
| `score` | float | 리랭크된 검색 관련성 점수 (MaxSim) |
| `metadata` | object | 추가 정보 (소스 버전, 청크 ID 등) |

---

## 검색 로그 (Search Log)

요구사항 `FR-005`에 따라 기록되는 로그 엔티티입니다. `SearchLog`는 별도의 DB 테이블로 관리하지 않고, 초기 구현에서는 표준 출력(stdout) 또는 별도의 로그 파일에 JSON 구조로 기록합니다.

### 로그 속성
- `timestamp`: ISO-8601 형식의 요청 시간.
- `query`: LLM으로부터 전달받은 원본 검색어.
- `results_count`: 검색된 총 결과 수.
- `top_results`: 상위 3개 결과의 `title` 및 `score` 리스트.
- `chunk_ids`: 반환된 문서 조각(Chunk)의 고유 식별자 리스트 (헌법 V.3 준수).
- `agent_strategy_guide`: 도구 설명에 포함된 가이드 적용 여부.

---

## 예외 상태 (Error States)
- `EMPTY_RESULT`: 검색 결과가 없는 경우 LLM에게 반환할 특수 메시지.
- `DJANGO_INIT_ERROR`: Django 환경 초기화 실패 시 반환할 시스템 오류.
