# 프로젝트 기획서: Django Docs MCP

> 💡 **프로젝트 비전**
> AI 에이전트가 환각(Hallucination) 없이 Django 공식 가이드와 코드를 정확하게 검색하고
> 프로젝트에 활용할 수 있도록 돕는 **RAG 기반 지식 통합 인터페이스**를 제공합니다.

---

## 1. 프로젝트 개요 (Overview)

| 항목 | 내용 |
| :--- | :--- |
| **프로젝트 명** | Django Docs MCP |
| **핵심 요약** | Django 공식 문서 및 Cookbook을 크롤링/파싱하여 데이터베이스에 임베딩한 뒤, Model Context Protocol(MCP) 서버를 통해 AI 에이전트에게 고품질의 Agentic Search 기능을 제공하는 시스템입니다. |
| **주요 기대 효과** | 개발 에이전트가 최신 Django 버전에 맞는 코드를 작성하도록 유도하며, 잘못된 API 사용이나 존재하지 않는 라이브러리를 참조하는 환각 현상을 원천 차단합니다. |

---

## 2. 프로젝트 진행 절차 (Phases)

프로젝트는 명확한 스펙 정의를 시작으로 인프라 구축, 서버 개발, 검증의 4단계로 진행됩니다.

### 단계 1: 요구사항 분석 및 스펙 정의 (Spec-Driven)
*   파싱 대상 문서의 범위를 확정합니다. (공식 문서의 특정 버전, 필수 튜토리얼, 쿡북 등)
*   AI 에이전트가 사용할 MCP Tool의 입출력 명세(Specification)를 작성합니다.
*   전체 데이터 흐름과 아키텍처, 데이터베이스 스키마를 선행 설계합니다.

### 단계 2: 데이터 파이프라인 및 데이터베이스 구축
*   대상 웹페이지를 수집하는 크롤링 스크립트와 마크다운 변환기를 개발합니다.
*   의미론적 검색 품질을 극대화하기 위해 헤더와 코드 블록을 고려한 청킹(Chunking) 전략을 수립하고 실행합니다.
*   설계된 데이터베이스 스키마에 맞게 테이블을 생성하고, 임베딩된 벡터 데이터를 적재(Ingestion)합니다.

### 단계 3: MCP 서버 개발
*   표준 MCP 프로토콜 규격에 부합하는 경량화된 서버 애플리케이션(FastMCP 등)을 구현합니다.
*   사용자 질의(Query)에 대해 하이브리드 검색 및 Reranking을 거쳐 가장 관련성 높은 문서 청크를 반환하는 Retriever 핵심 로직을 개발합니다.
*   필요에 따라 인증(Authentication) 및 예외 처리(Error Handling) 로직을 추가합니다.

### 단계 4: AI 에이전트 연동 및 검증
*   로컬 또는 클라우드 AI 에이전트(예: Claude Desktop, Cursor 등)와 완성된 MCP 서버를 연동합니다.
*   프롬프트 엔지니어링을 통해 검색 결과가 실제로 유용하게 적용되는지 테스트합니다. (예: `@Architect` 페르소나 적용 등)
*   평가 프레임워크를 기반으로 검색 품질을 측정하고 시스템 파라미터를 지속적으로 튜닝합니다.

---

## 3. 핵심 산출물 및 참조 위치

프로젝트의 진행과 결과물은 아래의 설계 문서들로 관리됩니다.

*   **기획/요구사항:** `specs/_architecture/project_proposal.md` (본 문서)
*   **시스템 아키텍처 및 데이터 흐름:** `specs/_architecture/architecture_design.md`
*   **청킹 및 임베딩 전략:** `specs/_architecture/embedding_strategy.md`
*   **데이터베이스 스키마:** `specs/_architecture/database_schema.md`
*   **MCP Tool 규약:** `specs/_architecture/mcp_tools_contract.md`
*   **검색 품질 평가 프레임워크:** `specs/_architecture/evaluation_framework.md`
