# 데이터 모델 (Data Model): Django Cookbook Crawler

**기능**: Django 관련 문서 RAG 데이터 소스 크롤링 (`001-crawl-django-docs`)
**날짜**: 2026-03-15

## 1. 개요
본 모델은 크롤링 대상 설정과 수집된 마크다운 문서의 메타데이터 구조를 정의합니다.

## 2. 엔티티 및 속성

### DataSource (설정 엔티티)
- **name**: 수집 대상의 고유 명칭 (예: `django2-orm-cookbook`)
- **base_url**: 크롤링 시작 URL
- **target_version**: 대상 Django 버전 (예: `2.x`)
- **storage_path**: 로컬 저장 디렉토리 (예: `./data_sources/django2-orm-cookbook/`)

### DocumentFile (수집 결과물)
- **file_path**: 로컬 저장 경로 (URL 계층 구조 반영)
- **content**: 마크다운으로 변환된 본문 텍스트
- **metadata**: 파일 상단에 삽입될 YAML Front Matter 구조
  - **source_url**: 원본 문서 URL
  - **target_version**: 대상 Django 버전 (고정값: `2.x`)
  - **collected_at**: 수집 일시 (ISO 8601 형식)

## 3. 유효성 검사 및 제약
- **Encoding**: 모든 파일은 `UTF-8` 인코딩으로 저장됨.
- **Unique Path**: 원본 URL 경로를 로컬 파일 경로로 일대일 매핑하여 중복 저장을 방지함.
- **Semantic Metadata**: 모든 문서 상단에는 반드시 메타데이터 블록이 포함되어야 함.
