# MCP Tools Contract

> 💡 **도구 호출 규약**
> 이 문서는 AI 에이전트와 MCP 서버 간의 도구(Tool) 호출 규격을 엄격히 정의합니다.
> 모든 MCP 도구는 이 문서에 명시된 Input/Output 스펙을 반드시 준수해야 합니다.

---

## 1. `search_django_knowledge`

AI 에이전트가 Django 공식 가이드와 코드를 검색하기 위해 호출하는
**RAG 기반 하이브리드 검색(Vector + BM25 + Rerank)** 도구입니다.

### 1.1 Input (요청 파라미터)

에이전트가 도구를 호출할 때 전달해야 하는 인자입니다.

| 파라미터명 | 타입 | 필수 여부 | 설명 및 예시 |
| :--- | :--- | :--- | :--- |
| `query` | string | **필수** | 검색하고자 하는 자연어 질문이나 구체적인 키워드. |
| `django_version` | string | **필수** | 검색 대상이 되는 Django 프레임워크 버전 (예: "5.0", "4.2"). |
| `document_type` | string | 선택 | 특정 문서 타입으로 결과를 필터링할 때 사용 (예: "topics", "ref", "howto"). |
| `max_results` | integer | 선택 | 최종 반환할 최대 청크 수 (기본값: 5, 최대 10).<br>*(참고: 내부적으로 20~50개의 하이브리드 후보군을 뽑아 Reranking한 후 최종 상위 N개만 반환합니다.)* |

### 1.2 Output (반환 구조)

도구 실행이 완료되면 아래 필드를 포함하는 **JSON 객체의 배열(List)** 형태로 결과를 반환해야 합니다.

| 반환 필드명 | 타입 | 설명 및 특징 |
| :--- | :--- | :--- |
| `content` | string | 실제 문서의 내용(청크)입니다. 설명과 함께 파이썬 예제 코드 블록이 포함되어 있을 수 있습니다. |
| `target_version` | string | 이 문서 청크가 적용되는 Django 버전 정보입니다. |
| `document_type` | string | 문서의 종류 카테고리입니다. |
| `source_url` | string | 정보 출처인 원본 공식 문서의 웹 URL입니다. |
| `relevance_score` | float | **Reranker 기반 관련성 점수 (0.0 ~ 1.0)**.<br>단순 키워드 매칭이 아닌, 문맥적 정밀도가 반영된 최종 신뢰도 점수입니다. |
| `extra_meta` | object | 청크가 속한 헤더 계층 정보(H1, H2) 등 추가적인 컨텍스트 메타데이터를 포함합니다. |
