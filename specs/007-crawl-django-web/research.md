# 조사 보고서: Django 5.2 공식 문서 웹 크롤링 및 마크다운 변환

본 문서는 Django 5.2 공식 문서 웹사이트(`https://docs.djangoproject.com/en/5.2/`)를 재귀적으로 크롤링하고 고품질 마크다운으로 변환하기 위한 기술적 조사 결과를 담고 있습니다.

## 1. URL 구조 및 파일 경로 매핑 (Decision)

### 결정 (Decision)
URL의 계층 구조를 로컬 파일 시스템의 디렉터리 구조로 1:1 매핑합니다.

- **URL 예시**: `https://docs.djangoproject.com/en/5.2/ref/models/fields/`
- **로컬 저장 경로**: `data_sources/django-5.2-docs/ref/models/fields.md`
- **인덱스 처리**: 트레일링 슬래시가 있는 URL은 해당 디렉터리 내의 `index.md`가 아닌, 경로의 마지막 이름을 파일명으로 사용합니다 (예: `.../ref/models/` -> `ref/models.md`). 단, 중첩된 하위 페이지가 있는 경우 디렉터리를 생성합니다.

### 근거 (Rationale)
RAG 검색 시 문서의 맥락을 유지하기 위해 URL 계층 구조를 보존하는 것이 유리하며, 로컬 탐색 및 관리도 용이합니다.

### 고려된 대안 (Alternatives Considered)
- **Flat 구조**: 모든 파일을 단일 폴더에 저장하고 URL을 해싱하여 파일명으로 사용. (비추천: 파일 관리가 어렵고 계층적 맥락 손실)
- **Slug 기반**: URL 슬러그를 하이픈으로 연결하여 저장 (예: `ref-models-fields.md`). (비추천: 디렉터리 구조보다 가독성이 떨어짐)

## 2. 콘텐츠 추출 및 마크다운 변환 전략

### 결정 (Decision)
- **추출 영역**: `<article id="docs-content">`를 최우선으로 하며, 없을 경우 `<main id="main-content">`를 폴백으로 사용합니다.
- **제목 추출**: `<article>` 내의 첫 번째 `<h1>` 태그를 추출하여 YAML 메타데이터의 `title` 필드에 기록합니다.
- **링크 보정**: `BeautifulSoup`을 사용하여 모든 `<a>` 태그의 `href` 속성을 절대 URL로 변환합니다. `urllib.parse.urljoin`을 활용하여 현재 페이지 URL을 기준으로 상대 경로를 계산합니다.
- **이미지 보정**: `<img>` 태그의 `src`를 절대 URL로 변환하고 마크다운 문법(`![alt](url)`)을 유지합니다.

### 근거 (Rationale)
Django 공식 문서는 Sphinx로 빌드되어 일관된 HTML 구조를 가지고 있습니다. `#docs-content`는 문서의 실제 본문을 가장 정확하게 포함하고 있는 영역입니다.

## 3. 크롤링 제어 및 효율성 (Decision)

### 결정 (Decision)
- **동시성 제어**: `httpx.AsyncClient`와 `asyncio.Semaphore(5)`를 사용하여 동시 요청 수를 5개로 제한합니다.
- **Resume 기능**: 로컬 임시 폴더(`crawler/.temp/django-5.2-docs/`)에 이미 HTML 파일이 존재하고 유효한 경우 요청을 건너뜁니다.
- **고립된 파일 정리**: 전체 크롤링 세션 동안 방문한 URL 목록을 메모리에 유지하고, 작업 완료 후 로컬 디렉터리를 스캔하여 방문 목록에 없는 파일을 삭제합니다.

### 근거 (Rationale)
대상 서버에 부하를 주지 않으면서(5개 제한), 중단된 작업을 효율적으로 재개하고(Resume), 원격지와 로컬의 상태를 동기화(Cleanup)하기 위함입니다.

## 4. 기술 스택 및 라이브러리 (Decision)

### 결정 (Decision)
- **HTTP Client**: `httpx` (비동기 지원 및 재시도 로직 구현 용이)
- **HTML Parsing**: `BeautifulSoup4` (LXML 파서 사용)
- **Markdown Conversion**: `markdownify` (HTML 구조를 마크다운으로 변환)
- **Retry Logic**: `tenacity` (지수 백오프 및 재시도 전략)
- **Progress Bar**: `tqdm` (실시간 진행 상황 표시)

### 근거 (Rationale)
기존 `crawler/utils/`에 구현된 라이브러리들과 일치하며, 프로젝트 헌법(Constitution)의 기술 표준을 준수합니다.
