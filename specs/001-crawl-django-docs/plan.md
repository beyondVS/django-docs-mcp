# 구현 계획서: Django 관련 문서 RAG 데이터 소스 크롤링

**브랜치**: `001-crawl-django-docs` | **날짜**: 2026-03-15 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/001-crawl-django-docs/spec.md`의 기능 명세서

## 요약
Django ORM Cookbook 문서를 RAG(검색 증강 생성)에 적합한 마크다운 형식으로 자동 수집하는 크롤러를 구축합니다. `httpx` 비동기 엔진과 `readability-lxml`을 사용하여 본문을 추출하고, `markdownify`를 통해 코드 블록이 보존된 마크다운을 생성합니다. 수집된 데이터는 `data_sources/` 하위에 URL 구조를 반영하여 계층적으로 저장됩니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.13 (Type 준수 의무)
**주요 의존성**: `httpx` (Async HTTP Client), `readability-lxml` (Content Extraction), `markdownify` (HTML to MD), `PyYAML` (Metadata), `beautifulsoup4` (Fallback)
**저장소**: 로컬 파일 시스템 (`data_sources/`)
**테스트**: `pytest`
**대상 플랫폼**: Docker 기반 컨테이너 환경
**프로젝트 유형**: 데이터 수집용 CLI 툴
**성능 목표**: 최대 5개 이내의 동시성 유지, 지수 백오프 기반 재시도
**제약 사항**: UTF-8 인코딩, 파이썬 코드 블록 분할 금지
**폴백 전략**: `readability-lxml`이 본문 추출에 실패(빈 결과 또는 짧은 텍스트)할 경우, `BeautifulSoup`을 사용하여 `.section`, `#content` 등 주요 HTML 컨테이너를 직접 타겟팅하는 로직을 `converter.py`에 포함함.
**규모/범위**: Django 2.x 기반 Django ORM Cookbook 문서 전체 수집 및 변환

## 헌법 준수 확인 (Constitution Check)

*게이트(GATE): 0단계 리서치 전에 반드시 통과해야 합니다. 1단계 설계 후 다시 확인하십시오.*

- [x] **RAG 정확성 확인**: 마크다운 변환 시 코드 블록 및 헤딩 구조를 보존하여 검색 품질을 보장함.
- [x] **아키텍처 분리 확인**: 수집 로직은 `crawler/` 폴더에 독립적으로 구현되며 Django 서버와 분리됨.
- [x] **데이터 무결성 확인**: `data_sources/` 하위에 출처 기반의 계층적 구조를 생성하여 데이터 SSOT를 준수함.
- [x] **컨테이너 환경 확인**: 모든 작업은 Docker 환경에서 실행 가능한 구조로 설계됨.

## 프로젝트 구조

### 문서 (이 기능 관련)

```text
specs/001-crawl-django-docs/
├── plan.md              # 이 파일
├── research.md          # 0단계 출력물
├── data-model.md        # 1단계 출력물
├── quickstart.md        # 1단계 출력물
├── contracts/           # 1단계 출력물
└── checklists/          # 품질 체크리스트
```

### 소스 코드 (저장소 루트)

```text
crawler/
├── utils/
│   ├── scraper.py       # httpx 및 재시도 로직 공통 유틸리티
│   ├── converter.py     # readability 및 markdownify 변환 로직
│   └── storage.py       # 경로 관리 및 파일 저장 로직
└── orm_cookbook.py      # ORM Cookbook 시작 스크립트

data_sources/
└── django2-orm-cookbook/
```

**구조 결정**: 프로젝트 폴더 구조 방침에 따라 `crawler/` 폴더를 신설하고, 대상 시작 스크립트와 공통 유틸리티를 분리하여 모듈화된 구조를 채택함.

## 복잡성 추적

| 위반 사항 | 필요한 이유 | 더 단순한 대안을 거부한 이유 |
|-----------|------------|---------------------------|
| 해당 없음 | 헌법 및 설계 지침을 엄격히 준수함 | - |
