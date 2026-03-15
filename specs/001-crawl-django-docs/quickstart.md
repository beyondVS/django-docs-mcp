# 퀵스타트 가이드 (Quickstart Guide): Django Cookbook Crawler

**기능**: Django 관련 문서 RAG 데이터 소스 크롤링 (`001-crawl-django-docs`)
**날짜**: 2026-03-15

## 1. 환경 설정

### 필수 요구 사항
- Python 3.14+
- `uv` 패키지 매니저 (권장)

### 의존성 설치
```bash
uv add httpx readability-lxml markdownify tenacity PyYAML beautifulsoup4 lxml
```

## 2. 크롤러 실행

### Django ORM Cookbook 수집
```bash
python crawler/orm_cookbook.py
```

### Django Admin Cookbook 수집
```bash
python crawler/admin_cookbook.py
```

## 3. 결과 확인
수집된 파일은 다음 경로에서 확인할 수 있습니다:
- `data_sources/django2-orm-cookbook/`
- `data_sources/django2-admin-cookbook/`

각 마크다운 파일의 상단에 다음과 같은 메타데이터가 포함되어 있는지 확인하십시오:
```yaml
---
source_url: https://books.agiliq.com/...
target_version: 2.x
collected_at: 2026-03-15T...
---
```

## 4. 문제 해결
- **429 Too Many Requests**: 크롤러가 자동으로 지수 백오프 대기 후 재시도합니다. 강제로 중단하지 말고 기다려 주십시오.
- **lxml 설치 오류**: Python 3.14 환경에서 lxml 빌드 실패 시, 시스템에 `libxml2`, `libxslt` 개발 헤더가 설치되어 있는지 확인하십시오.
