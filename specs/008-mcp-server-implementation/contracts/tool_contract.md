# 컨트랙트 (Contract): MCP 서버 구현 (mcp-server-implementation)

본 문서는 `mcp-server-implementation` 프로젝트에서 제공하는 `search_django_docs` 도구의 구체적인 구현 규격을 정의합니다. 이는 `specs/_architecture/mcp_tools_contract.md`를 기반으로 하되, 실제 구현 단계에서의 세부 사항을 반영합니다.

## 도구: `search_django_docs`

### 1. 인터페이스 정의 (FastMCP Python)
```python
@mcp.tool()
async def search_django_docs(
    query: str,
    django_version: str = "5.2",
    max_results: int = 5
) -> str:
    """
    Django 공식 문서를 하이브리드 검색(Vector + BM25) 및 리랭킹(MaxSim)을 통해 검색합니다.
    에이전틱 서치를 위해 다음 지침을 따르세요:
    1. 구체적이고 명확한 키워드를 사용하세요.
    2. 결과가 부족하면 새로운 키워드로 재검색하세요.
    3. 동일 검색어 반복을 금지합니다.
    4. 리랭크 점수가 낮으면 검색어를 최적화하세요.
    """
    ...
```

### 2. 입력 페이로드 (Input Payload)
| 필드 | 필수 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| `query` | Yes | - | 검색할 질문 또는 키워드 |
| `django_version` | No | "5.2" | 검색 대상 버전 |
| `max_results` | No | 5 | 반환할 최대 결과 수 (최대 10) |

### 3. 출력 형식 (Output Format)
LLM이 읽기 쉬운 텍스트(Markdown) 형식으로 반환하거나, 구조화된 JSON 문자열로 반환합니다. `fastmcp`는 기본적으로 문자열 반환을 권장하므로, 각 결과 청크를 구분하여 텍스트로 결합합니다.

**반환 텍스트 구조 예시:**
```markdown
[Result 1] (Score: 0.92)
Title: Models | Django documentation
URL: https://docs.djangoproject.com/en/5.2/topics/db/models/
Content:
Django models are the single, definitive source of information about your data...

---
[Result 2] (Score: 0.85)
...
```

### 4. 로깅 규격 (Logging Specification)
모든 도구 호출은 서버의 `stdout`에 다음 JSON 형식으로 기록되어야 합니다.
```json
{
  "event": "tool_call",
  "tool": "search_django_docs",
  "query": "...",
  "params": {"django_version": "5.2", "max_results": 5},
  "results_count": 5,
  "top_score": 0.92,
  "timestamp": "2026-03-25T..."
}
```
