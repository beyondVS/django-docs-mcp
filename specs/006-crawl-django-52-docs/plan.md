# 구현 계획서: Django 5.2 문서 크롤러

**브랜치**: `006-crawl-django-52-docs` | **날짜**: 2026-03-23 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/006-crawl-django-52-docs/spec.md`의 기능 명세서

## 요약

Django 5.2 공식 문서를 파싱하고 마크다운 형식으로 로컬에 저장하기 위한 전용 크롤러 스크립트(`django52_crawler.py`)를 개발합니다.
문서 원본은 `git clone` (sparse-checkout 활용)을 통해 `crawler/.temp/django_src`에 임시 다운로드하며, Python의 `docutils` 라이브러리를 활용해 RST(.txt) 파일들을 마크다운 형식으로 변환합니다. 기존 크롤러 시스템(`orm_cookbook.py` 등)과의 하위 호환성을 유지하기 위해 RST 처리 전용 모듈(`rst_converter.py`)을 신규 작성하여 모듈 간 충돌을 방지합니다. 변환된 문서들은 `data_sources/django-5.2-docs/` 하위에 원본 저장소의 폴더 구조를 유지하며 저장됩니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.13
**주요 의존성**: `docutils` (RST 파싱 및 Markdown 변환), `git` CLI (저장소 클론)
**저장소**: 로컬 파일 시스템 (`data_sources/django-5.2-docs/`)
**테스트**: `pytest` (Crawler 유닛 테스트)
**대상 플랫폼**: Linux/Windows 환경 (CLI 실행)
**프로젝트 유형**: 로컬 CLI 데이터 수집 도구
**성능 목표**: 전체 파싱 및 변환 소요 시간 2분 이내
**제약 사항**: 기존 크롤링 유틸리티(`converter.py`, `scraper.py`) 기능 변경 없이 독립적 구현 필요
**규모/범위**: 단일 브랜치(`stable/5.2.x`)의 `docs/` 폴더 내 모든 `.txt` 문서 파일 수집 (약 수백 개 예상)

## 헌법 준수 확인 (Constitution Check)

*게이트(GATE): 0단계 리서치 전에 반드시 통과해야 합니다. 1단계 설계 후 다시 확인하십시오.*

- [x] **RAG 정확성 확인**: 마크다운 분할이 H2/H3/RST 지시어 기반으로 설계되었는가? (파이썬 코드 블록 보존 여부 포함)
  *(크롤러의 변환 결과물이 추후 정확한 의미론적 청킹의 재료가 되도록 구조화된 마크다운을 출력해야 함)*
- [x] **아키텍처 분리 확인**: 로직이 Crawler / Django / FastMCP 중 올바른 컴포넌트에 할당되었는가?
  *(기존 `crawler/` 디렉터리 내에 할당됨)*
- [x] **데이터 무결성 확인**: 데이터 모델이 Source > Document > Chunk의 3단계 계층을 준수하는가?
  *(원시 Source(RST)를 Document(Markdown) 형태로 변환하여 메타데이터와 함께 저장)*
- [x] **컨테이너 환경 확인**: 실행 및 테스트 환경이 Docker/Docker Compose 기반으로 설계되었는가?
  *(공통 uv 환경 기반으로 로컬 실행)*

## 프로젝트 구조

### 문서 (이 기능 관련)

```text
specs/006-crawl-django-52-docs/
├── plan.md              # 이 파일 (/speckit.plan 명령 출력물)
├── research.md          # 0단계 출력물 (/speckit.plan 명령)
├── data-model.md        # 1단계 출력물 (/speckit.plan 명령)
├── quickstart.md        # 1단계 출력물 (/speckit.plan 명령)
└── tasks.md             # 2단계 출력물 (/speckit.tasks 명령 - /speckit.plan에서 생성하지 않음)
```

### 소스 코드 (저장소 루트)

```text
crawler/
├── django52_crawler.py
├── utils/
│   └── rst_converter.py
└── tests/
    └── test_rst_converter.py

data_sources/
└── django-5.2-docs/
    └── (변환된 마크다운 파일 및 폴더 계층)
```

**구조 결정**: 기존 `crawler` 프로젝트를 유지하며, 루트 디렉터리에 새로운 5.2 전용 실행 스크립트(`django52_crawler.py`)를 추가하고, `utils/` 내부에 RST 파싱 전용 유틸리티(`rst_converter.py`)를 격리하여 구현합니다. 출력된 데이터는 `data_sources/django-5.2-docs/` 에 저장됩니다.

## 복잡성 추적

해당 사항 없음.
