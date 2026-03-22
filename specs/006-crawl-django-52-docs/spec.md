# 기능 명세서: Django 5.2 문서 크롤러

**기능 브랜치**: `006-crawl-django-52-docs`
**생성일**: 2026-03-23
**상태**: 초안(Draft)
**입력**: 사용자 설명: "django 5.2 버전의 공식 문서를 크롤러를 만든다. 1. 대상은 https://github.com/django/django/tree/stable/5.2.x/docs 이다. 2. 문서는 rst 포맷이므로 markdown 포맷으로 변환 할 수 있어야 한다. 3. 크롤러 프로젝트는 ./crawler 폴더 이다. 4. 크롤링 스크립트는 따로 만든다. 5. 크롤러 프로젝트의 유틸 함수는 기존 크롤러 작동에 문제가 없어야 한다. 6. 실제 문서의 웹페이지 경로는 https://docs.djangoproject.com/en/5.2/ 를 참고 한다. - https://docs.djangoproject.com/en/5.2/intro/overview/ - https://docs.djangoproject.com/en/5.2/faq/help/ - https://docs.djangoproject.com/en/5.2/ref/django-admin/ - https://docs.djangoproject.com/en/5.2/topics/settings/"

## Clarifications

### Session 2026-03-23

- Q: 다수의 원본 `.txt` (RST) 파일들을 대량으로 가져오기 위해 어떤 방식을 사용해야 합니까? → A: `git clone` (또는 부분 클론)을 통해 5.2 브랜치를 로컬에 다운로드한 후 `docs` 폴더 처리
- Q: 새 크롤러는 GitHub 저장소의 원본 RST(`.txt`) 파일을 파싱하여 변환해야 하는데, 어떤 도구나 라이브러리를 사용할 계획입니까? → A: `docutils`를 사용하여 파싱 후 커스텀 작성 또는 타사 플러그인 연동
- Q: `git clone`을 통해 받아온 저장소 또는 `docs` 폴더를 크롤러 프로젝트의 어느 경로에 임시 또는 영구적으로 저장할 것입니까? → A: `./crawler/.temp/django_src`에 저장하고 `./crawler/.gitignore`에 추가
- Q: 변환된 Markdown 파일들을 최종적으로 어느 경로에, 어떤 폴더 구조로 저장해야 합니까? → A: `data_sources/django-5.2-docs/` 아래에 원본 `docs` 폴더 계층 구조를 그대로 유지하여 저장
- Q: `docutils`를 이용한 RST 파싱 로직이나 Git 클론 로직 등을 기존 `crawler/utils/` 안에 통합할 것입니까, 아니면 5.2 크롤러 전용으로 분리할 것입니까? → A: `crawler/utils/rst_converter.py` 등의 새 유틸리티 모듈을 생성하여 독립적으로 구현

## 사용자 시나리오 및 테스트 *(필수)*

### 사용자 스토리 1 - Django 5.2 문서 수집 및 변환 (우선순위: P1)

관리자는 Django 5.2 공식 문서 저장소를 로컬에 클론하여 문서를 수집하고 Markdown 형태로 변환할 수 있어야 합니다.

**우선순위 이유**: Django 5.2 지식 베이스를 구축하기 위한 핵심 요구사항입니다.

**독립적 테스트**: 새로운 크롤러 스크립트를 독립적으로 실행하여 지정된 저장소가 로컬 임시 폴더(`.temp`)로 클론되고 문서가 마크다운으로 변환 및 `data_sources/django-5.2-docs/`에 저장되는지 확인합니다.

**수락 시나리오(Acceptance Scenarios)**:

1. **Given** 대상 GitHub 저장소(https://github.com/django/django/tree/stable/5.2.x)가 접근 가능할 때, **When** 5.2 크롤링 스크립트를 실행하면, **Then** Git 클론(또는 부분 클론)을 통해 `./crawler/.temp/django_src`에 문서를 가져와 `docs` 폴더 내용을 탐색합니다.
2. **Given** 클론된 RST 형식의 문서가 존재할 때, **When** 마크다운으로 변환 과정을 거치면, **Then** 웹 경로 정보(https://docs.djangoproject.com/en/5.2/...)가 포함된 메타데이터가 파일에 함께 저장되며, `data_sources/django-5.2-docs/` 아래에 원본 계층 구조를 유지하며 저장됩니다.

---

### 사용자 스토리 2 - 기존 크롤러 하위 호환성 유지 (우선순위: P2)

기존 크롤러 유틸리티 함수들을 수정하더라도 기존 크롤링 작업이 문제없이 동작해야 합니다.

**우선순위 이유**: 새로운 기능 추가로 인해 기존 데이터 수집 파이프라인이 망가지는 것을 방지해야 합니다.

**독립적 테스트**: 기존 크롤링 스크립트(`orm_cookbook.py` 등)를 실행하여 정상 작동 여부를 확인합니다.

**수락 시나리오**:

1. **Given** 기존 크롤러 스크립트가 존재할 때, **When** 해당 스크립트를 실행하면, **Then** 에러 없이 기존 방식대로 문서를 수집 및 변환합니다.

### 예외 케이스 (Edge Cases)

- Git 클론 실패(네트워크 오류 또는 권한 문제) 시: 명확한 오류 메시지를 출력하고 재시도를 안내해야 합니다.
- 일부 RST 문서가 마크다운으로 변환되는 과정에서 문법 오류가 발생할 경우: 변환 실패된 문서를 건너뛰지 않고 오류 로그를 남기되, 전체 실행이 중단되지 않아야 합니다.

## 요구 사항 *(필수)*

### 기능적 요구 사항 (Functional Requirements)

- **FR-001**: 시스템은 `git clone` (또는 부분 클론) 방식을 사용하여 `https://github.com/django/django` 저장소의 `stable/5.2.x` 브랜치에서 `docs` 폴더 내용을 `./crawler/.temp/django_src` 경로로 로컬에 다운로드해야 함
- **FR-002**: 가져온 임시 폴더가 Git 트래킹에 포함되지 않도록 `./crawler/.gitignore` 파일에 `.temp/` 경로를 추가해야 함
- **FR-003**: 시스템은 가져온 `.txt` (RST 형식) 문서를 `docutils` 기반 파서를 활용하여 Markdown 형식으로 변환해야 함
- **FR-004**: RST 파싱 및 변환 로직은 하위 호환성을 위해 기존 모듈을 수정하지 않고 `crawler/utils/rst_converter.py` 등의 새로운 유틸리티 모듈에 독립적으로 구현해야 함
- **FR-005**: 시스템은 `./crawler` 폴더 내에 Django 5.2 크롤링 전용 스크립트를 독립적으로 생성해야 함
- **FR-006**: 시스템은 문서 변환 과정에서 생성된 Markdown에 실제 문서의 웹페이지 경로(`https://docs.djangoproject.com/en/5.2/...`) 정보를 식별하여 메타데이터로 포함시켜야 함
- **FR-007**: 변환된 Markdown 파일은 `data_sources/django-5.2-docs/` 디렉터리 내에 원본 RST 파일의 폴더 계층 구조를 유지하여 저장해야 함
- **FR-008**: 기존 크롤러 스크립트(`orm_cookbook.py` 등)는 유틸리티 함수 변경 후에도 정상적으로 작동해야 함

### 시스템 제약 사항 (System Constraints - Django Docs MCP)

- **SYS-001**: 데이터 청킹 시 500~800 토큰 범위 및 10% 오버랩 유지 (파이썬 코드 블록은 절대 분할하지 않음).
- **SYS-002**: 검색 API 반환 포맷은 `search_django_knowledge` 규격(`content`, `target_version`, `document_type`, `source_url`, `relevance_score`, `extra_meta`)을 반드시 준수해야 함.
- **SYS-003**: 모든 데이터 조회는 `pgvector`의 벡터 검색(HNSW)을 통해 수행되어야 함.

### 주요 엔티티 (데이터 관련 기능인 경우 포함)

- **Django 5.2 문서 (Document)**: 원본 RST 콘텐츠, 변환된 Markdown 콘텐츠, 소스 웹 URL 등 메타데이터

## 성공 기준 *(필수)*

### 측정 가능한 결과 (Measurable Outcomes)

- **SC-001**: 새로운 5.2 크롤링 스크립트 실행 시 대상 저장소의 문서를 100% 탐색하고 가능한 모든 문서를 마크다운으로 저장함
- **SC-002**: 변환된 모든 문서에 유효한 `https://docs.djangoproject.com/en/5.2/...` 형태의 원본 URL이 메타데이터로 포함됨
- **SC-003**: 기존 크롤러 스크립트를 실행했을 때 에러 없이 성공적으로 기존 작업이 완료됨 (하위 호환성 유지)
