# 서비스 연동 아키텍처 (Serving Architecture)

> 💡 **아키텍처 목적**
> 본 문서는 Django 기반의 검색 엔진(Search Engine)과
> AI 에이전트 간의 통신을 담당하는 MCP 서버(Serving Layer) 간의
> 효율적이고 안전한 연동 방식을 정의합니다.

---

## 1. 시스템 분리 개요 (Overview)

시스템의 역할과 책임을 명확히 하기 위해
**데이터 관리/검색 로직(Django)**과 **클라이언트 인터페이스(FastMCP)**를 논리적으로 분리하여 운영합니다.

| 서버 역할 | 담당 기술 | 주요 기능 및 책임 |
| :--- | :--- | :--- |
| **Search Engine** | Django 5.2 | 데이터 적재(Ingestion), 임베딩 벡터 생성, 하이브리드 검색 쿼리, 리랭킹 로직 등 **백엔드 코어 연산**을 전담합니다. |
| **Serving Layer** | FastMCP | AI 에이전트(Claude, Cursor 등)가 사용할 수 있는 **표준화된 MCP 도구(Tools)**를 **SSE(Server-Sent Events)** 방식으로 노출합니다. |

---

## 2. 연동 방식: 내부 모듈 호출 (Internal Module Strategy)

시스템의 지연 시간(Latency)을 최소화하고 인프라 구성을 단순화하기 위해 **내부 모듈 호출 방식**을 채택했습니다.

*   **구조:** MCP 서버(`mcp_server/main.py`)가 구동될 때 Django 프로젝트의 환경 설정을 메모리에 로드하여, Django 내부의 `SearchService` 클래스 메서드를 직접 호출합니다.
*   **실행 환경:** `mcp_server` 디렉토리 내에서 `uv run main.py` 명령어로 실행하며, Django 소스 경로(`django_server/src`)를 `sys.path`에 동적으로 추가하여 참조합니다.
*   **아키텍처 이점:** 서비스 간 네트워크 통신 오버헤드(HTTP 직렬화/역직렬화, 네트워크 왕복 시간)를 제거하여 검색 속도를 극대화합니다.

### 2.1 Django 환경 초기화 로직
```python
# mcp_server/main.py 핵심 구조
import os
import sys
import django

# 1. Django 소스 경로 추가 및 환경 변수 설정
sys.path.append(str(DJANGO_SRC_PATH))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# 2. Django 앱 레지스트리 초기화
django.setup()

# 3. 검색 서비스 직접 호출 (Async)
from documents.services.search import get_search_service
```

---

## 3. 전송 프로토콜: SSE (Server-Sent Events)

본 프로젝트의 MCP 서버는 표준 `stdio` 방식 대신 **SSE(Server-Sent Events)** 방식을 기본 전송 프로토콜로 사용합니다.

*   **기본 포트:** `8080`
*   **엔드포인트:** `http://127.0.0.1:8080/sse`
*   **이점:** 로컬 환경뿐만 아니라 네트워크를 통한 원격 클라이언트(예: 별도 서버에서 구동 중인 LLM 에이전트 클라이언트)와의 연결이 용이하며, 실시간 스트리밍 응답 구조를 지원합니다.

---

## 4. 데이터 파이프라인 흐름 (Data Flow)

AI 에이전트의 검색 요청부터 최종 응답까지의 전체 흐름은 다음과 같습니다.

1.  **에이전트 요청:** 외부 AI 에이전트가 `search_django_knowledge` 도구를 호출하며 쿼리 및 파라미터(버전, 카테고리 등)를 전달합니다.
2.  **MCP 수신 및 검증:** FastMCP 서버가 질의를 수신하고 `Literal` 타입을 통해 파라미터 유효성을 검사합니다.
3.  **Django 검색 실행:** MCP 서버가 Django의 `SearchService`를 직접 호출하여 다음 과정을 거칩니다.
    *   **질문 인코딩 (Single Call):** `int8` ONNX 모델로 질문을 한 번만 인코딩하여 Dense 및 Multi-vector를 동시에 생성합니다.
    *   **1차 하이브리드 리트리벌:** `django-paradedb`를 통해 벡터와 키워드가 통합된 후보군을 추출합니다.
    *   **2차 Late Interaction 리랭킹:** 저장된 멀티 벡터를 DB에서 로드하여 **MaxSim 연산**을 수행, 정밀 순위를 도출합니다.
4.  **최종 응답 반환:** 가공이 완료된 검색 결과(본문, 버전, 소스 URL, 리랭크 점수 등)를 MCP 규격에 맞춰 에이전트에게 전달합니다.

---

## 5. 서버 성능 및 품질 전략

*   **에이전틱 서치 가이드 (Agentic Search Guide):** 도구 설명(Description)에 LLM을 위한 단계적 탐색 지침을 포함하여, 에이전트가 결과가 부족할 경우 스스로 검색 전략을 최적화하도록 유도합니다.
*   **상세 로깅 시스템 (Observability):** 모든 도구 호출 시 입력된 검색어, 결과 문서 제목, 리랭크 점수 등을 실시간으로 로깅하여 개발자가 에이전트의 사고 과정을 추적할 수 있게 합니다.
*   **중복 검색 방지:** 세션 내 최근 검색어를 추적하여 동일 키워드가 반복될 경우 경고 로그를 남기고 에이전트의 효율적인 탐색을 유도합니다.

---

## 6. 보안 및 권한 제어 (Security)

*   **비인증 구조 (No-Auth):** 로컬 및 신뢰된 환경에서의 사용을 전제로 하여 인증 레이어를 제외, 연동 복잡도를 최소화했습니다.
*   **읽기 전용 지침:** 도구 메타데이터에 `readOnlyHint` 및 `idempotentHint`를 명시하여 에이전트가 안전하게 조회를 수행할 수 있도록 돕습니다.
