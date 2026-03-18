# 서비스 연동 아키텍처 (Serving Architecture)

본 문서는 Django 기반의 검색 엔진(Search Engine)과 AI 에이전트 간의 통신을 담당하는 MCP 서버(Serving Layer) 간의 연동 방식을 정의합니다.

## 1. 개요 (Overview)

시스템은 **데이터 관리/검색 로직(Django)**과 **클라이언트 인터페이스(FastMCP)**를 분리하여 운영합니다.

*   **Django Server**: 데이터 적재(Ingestion), 임베딩 생성, 하이브리드 검색, 리랭킹 로직을 포함하는 백엔드 코어입니다.
*   **MCP Server (FastMCP)**: AI 에이전트(Claude, Gemini 등)가 사용할 수 있는 표준화된 MCP 도구(Tools)와 리소스(Resources)를 노출합니다.

## 2. 연동 방식: 내부 호출 (Internal Import Strategy)

초기 단계(MVP)에서는 지연 시간(Latency) 최소화와 인프라 구성을 단순화하기 위해 **내부 호출 방식**을 채택합니다.

*   **구조**: MCP 서버가 Django 프로젝트의 설정을 로드하여 Django 내부의 `SearchService`를 직접 호출합니다.
*   **이점**: REST API 호출 시 발생하는 오버헤드(HTTP 직렬화, 네트워크 왕복)를 방지할 수 있습니다.
*   **구현**:
    ```python
    # mcp_server/src/server.py (예시)
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    from documents.services.search import get_search_service
    search_service = get_search_service()
    ```

## 3. 데이터 흐름 (Data Flow)

1.  **에이전트 요청**: AI 에이전트가 `search_django_knowledge` 도구를 호출합니다.
2.  **MCP 수신**: FastMCP 서버가 질의를 수신하고 유효성을 검사합니다.
3.  **Django 검색 실행**: MCP 서버가 Django의 `HybridSearchService`를 호출하여 다음 과정을 거칩니다.
    *   `pgvector` + `pg_search`를 통한 1차 검색
    *   RRF 기반 점수 통합
    *   `RerankingService`를 통한 최종 순위 정렬
4.  **응답 반환**: 가공된 검색 결과(청크 본문 및 메타데이터)를 MCP 프로토콜 형식에 맞춰 에이전트에게 전달합니다.

## 4. 성능 최적화 전략 (Performance Optimization)

*   **모델 선로딩 (Warm-up)**: 서버 시작 시 임베딩 모델(bge-m3)과 리랭커 모델(keisuke-miyako/bge-reranker-base-onnx-int8)을 메모리에 미리 로드하여 첫 번째 질의의 지연 시간을 방지합니다.
*   **비동기 처리**: Django의 `sync_to_async`를 활용하여 CPU 집약적인 리랭킹 연산이 MCP 서버의 비동기 이벤트 루프를 방해하지 않도록 처리합니다.
*   **캐싱 (Caching)**: 반복되는 동일 질의에 대해서는 검색 결과를 캐싱하여 DB 부하를 줄입니다.

## 5. 보안 및 권한 (Security)

*   **입력 필터링**: 사용자 입력 질의에서 유해한 SQL이나 비정상적인 길이를 사전에 차단합니다.
*   **격리**: Django 어드민 계정과 검색 전용 DB 계정을 분리하여 보안 사고 시 영향을 최소화합니다.

## 6. 향후 확장성 (Future Scalability)

프로젝트 규모가 확장될 경우, MCP 서버와 Django 검색 엔진을 독립된 서비스로 분리하고 **gRPC** 또는 **REST API**를 통해 통신하는 마이크로서비스 아키텍처로 전환할 수 있습니다.
