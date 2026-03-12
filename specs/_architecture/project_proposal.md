# 프로젝트 기획서: Django Docs MCP

## 1. 프로젝트 개요

* **프로젝트 명:** Django Docs MCP
* **목적:** AI 에이전트가 환각(Hallucination) 없이 Django 공식 가이드와 코드를 정확하게 검색하고 활용할 수 있도록, RAG(Retrieval-Augmented Generation) 기반의 지식 통합 인터페이스를 제공한다.
* **핵심 요약:** Django 공식 문서 및 Cookbook을 파싱하여 임베딩한 뒤, Model Context Protocol(MCP) 서버를 통해 AI 에이전트에게 Agentic Search 기능을 제공하는 시스템.

## 2. 프로젝트 진행 절차

**단계 1: 요구사항 분석 및 스펙 정의 (Spec-Driven)**
* 파싱 대상 문서 범위 확정 (공식 문서 특정 버전, 튜토리얼 등)
* MCP Tool 입출력 명세(Specification) 작성
* 전체 데이터 흐름 및 아키텍처 설계

**단계 2: 데이터 파이프라인 및 데이터베이스 구축**
* 대상 웹페이지 크롤링 및 마크다운 변환 스크립트 개발
* 의미론적 검색 품질을 높이기 위한 청킹(Chunking) 전략 수립 및 실행
* 데이터베이스 스키마 설계 및 임베딩 벡터 적재

**단계 3: MCP 서버 개발**
* MCP 프로토콜 규격에 맞는 서버 애플리케이션 구현
* 사용자 질의(Query)에 대해 가장 관련성 높은 문서 청크를 반환하는 Retriever 로직 개발
* 필요시 인증(Authentication) 및 에러 핸들링 로직 추가

**단계 4: AI 에이전트 연동 및 검증**
* 로컬/클라우드 AI 에이전트(예: Claude Desktop 등)와 완성된 MCP 서버 연동
* 프롬프트 엔지니어링을 통한 검색 결과 활용도 테스트 (예: @Architect 페르소나 적용 등)
* 검색 품질 평가 및 시스템 튜닝 (회고)

## 3. 핵심 산출물 목록 및 참조 위치

* **기획/요구사항:** `specs/_architecture/project_proposal.md` (본 문서)
* **시스템 아키텍처 및 데이터 흐름:** `specs/_architecture/architecture_design.md`
* **청킹 및 임베딩 전략:** `specs/_architecture/embedding_strategy.md`
* **데이터베이스 스키마:** `specs/_architecture/database_schema.md`
* **MCP Tool 규약:** `specs/_architecture/mcp_tools_contract.md`
