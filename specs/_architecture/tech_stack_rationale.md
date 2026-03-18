# 기술 스택 선정 근거서 (Technology Stack Rationale)

본 문서는 Django Docs MCP 프로젝트에서 채택한 주요 기술 및 라이브러리의 선정 근거와 기술적 전환 이력을 상세히 기술합니다. 모든 기술 선택은 프로젝트 헌법의 **'실용주의'**와 **'책임 분리'** 원칙을 바탕으로 결정되었습니다.

## 1. 인프라 및 데이터베이스 (Infrastructure & DB)

### 1.1 ParadeDB (PostgreSQL + pg_search + pgvector)
*   **기술 전환 1**: `pgvector/pgvector:pg16` 이미지 → **`paradedb/paradedb` 공식 이미지**
    *   **이유**: 초기에는 단순히 벡터 검색 기능을 확보하기 위해 전용 이미지를 사용했으나, 하이브리드 검색 구현을 위해 BM25 엔진이 사전 설치된 ParadeDB 이미지가 관리 효율성과 확장성 면에서 더 우수하다고 판단했습니다.
*   **기술 전환 2**: 단일 벡터 검색 → **하이브리드 검색 (`pg_search` 도입)**
    *   **이유**: 벡터 검색만으로는 Django API 명칭(`filter()`, `QuerySet` 등)에 대한 '키워드 정밀도'를 확보하는 데 한계가 있었습니다.
    *   **선정 근거**: `pg_search`는 BM25를 DB 내부에 Rust로 구현하여 정밀도가 높으며, SQL 기반 RRF 통합으로 어플리케이션 계층의 지연 시간을 최소화합니다.
*   **DB 드라이버 (psycopg3)**: Django 5.x의 비동기 기능을 최대로 활용하기 위해 `async/await`를 기본 지원하는 `psycopg 3.2.x`를 채택했습니다.

### 1.2 Docker & Docker Compose
*   **선정 근거**: '컨테이너 우선' 원칙에 따라 개발 환경과 운영 환경의 일치성을 보장합니다. 특히 ParadeDB와 같은 복잡한 DB 확장을 별도의 설치 과정 없이 즉시 실행할 수 있습니다.

## 2. 모델 런타임 및 최적화 (Model Runtime & Optimization)

### 2.1 ONNX Runtime (optimum)
*   **기술 전환**: `sentence-transformers` (PyTorch) → **`optimum` (ONNX)**
    *   **이유**: 임베딩과 리랭커 모델이 각각 메모리를 점유하고, CPU 환경에서 추론 속도가 저하되는 문제를 해결하기 위해 도입했습니다.
    *   **선정 근거**:
        *   **메모리 최적화**: 동일한 `onnxruntime` 라이브러리를 공유하여 상주 메모리를 절감합니다.
        *   **추론 가속**: **사전 양자화된 INT8 모델**을 선택하여 ONNX Runtime에서 구동함으로써, CPU 환경에서 FP32 대비 약 2~3배 빠른 추론 속도를 달성했습니다.
        *   **런타임 경량화**: PyTorch 전체 라이브러리 대신 추론 전용 런타임만을 사용하여 컨테이너 크기를 최적화했습니다.

## 3. 검색 및 리랭킹 모델 (Search & Reranking Models)

### 3.1 BAAI/bge-m3 (Embedding Model)
*   **선정 근거**: 8,192 토큰의 매우 넓은 컨텍스트 윈도우를 지원하여 긴 파이썬 예제 코드 블록을 절단 없이 임베딩할 수 있습니다. 또한 다국어 성능이 우수하여 한국어 기술 질문에 대해 높은 의미적 유사도를 보장합니다.

### 3.2 keisuke-miyako/bge-reranker-base-onnx-int8 (Reranker Model)
*   **선정 근거**: 110M 파라미터 수준의 Base 모델은 CPU 환경에서 v2-m3 모델 대비 압도적으로 빠른 추론 속도를 제공하면서도, 하이브리드 검색으로 추출된 Top-20 후보군 사이의 순위를 정밀하게 보정하는 데 최적의 성능을 보입니다.

## 4. 데이터 수집 및 백엔드 (Data Ingestion & Backend)

### 4.1 크롤링 및 파싱 (httpx, readability, markdownify)
*   **선정 근거**: `httpx`의 비동기 처리와 `tenacity`의 지수 백오프를 통해 수집 안정성을 확보했습니다. 또한 `readability`를 통한 본문 식별과 `markdownify` 커스터마이징을 통해 코드 펜스가 보존된 고품질 마크다운을 생성합니다.

### 4.2 Django & FastMCP
*   **기술 전환**: 단일 단계 청킹 → **2단계 청킹 파이프라인**
    *   **이유**: 청크의 섹션 문맥 단절 및 코드 블록 절단 문제를 해결하기 위해 도입했습니다.
    *   **선정 근거**: `MarkdownHeaderTextSplitter`와 `MarkdownTextSplitter`를 파이프라인으로 연결하여 메타데이터 상속과 코드 무결성을 동시에 확보했습니다.
*   **FastMCP**: 표준 MCP SDK보다 가볍고 현대적인 비동기 문법을 지원하며, Django 검색 로직을 에이전트 인터페이스로 빠르게 노출하는 데 최적입니다.

## 5. 의존성 및 개발 도구 (Dependency & Tooling)

### 5.1 uv (Workspace Manager)
*   **선정 근거**: Rust 기반의 압도적인 속도를 제공하며, 루트와 개별 프로젝트의 의존성을 하나의 `uv.lock`으로 통합 관리하면서도 런타임 환경을 격리할 수 있는 강력한 워크스페이스 기능을 제공합니다.

### 5.2 Ruff (Lint & Format)
*   **선정 근거**: `flake8`, `isort`, `black` 등을 모두 대체하는 올인원 도구로, 정적 분석 속도가 수십 배 빠르며 프로젝트 전체의 코드 일관성을 강제하는 데 최적입니다.
