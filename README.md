# Django Docs MCP (Model Context Protocol)

AI 에이전트를 위한 RAG 기반 Django 공식 문서 검색 MCP 서버. FastMCP와 pgvector를 활용하여 환각(Hallucination) 없는 정확한 레퍼런스 및 코드 검색 환경을 제공합니다.

## 🎯 왜 이 프로젝트가 필요한가요? (Why)

AI 모델은 코드를 생성할 때 종종 과거 버전의 지식을 사용하거나 존재하지 않는 API를 만들어내는 환각(Hallucination) 현상을 겪습니다. 특히 프레임워크의 특정 버전에 의존적인 코드를 작성할 때 이 문제는 더욱 두드러집니다.

이 프로젝트는 최신 Django 공식 문서와 Cookbook을 벡터 데이터베이스에 임베딩하고, **Model Context Protocol (MCP)** 서버를 통해 AI 에이전트에게 제공합니다. 이를 통해 AI는 단순한 코드 완성을 넘어, 검증된 공식 문서를 기반으로 정확한 아키텍처를 설계하고 코드를 작성할 수 있습니다.

## 🏗 어떻게 작동하나요? (How)

시스템의 무결성과 확장성을 위해 **데이터 적재(Ingestion)** 파트와 **데이터 제공(Serving)** 파트를 분리하여 설계했습니다.

1. **지식 베이스 구축 (Django Server):** 크롤링된 마크다운 문서를 **2단계 논리적 청킹(Semantic Chunking)** 전략을 통해 헤더 구조와 코드 블록 무결성을 보존하며 임베딩합니다. 벡터 데이터베이스(PostgreSQL + pgvector)에 적재된 데이터는 관리자 웹 UI(Playground)를 통해 검색 품질을 시각적으로 테스트하고 튜닝할 수 있습니다.
2. **AI 에이전트 연동 (MCP Server):** AI 에이전트는 FastMCP 기반 서버에 질의를 보냅니다. 서버는 HNSW 인덱스를 활용해 고속으로 관련 문서 청크를 검색하고 응답하여, AI가 문맥을 잃지 않도록 돕습니다.

## ✨ 주요 특징 (Key Features)

* **하이브리드 검색 (BM25 + Vector)**: PostgreSQL의 `pg_search`를 활용한 키워드 검색(BM25)과 `pgvector` 기반의 벡터 검색을 RRF(Reciprocal Rank Fusion) 알고리즘으로 통합하여 검색 정확도를 극대화했습니다.
* **ONNX 기반 Reranking**: 하이브리드 검색 후보군(Top-10)을 대상으로 `bge-reranker-v2-m3` 모델을 ONNX Runtime에서 실행하여 질의와의 관련성을 정밀하게 재평가합니다.
* **의미론적 2단계 청킹**: `MarkdownHeaderTextSplitter`로 문서 구조(H1~H3)를 파싱하고, `MarkdownTextSplitter`로 코드 블록을 보호하며 재분할하는 정교한 파이프라인을 제공합니다.
* **코드 블록 무결성 보장**: `bge-m3` 모델의 넓은 컨텍스트(8,192 토큰)를 활용하여, 긴 파이썬 예제 코드도 잘림 없이 온전한 형태로 검색 결과에 제공합니다.
* **데이터 순수성 유지**: 청크 본문에 인위적인 컨텍스트 정보를 주입하지 않고 순수 마크다운만 유지함으로써 임베딩 품질을 높이고 데이터 원본성을 확보했습니다.

## 🛠 기술 스택 (What)

* **Vector Database:** PostgreSQL + `pg_search` + `pgvector` (ParadeDB 공식 이미지 활용)
* **Serving Layer:** Python `FastMCP` (비동기 지원 및 경량화 MCP 서버)
* **Ingestion & Testing:** Django (안정적인 Admin 제공 및 Playground 검색 튜닝 UI)
* **Models & Runtime:**
    * **Embedding:** `BAAI/bge-m3` (ONNX 기반 가속, 1024차원)
    * **Reranker:** `BAAI/bge-reranker-v2-m3` (ONNX INT8 양자화 모델)
    * **Runtime:** `ONNX Runtime` (CPU 환경 최적화 및 고속 추론)
* **Infrastructure:** Docker & Docker Compose (격리된 로컬 환경 및 배포 용이성)

## 📂 프로젝트 구조

```text
.
├── crawler/            # 외부 웹/문서 크롤링 및 로컬 볼륨 마운트용 스크립트
├── data_sources/       # 크롤링된 로컬 마크다운/문서 원본 저장소 (버전 관리 제외)
├── django_server/      # [Ingestion] 문서 파싱, 청킹, 임베딩, 하이브리드 검색 및 Rerank
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
* [임베딩 및 리트리벌 전략](./specs/_architecture/embedding_strategy.md)
* [MCP 도구(Tools) 명세](./specs/_architecture/mcp_tools_contract.md)

## 🛠️ 개발 환경 구축 (Development Setup)

이 프로젝트는 `uv` 워크스페이스를 사용합니다. 개발 시에는 루트 디렉토리에서 아래 명령어를 실행하여 모든 멤버 프로젝트의 의존성을 통합 설치하십시오.

```bash
# 모든 워크스페이스 멤버와 개발 도구를 한 번에 설치
uv sync --all-packages
```

## 🚦 시작하기 (Getting Started)

현재 지식 베이스 구축 및 하이브리드 검색 엔진 단계가 완료되어 로컬에서 문서 적재 및 고성능 검색 테스트가 가능합니다.

### 1. 인프라 실행 (ParadeDB: PostgreSQL + pg_search + pgvector)
```bash
docker-compose up -d db
```

### 2. Django Server 초기화 및 실행
```bash
cd django_server
uv sync
uv run python src/manage.py migrate
```

# 3. 데이터 적재 및 임베딩 (Django Command)
```bash
# data_sources/django2-orm-cookbook 폴더 내의 마크다운 파일을 적재 (ONNX 기반 임베딩 자동 수행)
uv run python src/manage.py ingest_docs ../data_sources/django2-orm-cookbook/ --doc-version 2.2 --category Cookbook
```

# 4. 검색 실험실(Playground) 및 평가
```bash
uv run python src/manage.py runserver
```
- **Playground 접속**: `http://127.0.0.1:8000/playground/` (하이브리드 검색 및 Rerank 점수 확인 가능)
- **품질 평가 실행**: `uv run python scripts/evaluate_search.py` (MRR, Hit Rate 지표 분석)

## 📅 로드맵 및 진행 현황

- [x] **Phase 1: 인프라 및 기반 설계** (DB 스키마, 임베딩 모델 선정)
- [x] **Phase 2: Django Server (Ingestion & Search Engine)**
    - [x] pgvector 기반 텍스트 청킹 및 임베딩 파이프라인
    - [x] 하이브리드 검색 엔진 (BM25 + Vector + RRF) 구축
    - [x] ONNX Runtime 기반 Reranker 통합
    - [x] 검색 품질 평가 프레임워크 구축 (MRR 지표 검증)
    - [x] 검색 품질 테스트용 웹 UI (Playground)
- [ ] **Phase 3: MCP Server (Serving)**
    - [ ] FastMCP 기반 서버 골격 구축
    - [ ] 하이브리드 검색 도구(Tool) 및 문서 리소스(Resource) 구현
- [ ] **Phase 4: 문서 확장 및 고도화**
    - [ ] Django 공식 문서 전체 크롤링 및 적재
    - [ ] 다국어 질의 성능 최적화 (bge-m3 튜닝)


### 🚨 트러블슈팅 (Troubleshooting)
- **네트워크 타임아웃 & 429 Too Many Requests:** 크롤러는 `tenacity`를 활용해 자동으로 지수 백오프 기반 재시도를 수행합니다. 오류 발생 시 강제로 중단하지 말고 대기하세요.
- **인코딩 오류:** 크롤링된 결과물은 자동으로 `UTF-8`로 변환되어 저장됩니다. Windows 환경 등에서 파일 읽기/쓰기 시 인코딩 문제가 발생하면 Python 실행 환경이 `UTF-8`을 기본으로 사용하는지 확인하세요.
- **추출 실패 시 폴백:** 본문 추출 시 `readability-lxml`이 실패할 경우, 내부적으로 `BeautifulSoup`을 사용하여 주요 CSS 컨테이너(`.section`, `main` 등)를 탐색하도록 폴백(Fallback) 처리되어 있습니다. 빈 내용이 저장될 경우 `converter.py`의 폴백 셀렉터를 추가할 수 있습니다.
