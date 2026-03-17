# 작업 목록 (Tasks): 마크다운 코드 블록 보호 및 논리적 청킹 전략 개선

**기능**: `003-improve-markdown-chunking` | **날짜**: 2026-03-18
**참고**: 이 파일은 구현 상태를 추적하기 위한 체크리스트입니다. 각 작업은 독립적으로 실행 및 테스트 가능해야 합니다.

## 요약
- **총 작업 수**: 14개
- **사용자 스토리별 작업**: US1(3개), US2(3개), US3(2개)
- **병렬 가능 작업**: 4개 ([P] 표시)
- **MVP 범위**: 3단계 (US1: 논리 구조 보존 및 2단계 파이프라인 기본 구현)

## 구현 단계 (Phases)

### 1단계: 설정 및 환경 준비 (Setup)
- [ ] T001 `django_server` 내 `langchain-text-splitters` 패키지 설치 여부 최종 확인 및 환경 동기화
- [ ] T002 `django_server/src/documents/services/chunking.py` 파일의 기존 구현 내용을 참조용으로 백업 또는 Git 브랜치 상태 확인

### 2단계: 기초 테스트 및 유틸리티 (Foundational)
- [ ] T003 [P] `django_server/tests/test_chunking.py` 파일을 생성하고 기본 마크다운 분할 테스트 케이스 작성
- [ ] T004 [P] 코드 블록이 포함된 3000자 이상의 테스트용 마크다운 샘플 데이터를 `django_server/tests/samples/large_code_block.md`에 생성

### 3단계: [US1] 문서 논리 구조 및 문맥 보존 (P1)
- [ ] T005 [US1] `django_server/src/documents/services/chunking.py`의 `ChunkingService.__init__`에서 `MarkdownHeaderTextSplitter`와 `MarkdownTextSplitter` 초기화
- [ ] T006 [US1] `ChunkingService.split_markdown`에서 1단계(Header Split)와 2단계(Text Split)를 연결하는 파이프라인 구현 (메타데이터 자동 상속 활용)
- [ ] T007 [US1] `django_server/tests/test_chunking.py`에서 각 청크가 올바른 `Header 1~3` 메타데이터와 `header_context`를 포함하는지 검증

### 4단계: [US2] 코드 블록 무결성 보장 (P1)
- [ ] T008 [US2] MarkdownTextSplitter의 separators 설정을 조정하여 코드 블록 기호(\n```\n)를 최우선 구분자로 인식하게 함으로써 내부 절단을 방지
- [ ] T009 [US2] `django_server/src/documents/services/chunking.py`에서 분할된 결과물 중 코드 블록이 닫히지 않은 경우를 탐지하는 유효성 검사 로직(Sanity Check) 추가
- [ ] T010 [US2] django_server/tests/test_chunking.py에서 코드 블록 내부의 줄바꿈으로 인한 강제 분할이 발생하지 않는지, 그리고 분할 시 문법적 유효성을 유지하는지 검증

### 5단계: [US3] 임베딩 최적화 및 크기 조절 (P2)
- [ ] T011 [US3] `ChunkingService`의 기본 `chunk_size`를 2500자로 상향 조정하고 bge-m3 모델과의 호환성 확인
- [ ] T012 [US3] `django_server/tests/test_chunking.py`에서 모든 최종 청크의 길이가 `chunk_size` 상한을 넘지 않는지 확인

### 6단계: 다듬기 및 통합 검증 (Polish)
- [ ] T013 `django_server/src/documents/services/chunking.py`에서 기존의 강제 텍스트 주입(Context:, Document:) 로직을 완전히 제거하고 순수 텍스트만 반환하도록 정리
- [ ] T014 `django_server/tests/test_ingestion.py`를 실행하여 새로운 청킹 전략이 DB 적재(`ingest_docs` 명령)와 정상적으로 통합되는지 최종 확인

## 의존성 및 실행 순서
1. **기초 (T003-T004)**: 모든 구현 작업 전에 테스트 환경이 구축되어야 함.
2. **US1 (T005-T007)**: 2단계 파이프라인의 핵심 구조이므로 가장 먼저 완료해야 함 (MVP).
3. **US2 (T008-T010)**: US1 완료 후 코드 블록 보호 동작을 미세 조정함.
4. **통합 (T013-T014)**: 모든 사용자 스토리가 완료된 후 최종적으로 하위 호환성을 검증함.

## 구현 전략 (MVP First)
- **우선순위**: US1 > US2 > US3.
- **병렬 실행**: 테스트 케이스 작성(T003)과 샘플 데이터 생성(T004)은 독립적으로 진행 가능.
- **검증**: 각 단계 완료 후 `pytest`를 통해 독립적 테스트 기준을 통과해야 다음 단계로 진행.
