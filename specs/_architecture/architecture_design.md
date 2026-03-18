# 시스템 아키텍처 설계서 (Architecture Design)

> 💡 **설계 핵심 목표**
> 본 시스템은 데이터 적재(Ingestion) 파트와 데이터 제공(Serving) 파트를
> 물리적/논리적으로 분리하여 인프라의 확장성과 무결성을 보장합니다.

---

## 1. 기술 스택 (Tech Stack)

시스템을 구성하는 주요 기술과 프레임워크는 다음과 같습니다.

| 분류 | 기술 및 스택 | 역할 및 특징 |
| :--- | :--- | :--- |
| **Database** | PostgreSQL (ParadeDB) | `pgvector`와 `pg_search`가 기본 포함된 강력한 벡터 검색 DB |
| **Serving** | Python FastMCP | AI 에이전트 연동을 위한 경량화 및 비동기 지원 MCP 서버 |
| **Ingestion & UI** | Django | 하이브리드 검색 및 Rerank 엔진, 수집 파이프라인 관리 |
| **Infra** | Docker & Docker Compose | ParadeDB 공식 이미지 활용 및 컨테이너 기반 독립 환경 구성 |

**AI 모델 및 런타임 (Models & Runtime)**
*   **Embedding:** `BAAI/bge-m3` (ONNX Runtime 가속, 1024 차원 벡터)
*   **Reranker:** `keisuke-miyako/bge-reranker-base-onnx-int8` (ONNX INT8 양자화)
*   **Runtime:** ONNX Runtime (순수 CPU 환경 최적화)

---

## 2. 아키텍처 구성 및 데이터 흐름

시스템 구축은 MVP부터 고도화 단계까지 3단계(Phase)로 나누어 진행됩니다.

### Phase 1: MVP (분리형 수동 파이프라인)
*   **크롤러 스크립트:** 외부 웹/문서를 다운로드한 후, 컨테이너 내부의 공유 볼륨(로컬 파일)에 저장합니다.
*   **Django Command:** `python manage.py ingest_docs` 등의 명령어를 실행하여 로컬 파일을 읽습니다.
    이후 마크다운 파싱 및 청킹을 수행하고, `bge-m3` ONNX 모델로 임베딩을 생성하여
    PostgreSQL(`pgvector`)에 INSERT 합니다.

### Phase 2: 검색 품질 고도화 (하이브리드 & Rerank)
*   **Hybrid Retrieval:** 에이전트 또는 사용자(Playground)의 질의가 발생하면,
    BM25 키워드 검색과 벡터 유사도 검색을 병렬로 수행합니다.
*   **RRF 통합:** 두 검색 결과의 점수 스케일 차이를 극복하기 위해,
    RRF(Reciprocal Rank Fusion) 알고리즘으로 순위를 결합하여 상위 후보군(Top 10~20)을 추출합니다.
*   **ONNX Reranking:** 추출된 1차 후보군을 대상으로 Reranker 모델을 실행하여,
    질문과의 문맥적 관련성을 정밀하게 재계산합니다.
*   **Playground:** 하이브리드 점수와 Rerank 점수를 시각적으로 비교 분석하고,
    MRR 등 품질 평가 지표를 산출하여 검색 로직을 튜닝합니다.

### Phase 3: 데이터 제공 (Serving - MCP 인터페이스)
*   **Data Serving:** AI 에이전트의 질의가 FastMCP 서버로 수신됩니다.
    FastMCP는 내부적으로 Django Search Service(하이브리드 + Rerank 파이프라인)를 호출하여,
    최종적으로 검증된 고품질 검색 결과를 에이전트에게 반환합니다.

---

## 3. 시스템 구성도

```mermaid
graph TD
    %% 스타일 정의
    classDef client fill:#f9f9f9,stroke:#666,stroke-width:2px,color:#333;
    classDef web fill:#e1f5fe,stroke:#039be5,stroke-width:2px,color:#000;
    classDef worker fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#000;
    classDef db fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,color:#000;
    classDef mcp fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#000;
    classDef file fill:#eeeeee,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5,color:#000;
    classDef docker fill:#f4fbfe,stroke:#2496ed,stroke-width:2px,stroke-dasharray: 5 5;
    classDef model fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000;

    %% 액터 정의
    Dev([개발자 / 관리자]):::client
    Agent([AI 에이전트]):::client

    subgraph Docker_Compose ["Docker Compose (ParadeDB Infrastructure)"]
        direction TB

        %% 데이터 적재 파트
        subgraph Ingestion_Layer [데이터 수집 및 적재 계층]
            direction TB
            Crawler[1. Crawler Script]:::worker
            LocalFile[(2. 로컬 마크다운 파일)]:::file
            DjangoCmd[3. Django Ingestion Command]:::worker

            Crawler -- "수집" --> LocalFile
            LocalFile -- "파싱/청킹" --> DjangoCmd
        end

        %% 모델 런타임
        subgraph Model_Runtime [ONNX Runtime]
            EmbedModel[bge-m3 Embedding]:::model
            RerankModel[bge-reranker Reranking]:::model
        end

        %% 데이터베이스 파트
        subgraph Database_Layer [통합 데이터베이스 계층]
            PG[(PostgreSQL + pgvector + pg_search)]:::db
        end

        %% UI 및 로직 파트
        subgraph Logic_Layer [Django Search Engine]
            direction TB
            SearchService["Hybrid Search Service<br/>(BM25 + Vector + RRF)"]:::web
            RerankService["Reranking Service<br/>(ONNX Refinement)"]:::web
            DjangoWeb["Admin & Playground UI"]:::web
        end

        %% 데이터 제공 파트
        subgraph Serving_Layer [MCP 인터페이스 계층]
            FastMCP[FastMCP Server]:::mcp
        end

        DjangoCmd -- "임베딩 생성" --> EmbedModel
        EmbedModel -- "Vector Insert" --> PG
        SearchService -- "Hybrid Query" --> PG
        SearchService -- "Top-N 후보 전달" --> RerankService
        RerankService -- "Score 산출" --> RerankModel
        FastMCP -- "검색 요청" --> SearchService
        DjangoWeb -- "모니터링/테스트" --> SearchService
    end

    %% 외부 상호작용
    Dev -- "데이터 관리" --> DjangoWeb
    Agent -- "검색 질의" --> FastMCP
```
