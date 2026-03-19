# 구현 계획서: 고성능 하이브리드 검색 및 Late Interaction 리랭커 도입

**브랜치**: `005-optimize-search-rerank` | **날짜**: 2026-03-20 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/005-optimize-search-rerank/spec.md`의 기능 명세서

## 요약

현재 CPU 환경에서 1.5초가 소요되는 `bge-reranker-base`(Cross-Encoder) 기반 리랭킹 시스템을 `gpahal/bge-m3-onnx-int8` 모델 기반의 **Late Interaction(ColBERT-style)** 아키텍처로 전환하여 응답 속도를 **1초 이내(기대치 300ms 내외)**로 개선합니다. `django-paradedb`를 도입하여 기존 후보군(50개) 규모를 유지하면서 하이브리드 검색 코드를 ORM 스타일로 현대화하고, 128차원/int8 멀티 벡터 압축 저장 전략을 통해 성능과 저장 공간의 효율을 극대화합니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.13
**주요 의존성**: `django-paradedb~=0.4.0`, `onnxruntime`, `optimum`, `numpy`
**저장소**: PostgreSQL (ParadeDB: pg_search + pgvector), `bytea` 필드를 통한 멀티벡터 저장
**테스트**: `pytest`
**대상 플랫폼**: Docker / Linux
**프로젝트 유형**: Django 검색 서비스 확장
**성능 목표**: 전체 검색 응답(Retrieval + Rerank) < 1,000ms
**규모/범위**: 수만 개의 문서 청크 대상 고성능 리랭킹

## 헌법 준수 확인 (Constitution Check)

- [x] **RAG 정확성 확인**: 기존 512 토큰 청킹 전략을 유지하며, Late Interaction(MaxSim) 연산 시 [CLS] 등 특수 토큰을 포함하여 문맥 유지 설계 완료.
- [x] **아키텍처 분리 확인**: 하이브리드 검색 고도화는 `django_server` 모델 및 서비스 레이어에 응집력 있게 할당됨.
- [x] **데이터 무결성 확인**: `Chunk` 모델 확장을 통해 기존 3단계 계층 구조 내에서 멀티벡터 데이터 관리 체계 설계 완료.
- [x] **컨테이너 환경 확인**: ParadeDB(pg_search)가 포함된 기존 Docker Compose 환경을 그대로 활용함.

## 프로젝트 구조

### 문서 (이 기능 관련)

```text
specs/005-optimize-search-rerank/
├── plan.md              # 이 파일 (기술 설계 및 게이트 통과)
├── research.md          # 0단계: 모델 연산, 압축 전략, MaxSim 알고리즘 조사 결과
├── data-model.md        # 1단계: DocumentChunk 확장 및 바이너리 포맷 정의
├── quickstart.md        # 1단계: 설정 및 테스트 가이드
└── tasks.md             # 2단계: 구현 태스크 목록 (/speckit.tasks 명령 생성 예정)
```

### 소스 코드 (저장소 루트)

```text
django_server/
├── src/
│   └── documents/
│       ├── models.py           # DocumentChunk에 bytea 필드 추가
│       ├── services/
│       │   ├── embedding.py    # int8 ONNX 모델 단일 로더 및 동시 출력 구현
│       │   ├── reranking.py    # Late Interaction (MaxSim) 엔진 구현
│       │   └── search.py       # django-paradedb ORM 통합 검색 파이프라인
│       └── management/
│           └── commands/
│               └── ingest_docs.py # 멀티벡터 생성 로직 추가
└── tests/
    └── test_search.py          # 성능 및 정밀도 검증 테스트 추가
```

**구조 결정**: 기존 `django_server` 앱의 `documents` 도메인 내부에 서비스 로직을 통합하며, ParadeDB 연동을 위해 모델 메타데이터를 업데이트함.

## 복잡성 추적

> **특이 사항 없음.**
