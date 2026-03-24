# 빠른 시작 가이드: Django 5.2 공식 문서 크롤러

본 문서는 Django 5.2 공식 문서 크롤러의 설치 및 실행 방법을 설명합니다.

## 1. 전제 조건 (Prerequisites)

- **Python 3.13** (pyenv 또는 nvm 등으로 설치 권장)
- **uv** (의존성 관리 도구)
- **Internet Connection** (Django 공식 사이트 접속 가능해야 함)

## 2. 설정 및 실행 (Setup & Execution)

### 의존성 설치
루트 디렉터리에서 다음 명령을 실행하여 모든 패키지를 동기화합니다.
`uv sync --all-packages`

### 크롤러 실행 (전체 파이프라인)
`cd crawler`
`uv run python django52_crawler.py all`

### 부분 실행 예시
- **수집만 실행 (HTML 저장)**:
  `uv run python django52_crawler.py crawl`
- **변환만 실행 (마크다운 생성)**:
  `uv run python django52_crawler.py convert`
- **강제 재수집 및 고립 파일 정리**:
  `uv run python django52_crawler.py all --force --cleanup`

## 3. 결과 확인 (Verification)

### HTML 임시 파일
수집된 HTML 파일은 아래 경로에서 확인할 수 있습니다.
`crawler/.temp/django-5.2-docs/`

### 변환된 마크다운 파일
RAG 엔진에 사용될 최종 마크다운 파일은 아래 경로에 저장됩니다.
`data_sources/django-5.2-docs/`

### 마크다운 품질 확인
각 마크다운 파일 상단에 아래와 같은 YAML 메타데이터가 포함되어 있는지 확인하십시오.
```yaml
---
source_url: https://docs.djangoproject.com/en/5.2/ref/models/fields/
title: Model field reference
target_version: 5.2
collected_at: 2026-03-24T12:00:00Z
---
```
또한, 문서 내의 모든 링크가 `https://docs.djangoproject.com/en/5.2/`로 시작하는 절대 URL인지 확인하십시오.
