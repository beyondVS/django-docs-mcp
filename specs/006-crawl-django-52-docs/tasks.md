# 작업 목록 (Tasks): Django 5.2 문서 크롤러

이 문서는 `006-crawl-django-52-docs` 기능 구현을 위한 상세 작업 목록입니다. 각 작업은 독립적으로 실행 가능하도록 작성되었습니다.

## 1단계: 설정 및 기초 (Setup & Foundational)
*공통 모듈 및 프로젝트 초기화 작업*

- [ ] T001 `crawler/utils/rst_converter.py` 모듈 생성 및 기본 골격 작성 (docutils 임포트)
- [ ] T002 [P] `crawler/tests/test_rst_converter.py` 테스트 파일 생성
- [ ] T003 `crawler/.gitignore` 파일에 `.temp/` 및 `.temp/django_src/` 경로 추가 확인/반영

## 2단계: 사용자 스토리 1 - Django 5.2 문서 수집 및 변환 (P1)
**목표**: GitHub에서 문서를 다운로드하고 RST 파싱 후 Markdown으로 변환하여 저장
**테스트**: 5.2 크롤러 스크립트 실행 후 `data_sources/django-5.2-docs/` 하위에 메타데이터가 포함된 변환된 마크다운 문서 생성 확인

- [ ] T004 [US1] `crawler/utils/rst_converter.py`에 RST 문자열을 마크다운 문자열로 변환하는 `rst_to_markdown` 핵심 함수 구현 (docutils 기반 파싱)
- [ ] T005 [US1] `crawler/utils/rst_converter.py`에 파일 경로 기반으로 `source_url` 메타데이터(Front Matter)를 추가하여 최종 마크다운을 반환하는 함수 구현
- [ ] T006 [US1] `crawler/django52_crawler.py` 스크립트 파일 생성
- [ ] T007 [US1] `crawler/django52_crawler.py` 내부에 `subprocess` 또는 `git` 명령어를 활용하여 `stable/5.2.x` 브랜치의 `docs` 폴더를 `crawler/.temp/django_src`에 sparse-checkout으로 클론하는 로직 구현
- [ ] T008 [US1] `crawler/django52_crawler.py`에 `.temp/django_src/docs` 내의 모든 `.txt` (RST) 파일을 재귀적으로 탐색하는 로직 구현
- [ ] T009 [US1] `crawler/django52_crawler.py`에 각 탐색된 파일을 읽어 `rst_converter`를 통해 변환하고, 계층 구조를 유지하며 `data_sources/django-5.2-docs/` 디렉터리에 `.md` 확장자로 저장하는 로직 구현
- [ ] T010 [US1] `crawler/tests/test_rst_converter.py`에 `rst_to_markdown` 함수 및 메타데이터 추가 함수에 대한 단위 테스트 작성

## 3단계: 사용자 스토리 2 - 기존 크롤러 하위 호환성 유지 (P2)
**목표**: 기존 크롤링 유틸리티를 변경하지 않아 기존 크롤러 동작 유지
**테스트**: `uv run pytest crawler/tests` 및 기존 크롤러 스크립트 실행 정상 여부 확인

- [ ] T011 [US2] `crawler/tests/` 하위의 기존 테스트 모듈(`test_converter.py` 등)이 정상 통과하는지 검증 (기존 파일 수정 여부 점검)
- [ ] T012 [US2] `crawler/orm_cookbook.py` 파일 등 기존 크롤러 스크립트를 변경 없이 실행하여 하위 호환성 최종 검증

## 4단계: 다듬기 (Polish)

- [ ] T013 전체 `crawler/` 디렉터리에 대해 `uv run ruff check --fix` 및 `uv run ruff format` 실행
- [ ] T014 `crawler/django52_crawler.py` 및 `crawler/utils/rst_converter.py`의 모든 함수에 Google Style Docstring이 한국어로 작성되었는지 확인 및 보완

## 구현 전략

- **MVP**: 사용자 스토리 1의 핵심 파이프라인(Git 클론 -> 파일 탐색 -> RST 파싱 -> Markdown 변환 -> 파일 저장)을 최우선으로 구현합니다. (T004 ~ T009)
- 구현 시 `utils/rst_converter.py`를 먼저 완성하여 파싱/변환 로직을 확립한 후, `django52_crawler.py`에서 이를 조립(Orchestration)하는 방식으로 진행합니다.
- 기존 파일(특히 `utils/converter.py` 등)은 수정하지 않음을 통해 T011/T012 단계의 부담을 최소화합니다.

## 의존성 그래프
1. T001, T003 (설정)
2. T004 -> T005 -> T010 (RST 파싱 코어)
3. T007 (다운로드) -> T008 (탐색) -> T009 (변환 및 저장 통합) [모두 T006, T004/T005 의존]
4. T011, T012 (하위 호환성 검증)
5. T013, T014 (다듬기)
