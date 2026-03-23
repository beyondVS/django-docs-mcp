# 기능 명세서: Django 5.2 공식 문서 웹 크롤링 및 마크다운 변환

**기능 브랜치**: `007-crawl-django-web`
**생성일**: 2026-03-24
**상태**: 준비 완료(Ready for Plan)
**입력**: 사용자 설명: "django 5.2 문서 크롤링 기능의 동작을 변경 한다. 1. 기존 github 에서 체크아웃 하는 방식에서 https://docs.djangoproject.com/en/5.2/ 웹페이지를 크롤링 하는 방식으로 변경 - 기존 rst 파일을 markdown 으로 변환이 제대로 동작하지 않음(링크 깨짐. 내용 누락 등) 2. 크롤링 대상 - django 5.2 공식 문서 웹페이지 https://docs.djangoproject.com/en/5.2/ - 위 주소의 문서에서 <main id="main-content"> 영역의 내용 - 재귀적으로 해당 문서에서 링크가 있는 문서들 - https://docs.djangoproject.com/en/5.2/ 로 시작하는 하위 웹페이지 - 제외되야 하는 크롤링 대상 - 릴리즈 노트: https://docs.djangoproject.com/en/5.2/releases/ 및 해당 주소의 하위 주소 - 외부 사이트 - https://docs.djangoproject.com/en/5.2/ 로 시작하지 않는 주소 3. 문서의 양이 많으므로 작업을 다음같이 분리 한다. 1. 웹페이지 크롤링 HTML을 임시폴더에 저장. crawler/.temp/django-5.2-docs 2. 다운로드된 HTML을 마크다운으로 변환하여 data_sources/django-5.2-docs 폴더에 저장 4. 문서의 링크 중에 django 공식 문서로 연결되는 상대 링크는 완전한 링크로 만들어야 함. - <a class="reference internal" href=\"../../howto/logging/#logging-how-to\"><span class=\"std std-ref\">How to configure and use logging</span></a> - 위의 링크는 https://docs.djangoproject.com/en/5.2/howto/logging/#logging-how-to 로 연결됨 - RAG 검색 결과 CHUNK 에서도 https://docs.djangoproject.com/en/5.2/howto/logging/#logging-how-to 로 나와야 검색 결과를 가져다 사용하는 LLM 이 정상적으로 액세스 가능 함."

## 사용자 시나리오 및 테스트 *(필수)*

### 사용자 스토리 1 - 웹 기반 문서 수집 (우선순위: P1)

관리자는 기존 GitHub 소스 코드(RST) 대신 Django 공식 웹사이트의 HTML을 직접 크롤링하여 최신이며 렌더링이 완료된 정확한 문서를 확보하고자 합니다.

**우선순위 이유**: 기존 RST 변환 방식의 링크 깨짐 및 내용 누락 문제를 해결하기 위한 핵심 요구사항입니다.

**독립적 테스트**: 크롤러를 실행하여 `crawler/.temp/django-5.2-docs` 폴더에 공식 문서의 HTML 파일들이 원본 구조를 유지하며 저장되는지 확인하여 테스트할 수 있습니다.

**수락 시나리오(Acceptance Scenarios)**:

1. **Given** 크롤러 설정이 완료됨, **When** 크롤링 시작, **Then** `https://docs.djangoproject.com/en/5.2/` 하위의 모든 유효 문서가 HTML로 저장됨.
2. **Given** 릴리즈 노트 URL(`.../releases/`), **When** 크롤링 수행, **Then** 해당 페이지 및 하위 페이지는 무시되어야 함.

---

### 사용자 스토리 2 - 정확한 본문 추출 및 마크다운 변환 (우선순위: P1)

수집된 HTML에서 내비게이션이나 광고 영역을 제외한 실제 문서 본문(`<main id="main-content">`)만을 추출하여 깨끗한 마크다운 형식으로 변환합니다.

**우선순위 이유**: 검색 엔진(RAG)에 불필요한 노이즈(내비게이션 텍스트 등)가 섞이는 것을 방지하여 검색 품질을 높입니다.

**독립적 테스트**: 변환된 마크다운 파일을 열어 실제 문서 내용만 포함되어 있고 HTML 태그가 적절히 마크다운 문법으로 변환되었는지 확인합니다.

**수락 시나리오(Acceptance Scenarios)**:

1. **Given** 수집된 HTML 파일, **When** 마크다운 변환 수행, **Then** 결과물은 `data_sources/django-5.2-docs`에 저장되며 `<main>` 태그 외부의 내용은 포함되지 않음.

---

### 사용자 스토리 3 - 절대 링크 보정 및 RAG 호환성 (우선순위: P1)

문서 내의 상대 경로 링크를 공식 웹사이트의 전체 URL(절대 경로)로 변환하여, 검색 결과(Chunk)를 사용하는 LLM이나 사용자가 즉시 해당 문서 페이지로 이동할 수 있게 합니다.

**우선순위 이유**: RAG 시스템에서 LLM이 참조하는 링크가 유효해야 하며, 사용자가 상세 내용을 확인하기 위해 클릭했을 때 올바른 웹페이지로 연결되어야 합니다.

**독립적 테스트**: 변환된 마크다운 내의 링크(`[text](../../path/)`)가 `[text](https://docs.djangoproject.com/en/5.2/path/)` 형식으로 정확히 치환되었는지 샘플 검사를 수행합니다.

**수락 시나리오(Acceptance Scenarios)**:

1. **Given** 상대 링크가 포함된 HTML, **When** 변환 프로세스 작동, **Then** 모든 내부 링크는 `https://docs.djangoproject.com/en/5.2/`로 시작하는 절대 링크로 변경됨.

### 예외 케이스 (Edge Cases)

- **네트워크 타임아웃**: 공식 사이트 응답 지연 시 `utils/scraper.py`의 기본 재시도 메커니즘이 작동함.
- **앵커 링크(#)**: 페이지 내부 앵커 링크가 포함된 절대 경로 변환 시 앵커(`hash`) 정보가 유실되지 않고 정확히 유지되어야 함.
- **중복 콘텐츠**: URL이 다르더라도 동일한 콘텐츠(Canonical URL이 다른 경우 등)는 해시 기반 중복 체크를 통해 하나만 저장함.

## 요구 사항 *(필수)*

### 기능적 요구 사항 (Functional Requirements)

- **FR-001**: 시스템은 `https://docs.djangoproject.com/en/5.2/`를 시작점으로 하여 재귀적으로 문서를 탐색해야 함.
- **FR-002**: 시스템은 반드시 `<main id="main-content">` 태그 내부의 데이터만 추출해야 함.
- **FR-003**: 시스템은 `https://docs.djangoproject.com/en/5.2/releases/` 및 그 하위 경로는 크롤링 대상에서 제외해야 함.
- **FR-004**: 수집된 HTML은 `crawler/.temp/django-5.2-docs` 폴더에 임시 저장되어야 함.
- **FR-005**: 시스템은 HTML을 마크다운으로 변환하여 `data_sources/django-5.2-docs`에 저장해야 함.
- **FR-006**: 크롤링 시 `concurrency_limit=5`를 유지하여 대상 사이트에 과도한 부하를 주지 않아야 함 (기존 `orm_cookbook` 사례 준수).
- **FR-007**: 수집 시 중복 방지를 위해 콘텐츠 해시(SHA-256)를 검증하며, 기존 데이터와 충돌 시 덮어쓰기(Full Overwrite) 방식으로 업데이트함.

### 시스템 제약 사항 (System Constraints - Django Docs MCP)

- **SYS-001**: 데이터 청킹 시 500~800 토큰 범위 및 10% 오버랩 유지 (파이썬 코드 블록은 절대 분할하지 않음).
- **SYS-002**: 검색 API 반환 포맷은 `search_django_knowledge` 규격 준수.
- **SYS-003**: 변환된 마크다운의 파일명은 원본 URL 구조를 반영하여 생성되어야 함.

### 주요 엔티티

- **CrawlerJob**: 크롤링 대상 URL 리스트, 진행 상태, 제외 패턴을 관리하는 작업 단위.
- **DocumentFile**: 수집된 HTML 및 변환된 마크다운 파일과 해당 원본 URL 매핑 정보.

## 성공 기준 *(필수)*

### 측정 가능한 결과 (Measurable Outcomes)

- **SC-001**: 릴리즈 노트를 제외한 Django 5.2 공식 문서의 모든 페이지가 마크다운으로 변환되어 저장됨.
- **SC-002**: 변환된 마크다운 내의 모든 장고 내부 링크가 `https://docs.djangoproject.com/en/5.2/`로 시작하는 유효한 절대 링크임.
- **SC-003**: 크롤링 및 변환 프로세스가 오류 없이 완료되며, 누락된 문서가 0개여야 함.
- **SC-004**: RAG 검색 결과에서 제공되는 링크를 클릭했을 때 공식 웹사이트의 해당 섹션으로 100% 연결됨.
