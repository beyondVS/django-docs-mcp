# 구현 계획서: 마크다운 코드 블록 보호 및 논리적 청킹 전략 개선

**브랜치**: `003-improve-markdown-chunking` | **날짜**: 2026-03-18 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/003-improve-markdown-chunking/spec.md`의 기능 명세서

## 요약
`langchain-text-splitters` 라이브러리의 `MarkdownHeaderTextSplitter`와 `MarkdownTextSplitter`를 직렬로 연결하여 문서의 논리적 구조(H1, H2, H3)와 코드 블록의 무결성을 동시에 보존하는 2단계 청킹 파이프라인을 구축합니다. 기존 `ChunkingService.split_markdown()`의 인터페이스를 유지하면서 본문 내 텍스트 주입을 제거하고 메타데이터로 모든 문맥 정보를 관리합니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.13 (Type 준수)
**주요 의존성**: `langchain-text-splitters~=1.1.1`
**저장소**: PostgreSQL + pgvector (기존 Chunk/Document 모델 유지)
**테스트**: `pytest` (새로운 `tests/test_chunking.py` 추가)
**대상 플랫폼**: Django Server (RAG 파이프라인)
**프로젝트 유형**: 내부 서비스 (Backend Service)
**성능 목표**: 청크 크기 문자 수 기준 1500~2500자 (bge-m3 임베딩 최적화)
**제약 사항**: 코드 블록(```) 분할 방지, 하위 호환 인터페이스 준수

## 헌법 준수 확인 (Constitution Check)

- [x] **RAG 정확성 확인**: 마크다운 분할이 H1/H2/H3 헤더 기반으로 설계되었는가? (파이썬 코드 블록 보존 포함)
- [x] **아키텍처 분리 확인**: 로직이 `django_server/src/documents/services/chunking.py`에 올바르게 할당되었는가?
- [x] **데이터 무결성 확인**: 데이터 모델이 Source > Document > Chunk의 3단계 계층을 준수하는가? (메타데이터 활용)
- [x] **컨테이너 환경 확인**: 실행 및 테스트 환경이 Docker/Docker Compose 기반으로 설계되었는가?

## 프로젝트 구조 (수정 대상)

```text
django_server/
├── src/
│   └── documents/
│       └── services/
│           └── chunking.py       # 핵심 리팩토링 대상
└── tests/
    └── test_chunking.py         # 신규 테스트 코드
```

## 실행 계획 (Execution Plan)

### 0단계: 리서치 및 검증 (완료)
- [x] `langchain-text-splitters`의 `MarkdownTextSplitter` 동작 방식 조사.
- [x] 기존 `ChunkingService` 인터페이스 분석 및 하위 호환 영향도 평가.
- [x] `research.md` 작성 및 기술 결정 확정.

### 1단계: 설계 및 컨트랙트 (완료)
- [x] `data-model.md` 및 `quickstart.md` 작성.
- [x] 메타데이터 키(`header_context`, `Header 1` 등) 정형화.

### 2단계: 구현 및 단위 테스트 (진행 예정)
1. **신규 테스트 코드 작성**: `django_server/tests/test_chunking.py`에서 코드 블록 보호 및 헤더 상속 시나리오 정의.
2. **`ChunkingService` 리팩토링**:
    - `__init__`: `MarkdownTextSplitter` 초기화 및 `chunk_size` 상향.
    - `split_markdown`: 2단계 파이프라인(`split_text` -> `split_documents`) 구현.
    - `content` 내 텍스트 주입 로직 제거.
    - 메타데이터 변환(`Document` -> `dict`) 래퍼 작성.
3. **통합 테스트**: `ingest_docs` 명령어를 통한 전체 데이터 흐름 검증.

## 복잡성 추적

(현재 보고된 복잡성 위반 사항 없음)
