# 조사 결과 (Research): MCP 서버 구현 (mcp-server-implementation)

## 1. FastMCP 3.1.1 분석

### 결정(Decision)
- **프레임워크**: `fastmcp==3.1.1` (Python 3.13 호환 확인 완료)
- **도구 정의**: `FastMCP` 클래스의 `@mcp.tool()` 데코레이터를 사용하여 `async` 함수로 구현.
- **로깅**: `FastMCP`의 기본 로깅 출력을 활용하되, `search_django_docs` 함수 내에서 상세한 `print()` 또는 `logging`을 통해 LLM의 사고 과정을 명시적으로 stdout에 기록함 (MCP 프로토콜을 통해 클라이언트에 전달됨).

### 근거(Rationale)
- `fastmcp`는 MCP 프로토콜의 복잡성을 추상화하며, Pydantic을 활용한 파라미터 유효성 검사를 자동으로 수행함.
- `3.1.1` 버전은 안정적인 도구 정의와 서버 실행 기능을 제공함.

### 고려된 대안(Alternatives considered)
- `mcp-python-sdk`: 저수준 라이브러리로 더 많은 제어가 가능하나, 구현 생산성과 유지보수성 측면에서 `fastmcp`가 우수함.

---

## 2. Django 런타임 통합

### 결정(Decision)
- **초기화 방식**: `mcp_server` 프로젝트의 진입점(`main.py` 등) 상단에서 `sys.path` 조작 및 `django.setup()`을 호출함.
- **경로 설정**:
  ```python
  import sys
  import os
  import django

  sys.path.append(os.path.join(PROJECT_ROOT, "django_server", "src"))
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
  django.setup()
  ```

### 근거(Rationale)
- 요구사항 `FR-003`에 따라 `django_server` 소스를 직접 모듈로 임포트하여 하이브리드 검색 및 리랭크 로직(`documents.services`)을 호출해야 함.
- 별도의 API 통신 없이 직접 DB 및 모델에 접근하므로 지연 시간이 최소화됨.

### 고려된 대안(Alternatives considered)
- `django_server`를 별도 프로세스로 띄우고 HTTP/gRPC 통신: 요구사항 `FR-003`(직접 임포트)에 위배되며 불필요한 레이턴시 발생.

---

## 3. 에이전틱 서치 프롬프트 가이드

### 결정(Decision)
- **도구 설명(Description)**:
  "Django 공식 문서를 검색합니다. 에이전틱 서치를 위해 다음 지침을 따르세요:
  1. 구체적이고 명확한 키워드를 사용하세요.
  2. 첫 번째 검색 결과가 부족하다면, 결과에 포함된 새로운 키워드를 활용해 다른 각도에서 재검색하세요.
  3. 동일한 검색어를 반복해서 사용하지 마세요.
  4. 검색 결과의 리랭크 점수가 낮다면 신뢰하지 말고 검색어를 최적화하세요."

### 근거(Rationale)
- 요구사항 `FR-004` 및 `FR-005`를 충족하기 위해 도구 설명 내에 명시적인 행동 가이드를 포함함.
- LLM이 스스로 검색 전략을 수정하도록 유도하여 품질을 높임.

### 고려된 대안(Alternatives considered)
- 시스템 프롬프트(Instructions)에 포함: MCP 서버는 도구 중심이므로 도구 설명에 직접 포함하는 것이 에이전트가 도구 선택 시 더 강력한 힌트를 얻게 함.

---

## 4. 의존성 충돌 및 가상환경 관리

### 결정(Decision)
- **UV 워크스페이스**: 루트의 `.venv`를 공유하되, `mcp_server/pyproject.toml`에 독립적인 의존성(`fastmcp`, `django` 등)을 명시함.
- **UV Sync**: `uv sync --all-packages` 명령어를 통해 통합 관리.

### 근거(Rationale)
- 헌법 `IV. 3. uv 워크스페이스 의존성 관리`를 준수하여 통합된 가상환경에서 개발 효율성을 극대화함.
- `django_server`와 `mcp_server`가 동일한 `onnxruntime`, `django` 버전을 사용하도록 강제하여 런타임 충돌 방지.
