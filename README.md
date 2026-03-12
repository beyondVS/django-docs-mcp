# Django Docs MCP (Model Context Protocol)

AI 에이전트를 위한 RAG 기반 Django 공식 문서 검색 MCP 서버. FastMCP와 pgvector를 활용하여 환각(Hallucination) 없는 정확한 레퍼런스 및 코드 검색 환경을 제공합니다.

## 🎯 왜 이 프로젝트가 필요한가요? (Why)

AI 모델은 코드를 생성할 때 종종 과거 버전의 지식을 사용하거나 존재하지 않는 API를 만들어내는 환각(Hallucination) 현상을 겪습니다. 특히 프레임워크의 특정 버전에 의존적인 코드를 작성할 때 이 문제는 더욱 두드러집니다.

이 프로젝트는 최신 Django 공식 문서와 Cookbook을 벡터 데이터베이스에 임베딩하고, **Model Context Protocol (MCP)** 서버를 통해 AI 에이전트에게 제공합니다. 이를 통해 AI는 단순한 코드 완성을 넘어, 검증된 공식 문서를 기반으로 정확한 아키텍처를 설계하고 코드를 작성할 수 있습니다.

## 🏗 어떻게 작동하나요? (How)

시스템의 무결성과 확장성을 위해 **데이터 적재(Ingestion)** 파트와 **데이터 제공(Serving)** 파트를 분리하여 설계했습니다.

1. **지식 베이스 구축 (Django Server):** 크롤링된 문서 파일들을 청킹(Chunking)하여 임베딩한 뒤, 벡터 데이터베이스(PostgreSQL + pgvector)에 적재합니다. 관리자는 내장된 웹 UI(Playground)를 통해 검색 품질을 시각적으로 테스트하고 튜닝할 수 있습니다.
2. **AI 에이전트 연동 (MCP Server):** AI 에이전트는 FastMCP 기반 서버에 질의를 보냅니다. 서버는 HNSW 인덱스를 활용해 고속으로 관련 문서 청크를 검색하고 응답하여, AI가 문맥을 잃지 않도록 돕습니다.

## 🛠 기술 스택 (What)

* **Vector Database:** PostgreSQL + `pgvector` (HNSW 인덱스 활용)
* **Serving Layer:** Python `FastMCP` (비동기 지원 및 경량화 MCP 서버)
* **Ingestion & Testing:** Django (안정적인 Admin 제공 및 Playground 검색 튜닝 UI)
* **Embedding Model:** `BAAI/bge-m3` (Hugging Face 오픈소스, 1024차원)
* **Infrastructure:** Docker & Docker Compose (격리된 로컬 환경 및 배포 용이성)

## 📂 프로젝트 구조

```text
.
├── crawler/            # 외부 웹/문서 크롤링 및 로컬 볼륨 마운트용 스크립트
├── data_sources/       # 크롤링된 로컬 마크다운/문서 원본 저장소 (버전 관리 제외)
├── django_server/      # [Ingestion] 문서 파싱, 청킹, 임베딩 및 검색 품질 테스트 (Playground)
├── mcp_server/         # [Serving] AI 에이전트 질의 응답용 FastMCP 서버
├── specs/              # 시스템 아키텍처 및 데이터베이스 상세 설계 문서
├── .gemini/            # Gemini CLI 전용 워크플로우 및 스킬 설정
└── .specify/           # 프로젝트 표준 및 메모리 관리 (Global Constitution)
```

## 📝 상세 설계 문서

시스템의 세부 구현 방향과 규약은 다음 문서를 참고하세요.

* [프로젝트 기획서](./specs/_architecture/project_proposal.md)
* [시스템 아키텍처 설계서](./specs/_architecture/architecture_design.md)
* [데이터베이스 스키마 설계](./specs/_architecture/database_schema.md)
* [임베딩 및 청킹 전략](./specs/_architecture/embedding_strategy.md)
* [MCP 도구(Tools) 명세](./specs/_architecture/mcp_tools_contract.md)

## 🚦 시작하기 (진행 중)

현재 아키텍처 설계 및 인프라 구축 단계에 있습니다. 추후 아래와 같은 흐름으로 실행될 예정입니다.

```bash
# 1. 인프라 실행 (PostgreSQL + pgvector)
docker-compose up -d

# 2. 문서 수집 (로컬 data_sources에 마운트)
python crawler/main.py

# 3. 데이터 적재 및 임베딩 (Django Command)
python django_server/manage.py ingest_docs

# 4. MCP 서버 실행 (AI 에이전트 연결용)
mcp dev mcp_server/main.py
```
