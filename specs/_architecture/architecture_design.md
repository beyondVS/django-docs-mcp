# 시스템 아키텍처 설계서 (Architecture Design)

본 시스템은 데이터 적재(Ingestion) 파트와 데이터 제공(Serving) 파트를 분리하여 인프라의 확장성과 무결성을 보장합니다.

## 1. 기술 스택 (Tech Stack)

* **Vector Database:** PostgreSQL + pgvector (차후 pg_vectorscale 검토)
* **Serving (MCP Server):** Python FastMCP (경량화 및 비동기 지원)
* **Ingestion & Testing (Web UI):** Django (내장 Auth/Admin 활용 및 **검색 테스트용 Playground 포함**)
* **Embedding Model:** BAAI/bge-m3 (Hugging Face 오픈소스, 1024 차원)
* **Infra:** Docker & Docker Compose (로컬 개발 환경 및 컨테이너 오케스트레이션)

## 2. 아키텍처 구성 및 데이터 흐름

### Phase 1 (MVP - 분리형 수동 파이프라인)
* **크롤러 스크립트:** 외부 웹/문서 다운로드 후 컨테이너 내 볼륨(로컬 파일)으로 저장.
* **Django Command:** `python manage.py ingest_docs` 등을 실행하여 로컬 파일을 읽고 마크다운 파싱/청킹 -> bge-m3 임베딩 -> PostgreSQL(pgvector)에 INSERT.
* **Playground (Django View):** 데이터 적재 후, 에이전트 없이 웹 브라우저에서 직접 질의(Query)를 입력하여 검색된 청크와 유사도 점수를 눈으로 확인하며 품질을 튜닝.

### Phase 2 (확장 - 보안 기반 웹 서비스)
* 관리자 Django Auth 세션 로그인 및 권한 검증.
* Django Admin을 통한 문서 다이렉트 업로드. 백그라운드 워커를 통한 비동기 파싱 및 안전한 DB 적재.
* **Data Serving (공통):** 에이전트 질의 -> FastMCP 서버 수신 -> DB 내 HNSW 인덱스 기반 고속 벡터 검색 -> 결과 JSON 반환.

## 3. 시스템 구성도

```mermaid
graph LR
    %% 스타일 정의
    classDef client fill:#f9f9f9,stroke:#666,stroke-width:2px,color:#333;
    classDef web fill:#e1f5fe,stroke:#039be5,stroke-width:2px,color:#000;
    classDef worker fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#000;
    classDef db fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,color:#000;
    classDef mcp fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#000;
    classDef file fill:#eeeeee,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5,color:#000;
    classDef docker fill:#f4fbfe,stroke:#2496ed,stroke-width:2px,stroke-dasharray: 5 5;

    %% 액터 정의
    Dev([개발자 / 관리자]):::client
    Agent([AI 에이전트]):::client

    subgraph Docker_Compose ["Docker Compose"]
        direction TB

        %% 데이터 적재 파트
        subgraph Ingestion_Layer [데이터 수집 및 적재 계층]
            direction TB
            Crawler[1. Crawler Script<br/>- httpx/readability 기반 수집]:::worker
            LocalFile[(2. 로컬 마크다운 파일<br/>data_sources/ 계층 구조)]:::file
            DjangoCmd[3. Django Command<br/>- YAML 메타데이터 파싱 및 적재]:::worker

            Crawler -- "URL 계층 저장" --> LocalFile
            LocalFile -- "Front Matter 파싱" --> DjangoCmd
        end

        %% 데이터베이스 파트
        subgraph Database_Layer [통합 데이터베이스 계층]
            PG[(PostgreSQL + pgvector<br/>- Source/Document/Chunk)]:::db
        end

        %% UI 파트
        subgraph Web_Layer [Django Web 서비스]
            direction TB
            DjangoWeb["Django Web Server<br/>- Admin (데이터 관리)<br/>- Playground (검색 테스트)"]:::web
        end

        %% 데이터 제공 파트
        subgraph Serving_Layer [MCP 인터페이스 계층]
            FastMCP[FastMCP Server<br/>- Agentic Search API]:::mcp
        end

        DjangoCmd -- "4. 데이터 INSERT" --> PG
        DjangoWeb -- "직접 DB 조회 (Playground)" <--> PG
        FastMCP -- "DB 유사도 검색" <--> PG
    end

    %% 외부 상호작용
    Dev -- "명령어 실행 (manage.py)" --> DjangoCmd
    Dev -- "테스트 쿼리 및 결과 확인" --> DjangoWeb
    Agent -- "검색 질의 (Tool Call)" --> FastMCP
```
