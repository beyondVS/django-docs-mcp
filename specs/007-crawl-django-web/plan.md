# 구현 계획서: Django 5.2 공식 문서 웹 크롤링 및 마크다운 변환

**브랜치**: `007-crawl-django-web` | **날짜**: 2026-03-24 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/007-crawl-django-web/spec.md`의 기능 명세서

## 요약

Django 5.2 공식 웹사이트(`https://docs.djangoproject.com/en/5.2/`)를 재귀적으로 크롤링하여 본문을 추출하고, RAG 엔진에 최적화된 고품질 마크다운으로 변환하는 파이프라인을 구축합니다. `httpx`를 통한 비동기 수집과 `BeautifulSoup` 및 `markdownify`를 활용한 정밀 추출 및 변환을 적용하며, URL 계층 구조를 보존하고 모든 링크를 절대 URL로 보정하여 데이터 품질을 보장합니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.13
**주요 의존성**: `httpx` (Async HTTP), `beautifulsoup4` (HTML Parsing), `markdownify` (MD Conversion), `tqdm` (UI), `tenacity` (Retry)
**저장소**: 로컬 파일 시스템 (Temporary HTML & Final Markdown)
**테스트**: `pytest`
**대상 플랫폼**: CLI (개발자 및 데이터 관리자용)
**프로젝트 유형**: Crawler/CLI 도구
**성능 목표**: 동시 요청 수 5개 제한, 1,000개 이상의 문서 페이지 수집 및 변환
**제약 사항**: Trailing Slash 정규화, `/en/5.2/` 접두사 제한, `/releases/` 제외
**규모/범위**: Django 5.2 공식 문서 전체 (수천 페이지 분량)

## 헌법 준수 확인 (Constitution Check)

- [x] **RAG 정확성 확인**: 마크다운 분할이 H1(메타데이터 제목) 및 본문 태그(`<article id="docs-content">`) 기반으로 설계되었으며, `markdownify`를 통해 파이썬 코드 블록이 보존됩니다.
- [x] **아키텍처 분리 확인**: 모든 로직이 `crawler/` 컴포넌트 내부에서 독립적으로 작동하며, 결과물은 `data_sources/`로 전달됩니다.
- [x] **데이터 무결성 확인**: URL 계층 구조를 로컬 디렉터리에 1:1 매핑하여 지식 데이터의 계층적 맥락을 유지합니다.
- [x] **컨테이너 환경 확인**: `pyproject.toml`을 통한 독립적 가상환경 및 `uv sync` 기반의 재현 가능한 환경이 구축되어 있습니다.

## 프로젝트 구조

### 문서 (이 기능 관련)

```text
specs/007-crawl-django-web/
├── spec.md              # 기능 명세서
├── plan.md              # 이 파일
├── research.md          # 0단계 결과 (URL 매핑, 추출 전략 등)
├── data-model.md        # 1단계 결과 (엔티티, 설정 구조)
├── quickstart.md        # 1단계 결과 (실행 방법)
└── contracts/           # 1단계 결과 (CLI 명령 규격)
    └── cli_contract.md
```

### 소스 코드 (저장소 루트)

```text
crawler/
├── django52_crawler.py  # 메인 CLI 진입점 (신규)
├── utils/
│   ├── scraper.py       # 비동기 수집 로직 (기존 재활용 및 확장)
│   ├── converter.py     # HTML-MD 변환 로직 (기존 재활용 및 확장)
│   ├── storage.py       # 파일 저장 및 계층 구조 관리 (기존 재활용)
│   └── logger.py        # 로깅 유틸리티
└── tests/
    ├── test_scraper.py  # 수집 기능 테스트
    └── test_converter.py # 변환 및 링크 보정 테스트
```

**구조 결정**: 기존 `crawler` 패키지 구조를 유지하며, `django52_crawler.py`를 신규 진입점으로 추가하여 명세에 정의된 전용 수집 로직을 구현합니다.

## 복잡성 추적

> **헌법 준수 확인에서 정당화가 필요한 위반 사항이 있는 경우에만 작성하십시오.**

(위반 사항 없음)
