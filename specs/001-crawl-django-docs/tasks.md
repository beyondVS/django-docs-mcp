# 작업 목록: 001-crawl-django-docs (Django ORM Cookbook Crawler)

**입력**: `/specs/001-crawl-django-docs/`의 설계 문서
**선행 조건**: `plan.md` (필수), `spec.md` (필수), `research.md`, `data-model.md`, `contracts/crawler-cli-contract.md`

**테스트**: `pytest`를 사용하여 크롤링 로직 및 변환 결과의 무결성을 검증합니다.

---

## 1단계: 설정 (공유 인프라)

**목적**: 프로젝트 초기화 및 기본 구조 설정

- [x] T001 [P] `crawler/` 및 `crawler/utils/` 디렉토리 구조 생성
- [x] T002 [P] `pyproject.toml`에 `httpx`, `readability-lxml`, `markdownify`, `tenacity`, `PyYAML`, `beautifulsoup4`, `lxml` 의존성 추가 및 `uv sync` 실행
- [x] T003 [P] `.ruff.toml` 또는 `pyproject.toml`에 Python 3.14 타입 체크 및 린팅 설정 추가

---

## 2단계: 기초 작업 (블로킹 선행 조건)

**목적**: 크롤링 및 변환 파이프라인을 위한 핵심 유틸리티 구현

- [x] T004 `crawler/utils/scraper.py`에 `httpx` 및 `tenacity`를 활용한 지수 백오프 기반 비동기 크롤러 유틸리티 구현
- [x] T005 `crawler/utils/converter.py`에 `readability-lxml` 본문 추출 및 실패 시 CSS 셀렉터 기반 폴백 로직(BeautifulSoup)을 포함한 변환 파이프라인 구현
- [x] T006 `crawler/utils/storage.py`에 URL 계층 구조를 반영한 파일 저장 및 경로 관리 로직 구현
- [x] T007 `crawler/utils/logger.py`에 크롤링 상태 및 에러 로깅을 위한 공통 로거 설정

**체크포인트**: 기초 작업 완료 - 공통 유틸리티가 준비되어 각 Cookbook별 크롤러 구현을 시작할 수 있습니다.

---

## 3단계: 사용자 스토리 1 & 2 - Django ORM Cookbook 수집 및 변환 (우선순위: P1) 🎯 MVP

**목표**: Django ORM Cookbook의 모든 챕터를 수집하여 마크다운으로 변환 후 로컬에 저장

**독립적 테스트**: `python crawler/orm_cookbook.py` 실행 후 `data_sources/django2-orm-cookbook/`에 마크다운 파일들이 생성되고, 내용에 본문과 코드 블록이 포함되어 있는지 확인

### 사용자 스토리 1 & 2 테스트 (선택 사항)

- [x] T008 [P] [US1] `crawler/tests/test_scraper.py`에 `httpx` 모킹을 통한 비동기 요청 및 재시도 로직 단위 테스트 작성
- [x] T009 [P] [US2] `crawler/tests/test_converter.py`에 샘플 HTML을 활용한 마크다운 변환 및 코드 블록 보존 테스트 작성

### 사용자 스토리 1 & 2 구현

- [x] T010 [US1] `crawler/orm_cookbook.py`에 ORM Cookbook 시작 URL 및 탐색 범위 정의 (내부 도메인 한정)
- [x] T011 [US1] `crawler/orm_cookbook.py`에 재귀적 링크 탐색 및 URL + 콘텐츠 해시(SHA256) 기반 중복 제거 로직 구현
- [x] T012 [US2] `crawler/orm_cookbook.py`에 수집된 HTML을 `converter.py`를 통해 마크다운으로 변환하는 파이프라인 통합
- [x] T013 [US1] `crawler/orm_cookbook.py`에 변환된 내용을 `storage.py`를 통해 `data_sources/django2-orm-cookbook/`에 저장하는 로직 연동

---

## 4단계: 사용자 스토리 3 - 메타데이터 관리 및 다듬기 (우선순위: P2)

**목표**: 수집된 문서에 Django 버전 및 출처 URL 메타데이터를 부여하고 안정성 강화

**독립적 테스트**: 생성된 마크다운 파일 상단에 YAML Front Matter가 포함되어 있는지 확인

### 사용자 스토리 3 구현

- [x] T014 [US3] `crawler/utils/converter.py`에 YAML Front Matter 생성 로직 추가 (`source_url`, `target_version: 2.x`, `collected_at`)
- [x] T015 [US3] `crawler/tests/test_metadata.py`를 작성하여 모든 저장된 파일에 필수 메타데이터가 포함되어 있는지 검증

---

## 5단계: 다듬기 및 횡단 관심사

**목적**: 안정성 강화 및 문서화

- [x] T016 [P] `crawler/utils/scraper.py`에 429 Too Many Requests 대응을 위한 동적 적응형 지연 로직 추가
- [x] T017 `README.md` 및 `specs/001-crawl-django-docs/quickstart.md`에 실행 방법 및 주요 장애(네트워크 타임아웃, 인코딩 오류, 추출 실패 시 폴백) 대응 가이드 업데이트
- [x] T018 전체 수집 프로세스 실행 및 `data_sources/` 결과물의 UTF-8 인코딩 및 마크다운 구조 최종 검수 (최소 10개 이상의 무작위 샘플링 검수 포함)

---

## 의존성 및 실행 순서

### 단계별 의존성
1. **설정 (1단계)** → **기초 작업 (2단계)** → **US1&2 (3단계)** → **US3 (4단계)** → **다듬기 (5단계)** 순으로 진행합니다.
2. Cookbook 스크립트(`orm_cookbook.py`)는 `crawler/utils/` 하위의 유틸리티들에 의존합니다.

### 병렬 작업 기회
- T001~T003 (설정 작업)은 병렬로 진행 가능합니다.
- T004~T007 (기초 유틸리티)은 구조가 설계되어 있다면 병렬로 개발 가능합니다.
- T010~T013 (ORM)은 모듈화된 기반 위에서 순차 또는 병렬로 개발 가능합니다.

---

## 구현 전략

### MVP 우선 (사용자 스토리 1 & 2)
가장 핵심적인 Django ORM Cookbook 수집 및 마크다운 변환 기능을 3단계에서 완료하여 RAG 시스템에 즉시 투입 가능한 데이터를 확보합니다.

### 점진적 전달
1. 공통 유틸리티(`utils/`)를 먼저 완성하여 코드 중복을 최소화합니다.
2. ORM Cookbook을 통해 파이프라인을 검증합니다.
3. 메타데이터 로직을 추가하여 데이터 정형성을 높입니다.
4. 최종 검수 및 안정화 작업을 수행합니다.
