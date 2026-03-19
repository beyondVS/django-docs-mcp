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
| **Search Engine** | Django | 데이터 적재(Ingestion), 임베딩 벡터 생성, 하이브리드 검색 쿼리, 리랭킹 로직 등 **백엔드 코어 연산**을 전담합니다. |
| **Serving Layer** | FastMCP | AI 에이전트(Claude, Cursor 등)가 사용할 수 있는 **표준화된 MCP 도구(Tools)**와 리소스를 외부에 노출합니다. |

---

## 2. 연동 방식: 내부 호출 (Internal Import Strategy)

초기 MVP 단계에서는 시스템의 지연 시간(Latency)을 최소화하고
인프라 구성을 단순화하기 위해 **내부 호출 방식**을 채택합니다.

*   **구조:** MCP 서버(FastMCP)가 구동될 때 Django 프로젝트의 환경 설정을 메모리에 로드하여,
    Django 내부의 `SearchService` 클래스 메서드를 직접 호출합니다.
*   **아키텍처 이점:** 두 서비스 간에 REST API 등을 통신할 때 발생하는
    불필요한 오버헤드(HTTP 직렬화/역직렬화, 네트워크 왕복 시간)를 원천적으로 방지합니다.

### 2.1 내부 호출 구현 예시
```python
# mcp_server/src/server.py (예시)
import os
import django

# 1. Django 환경 설정 강제 로드
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# 2. Django 애플리케이션 내부 서비스 직접 호출
from documents.services.search import get_search_service
search_service = get_search_service()
```

---

## 3. 데이터 파이프라인 흐름 (Data Flow)

AI 에이전트의 검색 요청부터 최종 응답까지의 전체 흐름은 다음과 같습니다.

1.  **에이전트 요청:** 외부 AI 에이전트가 노출된 `search_django_knowledge` MCP 도구를 호출하며 검색어(Query)를 전달합니다.
2.  **MCP 수신 및 검증:** FastMCP 서버가 질의를 수신하고 파라미터의 유효성을 검사합니다.
3.  **Django 검색 실행:** MCP 서버가 Django의 `SearchService`를 직접 호출하여 다음 과정을 거칩니다.
    *   **질문 인코딩 (Single Call):** `int8` ONNX 모델로 질문을 한 번만 인코딩하여 Dense 및 Multi-vector를 동시에 생성합니다.
    *   **1차 하이브리드 리트리벌:** `django-paradedb`를 통해 벡터와 키워드가 통합된 후보군(Top-20)을 추출합니다.
    *   **2차 Late Interaction 리랭킹:** 저장된 멀티 벡터를 DB에서 로드하여 **MaxSim 연산**을 수행, 정밀 순위를 도출합니다.
4.  **최종 응답 반환:** 가공이 완료된 검색 결과(문서 청크 본문, 점수, 메타데이터)를 MCP 프로토콜 표준 JSON 형식에 맞춰 에이전트에게 전달합니다.

---

## 4. 서버 성능 최적화 전략 (Performance Optimization)

*   **단일 모델 통합 서빙 (Single-Model Strategy):** 임베딩과 리랭킹을 위해 각각 모델을 올리는 대신, **`gpahal/bge-m3-onnx-int8` 모델 하나만 메모리에 로드**하여 리소스 점유율을 최적화하고 질문 인코딩 속도를 극대화합니다.
*   **Late Interaction 가속:** 무거운 Transformer 추론 대신 **NumPy 기반의 고속 행렬 연산(MaxSim)**을 수행하여 리랭킹 지연 시간을 획기적으로 낮춥니다.
*   **비동기 처리 (Async Safety):** Django의 `sync_to_async` 데코레이터를 사용하여 CPU 연산이 메인 이벤트 루프를 차단하지 않도록 보호합니다.

---

## 5. 보안 및 권한 제어 (Security)

*   **입력 필터링:** 사용자 입력 질의(Query)에서 유해한 SQL 인젝션 패턴이나
    비정상적으로 긴 텍스트 길이를 사전에 차단합니다.
*   **권한 격리:** 수집 및 관리를 위한 Django 어드민(Admin) 데이터베이스 계정과
    단순 읽기 위주의 검색 전용 DB 계정 권한을 분리하여, 보안 사고 발생 시 데이터 훼손 영향을 최소화합니다.

---

## 6. 향후 확장성 계획 (Future Scalability)

프로젝트 규모가 커지고 트래픽이 폭증할 경우,
단일 컨테이너 내부 호출 방식에서 벗어나 MCP 서버와 Django 검색 엔진을
물리적으로 완전 독립된 마이크로서비스(Microservice)로 분리할 계획입니다.
이때 서비스 간 통신은 고성능 **gRPC** 또는 **REST API** 아키텍처로 전환됩니다.
