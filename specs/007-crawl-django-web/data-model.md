# 데이터 모델: Django 5.2 공식 문서 크롤러

본 문서는 Django 5.2 공식 문서 웹 크롤러 구현을 위한 데이터 모델 및 엔티티 구조를 정의합니다.

## 1. 주요 엔티티 (Main Entities)

### CrawlerConfig (크롤러 설정)
- `root_url`: `str` (시작점: `https://docs.djangoproject.com/en/5.2/`)
- `prefix_filter`: `str` (포함 접두사: `https://docs.djangoproject.com/en/5.2/`)
- `exclude_patterns`: `List[str]` (제외 패턴: `.../releases/` 등)
- `temp_dir`: `Path` (HTML 저장소: `crawler/.temp/django-5.2-docs`)
- `output_dir`: `Path` (마크다운 저장소: `data_sources/django-5.2-docs`)
- `concurrency`: `int` (동시 요청 수: 기본 5)

### DocumentFile (문서 파일)
- `url`: `str` (정규화된 원본 URL, 트레일링 슬래시 포함)
- `title`: `str` (추출된 문서 제목)
- `html_path`: `Path` (로컬 HTML 파일 경로)
- `md_path`: `Path` (로컬 마크다운 파일 경로)
- `version`: `str` (대상 버전: `5.2`)
- `metadata`: `Dict[str, Any]` (YAML Front Matter 정보)

### CrawlSession (수집 세션)
- `visited_urls`: `Set[str]` (방문 완료된 URL 목록, 중복 방문 방지 및 고립 파일 정리용)
- `pending_urls`: `asyncio.Queue` (수집 대기 중인 URL 큐)
- `start_time`: `datetime` (세션 시작 시간)
- `stats`: `Dict[str, int]` (수집 성공/실패 수, 총 페이지 수 등)

## 2. 유효성 검사 규칙 (Validation Rules)

### URL 정규화
- 모든 URL은 끝에 슬래시(`/`)가 포함되도록 정규화되어야 합니다.
- `https://docs.djangoproject.com/en/5.2/ref/models` -> `https://docs.djangoproject.com/en/5.2/ref/models/`

### 중복 방지 (High-Level)
- `visited_urls` 집합을 통해 동일 URL에 대한 중복 수집을 방지합니다.
- 동일 URL에 대해 수집(Fetch)이 발생한 경우 항상 최신 내용으로 로컬 파일을 업데이트합니다.

### 계층 구조 매핑
- URL 경로의 `/en/5.2/` 이후 부분을 로컬 디렉터리 구조로 사용합니다.
- 상위 디렉터리가 존재하지 않을 경우 재귀적으로 생성합니다.
