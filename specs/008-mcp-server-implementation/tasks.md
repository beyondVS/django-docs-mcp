# 작업 목록 (Tasks): MCP 서버 구현 (mcp-server-implementation)

본 문서는 `mcp-server-implementation` 기능 구현을 위한 상세 작업 목록을 정의합니다. `fastmcp==3.1.1`을 사용하여 Django 검색 기능을 서빙하는 MCP 서버를 구축합니다.

## 1단계: 설정 (Setup) - 프로젝트 초기화
- [ ] T001 `mcp_server/` 디렉터리 생성 및 기본 구조 설정
- [ ] T002 `mcp_server/pyproject.toml` 생성 및 의존성(`fastmcp~=3.1.1`, `django~=5.2`) 정의
- [ ] T003 `mcp_server/main.py` 생성 및 `FastMCP` 인스턴스 초기화 코드 작성
- [ ] T004 `uv sync --all-packages` 실행하여 새 프로젝트 의존성 설치

## 2단계: 기초 (Foundational) - Django 런타임 통합
- [ ] T005 `mcp_server/main.py`에 Django 환경 초기화 로직 구현 (sys.path 추가 및 django.setup)
- [ ] T006 `mcp_server/main.py`에서 `django.apps.apps.ready`를 확인하는 간단한 연결 테스트 도구 작성

## 3단계: 사용자 스토리 US1 - 에이전틱 문서 검색 (P1)
**목표**: LLM이 Django 문서를 검색하고 에이전틱하게 지식을 활용할 수 있도록 도구를 제공함.
**테스트**: `mcp-inspector`를 통해 `search_django_docs` 도구를 호출하고 결과가 반환되는지 확인.

- [ ] T007 [US1] `mcp_server/main.py`에 `search_django_docs` 도구 정의 및 파라미터(`query`, `django_version`, `max_results`) 설정
- [ ] T008 [US1] 도구 설명(description)에 `spec.md` 및 `contracts/tool_contract.md`에 정의된 에이전틱 서치 가이드 삽입
- [ ] T009 [US1] `django_server.src.documents.services.search` (또는 해당 검색 서비스)를 호출하여 하이브리드 검색 로직 연동
- [ ] T010 [US1] 검색 결과를 `contracts/tool_contract.md`에 정의된 마크다운 텍스트 형식으로 변환하여 반환하는 로직 구현

## 4단계: 사용자 스토리 US2 - 검색 로깅 및 품질 모니터링 (P2)
**목표**: 개발자가 LLM의 검색 키워드와 전략을 추적할 수 있도록 상세 로그를 남김.
**테스트**: 도구 호출 후 `stdout`에 약속된 JSON 포맷의 로그가 출력되는지 확인.

- [ ] T011 [P] [US2] `mcp_server/logger.py` 생성 및 구조화된 JSON 로깅 유틸리티 구현
- [ ] T012 [US2] `search_django_docs` 도구 내에 검색어, 검색 시간, 결과 수, 상위 점수를 기록하는 로그 코드 추가

## 5단계: 사용자 스토리 US3 - 효율적인 검색 제어 (P3)
**목표**: 동일 키워드 반복 검색을 방지하고 에이전트의 효율성을 높임.
**테스트**: 동일 키워드 반복 검색 시 로그에 경고가 찍히거나 도구 설명에 의해 LLM이 회피하는지 확인.

- [ ] T013 [US3] 도구 설명 내 '동일 키워드 반복 금지' 지침의 강조 및 구체화
- [ ] T014 [US3] (선택 사항) 세션 내 최근 검색 키워드를 메모리에 유지하여 중복 발생 시 로그에 `duplicate_warning` 기록

## 6단계: 다듬기 (Polish) 및 마무리
- [ ] T015 `mcp_server/README.md` 작성 및 `quickstart.md` 내용 반영
- [ ] T016 전체 코드에 대해 `uv run ruff check .` 실행 및 스타일 교정
- [ ] T017 `mcp_server` 프로젝트의 최종 작동 확인 및 문서 업데이트

---

## 의존성 그래프 (Dependency Graph)
- **Setup (T001-T004)** -> **Foundational (T005-T006)** -> **US1 (T007-T010)**
- **US1** -> **US2 (T011-T012)**
- **US1** -> **US3 (T013-T014)**

## 병렬 실행 기회 (Parallel Opportunities)
- [P] 표시된 작업들은 서로 독립적으로 진행 가능합니다.
- T011 (로깅 유틸)은 US1 구현과 병렬로 진행할 수 있습니다.

## 구현 전략: MVP 우선
1. **1단계(T001-T010)**를 완료하여 기본적인 검색이 가능한 상태를 만듭니다 (MVP).
2. 검색 품질 확인을 위해 **2단계(T011-T012)**의 로깅 기능을 추가합니다.
3. 최종적으로 에이전틱 서치 가이드를 고도화하여 효율성을 확보합니다.
