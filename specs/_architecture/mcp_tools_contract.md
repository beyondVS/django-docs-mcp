# MCP Tools Contract (도구 규약)

> 💡 **도구 호출 규약**
> 이 문서는 AI 에이전트와 MCP 서버 간의 도구(Tool) 호출 규격을 엄격히 정의합니다.
> 모든 MCP 도구는 이 문서에 명시된 Input/Output 스펙을 반드시 준수해야 합니다.

---

## 1. `search_django_knowledge`

AI 에이전트가 Django 공식 가이드와 코드를 검색하기 위해 호출하는 **RAG 기반 하이브리드 검색(Vector + BM25 + Rerank)** 도구입니다.

### 1.1 도구 설명 및 에이전틱 서치 지침 (Description)

이 도구는 단순한 키워드 검색을 넘어, AI 에이전트가 스스로 지식을 탐색하고 검증할 수 있도록 설계되었습니다. 에이전트는 다음 지침을 따라야 합니다.

1.  **키워드 최적화**: 사용자의 질문에서 핵심 기술 용어(클래스명, 메서드명 등)를 추출하여 구체적이고 명확한 쿼리를 설계하세요.
2.  **단계적 탐색**: 첫 번째 검색 결과가 부족하거나 모호할 경우, 결과 내의 새로운 개념이나 키워드를 바탕으로 재검색을 수행하세요.
3.  **중복 검색 금지**: 🚫 동일한 검색 세션 내에서 동일한 키워드로 반복 검색하지 마세요. (이미 시도한 쿼리는 전략을 수정하여 다른 키워드로 변경해야 함)
4.  **품질 검증**: 반환된 `relevance_score`가 낮다면 검색어가 너무 모호할 수 있습니다. 더 구체적인 기술적 키워드를 시도하세요.

### 1.2 Input (요청 파라미터)

| 파라미터명 | 타입 | 필수 여부 | 설명 및 예시 |
| :--- | :--- | :--- | :--- |
| `query` | string | **필수** | 검색하고자 하는 자연어 질문이나 구체적인 키워드. |
| `django_version` | `Literal["2.x", "4.2", "5.2"]` | 선택 | 검색 대상 Django 버전 필터링. |
| `document_type` | `Literal["Documentation", "Cookbook"]` | 선택 | 문서 카테고리 필터링. |
| `max_results` | integer | 선택 | 반환할 최대 결과 수 (기본값: 5, 최대 10). |

### 1.3 Output (반환 구조)

| 반환 필드명 | 타입 | 설명 및 특징 |
| :--- | :--- | :--- |
| `content` | string | 실제 문서의 내용(청크). 파이썬 코드 블록이 포함될 수 있음. |
| `target_version` | string | 해당 문서 청크의 Django 버전 정보. |
| `document_type` | string | 문서 카테고리 ("Documentation" 또는 "Cookbook"). |
| `source_url` | string | 공식 문서 웹 URL (출처 명시용). |
| `relevance_score` | float | **Late Interaction (MaxSim) 기반 관련성 점수**. 0.8 이상은 높은 신뢰도를 의미함. |
| `extra_meta` | object | `document_title`, `section_title`, `id` 등 추가 컨텍스트 정보 포함. |

---

## 2. `test_django_connection`

Django 앱 레지스트리가 정상적으로 로드되었는지 확인하는 진단용 도구입니다.

### 2.1 Output (반환 구조)

| 타입 | 설명 |
| :--- | :--- |
| string | Django READY 상태 여부 및 로드된 앱(App) 목록 요약 메시지. |
