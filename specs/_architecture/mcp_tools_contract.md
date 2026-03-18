# MCP Tools Contract

이 문서는 AI 에이전트와 MCP 서버 간의 도구(Tool) 호출 규격을 정의합니다.
모든 MCP 도구는 이 문서에 명시된 Input/Output 스펙을 엄격히 준수해야 합니다.

## 1. `search_django_knowledge`

에이전트가 Django 공식 가이드와 코드를 검색하기 위해 호출하는 RAG 기반 하이브리드 검색(Vector + BM25) 도구입니다.

### Input (요청 파라미터)
- `query` (필수, string): 검색하고자 하는 자연어 질문이나 키워드.
- `django_version` (필수, string): 대상 Django 버전 (예: "5.0", "4.2").
- `document_type` (선택, string): 특정 문서 타입으로 필터링 (예: "topics", "ref", "howto").
- `max_results` (선택, integer): 반환할 최대 청크 수 (기본값: 5, 최대 10). 내부적으로 하이브리드 검색 후보군 10개를 Reranking한 후 상위 N개를 반환합니다.

### Output (반환 구조)
도구는 아래 필드를 포함하는 JSON 객체의 배열(리스트)을 반환해야 합니다.
- `content` (string): 문서 내용 (청크). 파이썬 코드 블록이 포함될 수 있음.
- `target_version` (string): 이 문서가 적용되는 Django 버전.
- `document_type` (string): 문서의 종류.
- `source_url` (string): 원본 문서의 URL.
- `relevance_score` (float): **Reranker 기반 관련성 점수 (0.0 ~ 1.0)**. 하이브리드 검색 결과에 문맥적 정밀도가 반영된 값입니다.
- `extra_meta` (object): 추가적인 메타데이터 (헤더 계층 정보 등).
