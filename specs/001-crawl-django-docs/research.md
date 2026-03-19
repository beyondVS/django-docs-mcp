# 기술 조사 보고서 (Research Report): Django ORM Cookbook Crawler

**기능**: Django 관련 문서 RAG 데이터 소스 크롤링 (`001-crawl-django-docs`)
**날짜**: 2026-03-15

## 1. 기술 선택 및 결정

### 결정 1: 비동기 크롤링 엔진 (`httpx` + `tenacity`)
- **선택**: `httpx.AsyncClient`와 `tenacity` 라이브러리 활용.
- **근거**: `httpx`는 비동기 요청을 기본 지원하며, `tenacity`는 429(Too Many Requests) 및 네트워크 타임아웃 발생 시 지수 백오프(Exponential Backoff)와 지터(Jitter)를 적용한 정교한 재시도 로직을 선언적으로 구현할 수 있게 함.
- **대안**: `aiohttp` (세션 관리의 복잡성), `requests` (동기 방식으로 성능 저하).

### 결정 2: 본문 추출 알고리즘 (`readability-lxml` + `BeautifulSoup` 폴백)
- **선택**: `readability.Document` 활용 및 실패 시 `beautifulsoup4` 활용.
- **근거**: Mozilla의 Readability 알고리즘은 휴리스틱 기반으로 본문(`article`, `main` 등)을 정확하게 감지하는 데 최적화됨. 다만 비표준 HTML 구조로 인해 추출이 실패할 경우를 대비하여 `BeautifulSoup`을 사용해 `.section`, `#content` 등의 CSS 셀렉터로 직접 타겟팅하는 폴백(Fallback) 전략을 추가함.
- **Python 3.13 이슈**: `lxml` 빌드 의존성 문제가 있을 수 있으므로 Docker 컨테이너 빌드 시 `libxml2`, `libxslt` 개발 헤더를 포함하거나 정적 빌드 옵션을 권장함.

### 결정 3: HTML to Markdown 변환 (`markdownify`)
- **선택**: `markdownify.markdownify` 함수 활용 (사용자 정의 콜백 포함).
- **근거**: `code_language_callback`을 통해 HTML 클래스명(예: `language-python`)에서 언어 힌트를 추출하여 마크다운 코드 펜스(```python)를 생성함으로써 RAG 시스템의 코드 이해도를 높임.

### 결정 4: 동시성 제어 (`asyncio.Semaphore`)
- **선택**: `asyncio.Semaphore(5)`를 활용하여 동시 요청 수를 엄격히 제한.
- **근거**: 서버 부하를 최소화하면서도 비동기의 이점을 살릴 수 있는 최적의 임계값 설정.

## 2. 조사 결과 요약 (Best Practices)

- **Rate Limit 대응**: `wait_exponential` 전략을 사용하여 대기 시간을 2s, 4s, 8s 등으로 늘리고, 최대 30초를 넘지 않도록 제한함.
- **코드 블록 보존**: `markdownify` 설정 시 `strip_pre=True`와 `convert=['pre', 'code']`를 명시적으로 설정하여 기술 문서의 핵심인 코드 가독성을 보장함.
- **경로 매핑**: URL 경로에서 특수 문자를 제거하고 계층적 폴더 구조를 생성하기 위해 `pathlib`과 `urllib.parse`를 조합하여 안전한 파일명을 생성함.

## 3. 미결정 사항 (Open Questions)
- 없음. 명시된 요구사항과 조사 결과를 통해 기술적 불확실성이 모두 해소됨.
