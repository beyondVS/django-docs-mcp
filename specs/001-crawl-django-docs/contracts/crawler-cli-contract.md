# CLI 컨트랙트 (CLI Contract): Django Cookbook Crawler

**기능**: Django 관련 문서 RAG 데이터 소스 크롤링 (`001-crawl-django-docs`)
**날짜**: 2026-03-15

## 1. 개요
본 문서는 `crawler/` 디렉토리 내의 독립적인 수집 스크립트 실행 및 공통 인터페이스 규약을 정의합니다.

## 2. 실행 인터페이스 (CLI Entry Points)

### Django ORM Cookbook 수집
- **실행 명령**: `python crawler/orm_cookbook.py`
- **주요 파라미터**: (내부 정의) `START_URL`, `STORAGE_DIR`
- **출력**: `data_sources/django2-orm-cookbook/` 하위에 계층적 마크다운 파일 생성

## 3. 공통 유틸리티 규약 (`crawler/utils/`)

### Scraper (`scraper.py`)
- `fetch_url(url: str) -> str`: 비동기 HTTP GET 요청, 429 에러 발생 시 재시도 로직 포함.

### Converter (`converter.py`)
- `extract_content(html: str) -> str`: Readability 알고리즘을 사용한 본문 추출.
- `to_markdown(html: str, source_url: str) -> str`: 마크다운 변환 및 YAML Front Matter 삽입.

### Storage (`storage.py`)
- `save_file(path: str, content: str) -> None`: UTF-8 인코딩으로 파일 저장 및 디렉토리 자동 생성.

## 4. 로깅 표준
- 모든 스크립트는 수집 성공, 실패, 재시도 대기 시간을 표준 출력(stdout)으로 실시간 보고해야 함.
