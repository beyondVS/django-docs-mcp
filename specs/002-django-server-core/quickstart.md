# 퀵스타트 가이드: django-server-core

`django_server` 멤버 프로젝트의 개발 환경 설정 및 데이터 적재 과정을 안내합니다.

## 1. 전제 조건 (Prerequisites)
- **Python**: 3.14 (uv 권장)
- **Docker**: Docker Desktop (PostgreSQL + pgvector 구동 필요)
- **Repo**: `django-docs-mcp` 저장소 루트

## 2. 설치 및 설정 (Installation)

### 가상환경 및 의존성 설치
```bash
cd django_server
uv sync
```

### 데이터베이스 및 컨테이너 구동
저장소 루트에서 Docker Compose를 실행합니다.
```bash
cd ..
docker-compose up -d db
```

### 데이터베이스 마이그레이션 및 슈퍼유저 생성
```bash
cd django_server
uv run python src/manage.py migrate
uv run python src/manage.py createsuperuser
```

## 3. 데이터 적재 (Ingestion)
`data_sources/` 폴더 내의 마크다운 파일들을 벡터 데이터베이스에 적재합니다.
```bash
cd django_server
uv run python src/manage.py ingest_docs ../data_sources/django2-orm-cookbook/ --doc-version 4.2 --category Reference
```

## 4. Playground 실행
Django 개발 서버를 구동하고 웹 브라우저에서 Playground를 확인합니다.
```bash
uv run python src/manage.py runserver
```
- **Playground 접속**: `http://127.0.0.1:8000/playground/` (로그인 필요)

## 5. 주요 확인 사항
- **임베딩 모델**: 첫 실행 시 `BAAI/bge-m3` 모델을 자동으로 다운로드하므로 네트워크 환경을 확인하십시오.
- **벡터 검색**: Playground에서 검색어를 입력하여 코사인 유사도 결과가 정상적으로 나오는지 확인하십시오.
- **Admin**: `http://127.0.0.1:8000/admin/`에서 적재된 `Document`와 `Chunk` 목록을 관리할 수 있습니다.
