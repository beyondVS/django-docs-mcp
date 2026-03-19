# 구현 계획서: django-server-core

**브랜치**: `002-django-server-core` | **날짜**: 2026-03-16 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/002-django-server-core/spec.md`의 기능 명세서

## 요약
본 계획은 기술 문서의 적재(Ingestion), 관리 및 검색 품질 검증(Playground)을 위한 중앙 Django 서버 구축을 목표로 합니다. **Django 5.2 LTS**와 **PostgreSQL + pgvector**를 기반으로 하며, 최신 **psycopg3** 드라이버를 통해 고성능 DB 연동을 구현합니다. `BAAI/bge-m3` 모델을 사용하여 고성능 벡터 검색 기능을 제공하며, 관리자 및 Staff 사용자가 품질을 테스트할 수 있는 웹 인터페이스를 포함합니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.13 (uv 권장)
**주요 의존성**:
  - Django 5.2.x (LTS - 2028년까지 지원 보장)
  - psycopg[binary] >= 3.2.1 (최신 비동기 드라이버, C-Extension 포함으로 속도 최적화)
  - pgvector-python >= 0.3.x (HNSW 인덱스 지원)
  - sentence-transformers >= 3.0.x
  - langchain-text-splitters
  - HTMX 2.x
**저장소**: PostgreSQL 16+ (pgvector 확장 활성화)
**테스트**: pytest (django-server 디렉토리 내 독립 관리)
**대상 플랫폼**: Linux 서버 (Docker 컨테이너 환경)
**프로젝트 유형**: 웹 서비스 및 데이터 관리 CLI
**성능 목표**: 코사인 유사도 검색 1초 이내 (Top-5 결과)
**제약 사항**: <800 토큰 청킹 사이즈 준수, 파이썬 코드 블록 보존, 1024차원 벡터 고정
**규모/범위**: Django 공식 문서 전 버전(2.x~5.x) 및 관련 에코시스템 문서 적재 가능

## 헌법 준수 확인 (Constitution Check)

*게이트(GATE): 0단계 리서치 및 1단계 설계 완료 후 통과 확인.*

- [x] **RAG 정확성 확인**: 마크다운 헤더(H2/H3) 기반 분할 설계 완료. 파이썬 코드 블록 보존 로직(정규식 후처리) 포함.
- [x] **아키텍처 분리 확인**: `django_server` 멤버 프로젝트 내 독립 구현. `mcp_server`와 DB만 공유하며 로직 분리됨.
- [x] **데이터 무결성 확인**: Document > Section > Chunk의 3단계 계층 구조 및 버전별 독립 엔티티 설계 반영.
- [x] **컨테이너 환경 확인**: `docker-compose.yml`을 통한 DB 공유 및 환경 설정 규격 정의 완료.

## 프로젝트 구조

### 문서 (이 기능 관련)

```text
specs/002-django-server-core/
├── plan.md              # 이 파일
├── research.md          # 0단계 리서치 보고서
├── data-model.md        # 1단계 데이터 모델 설계
├── quickstart.md        # 1단계 개발자 퀵스타트
├── contracts/           # 1단계 인터페이스 규격
│   ├── ingestion-cli-contract.md
│   └── playground-ui-contract.md
└── tasks.md             # 2단계 작업 분할 (tasks 명령 예정)
```

### 소스 코드 (django_server 디렉토리)

```text
django_server/
├── pyproject.toml       # 패키징 및 의존성 관리
├── Dockerfile           # 인프라 설정
├── tests/               # 테스트 메타데이터
└── src/                 # 순수 Django 애플리케이션 및 비즈니스 로직
    ├── manage.py
    ├── core/            # Django 프로젝트 설정
    └── documents/       # 문서 및 검색 핵심 앱
        ├── management/
        │   └── commands/
        │       └── ingest_docs.py
        ├── models.py
        ├── views.py
        └── services/    # Embedding, Chunking 로직
```

**구조 결정**: 백엔드 아키텍처의 정석인 `src` 레이아웃(옵션 B)을 채택함. 이는 인프라 설정과 비즈니스 로직을 엄격히 분리하고, 향후 `mcp_server` 등 다른 워크스페이스 멤버에서 Django 모델을 임포트할 때 패키징 안정성을 보장하기 위함임.

## 복잡성 추적

> **헌법 준수 확인에서 정당화가 필요한 위반 사항이 있는 경우에만 작성하십시오.**

| 위반 사항 | 필요한 이유 | 더 단순한 대안을 거부한 이유 |
|-----------|------------|---------------------------|
| **Section 엔티티 추가** | H2/H3 헤더 제목을 검색 문맥으로 주입하기 위함 | 단순 Chunking만으로는 헤더 정보가 유실되어 검색 품질이 저하됨 |
| **HTMX 도입** | 실시간 검색 결과 렌더링을 통한 품질 테스트 효율성 증대 | 일반적인 Django Template만으로는 페이지 새로고침이 발생하여 테스트 UX가 불편함 |
