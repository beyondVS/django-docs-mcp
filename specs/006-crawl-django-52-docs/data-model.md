# 데이터 모델 (Data Model)

Django 5.2 문서 크롤러에서 다루는 주요 데이터 엔티티와 구조를 정의합니다.

## Django 5.2 문서 (Document)

크롤링 및 변환 파이프라인에서 처리되는 개별 문서의 메타데이터 및 콘텐츠를 나타냅니다.

### 필드 (Fields)

- `source_url` (String): 원본 웹페이지 URL. (예: `https://docs.djangoproject.com/en/5.2/intro/overview/`)
- `target_version` (String): 대상 Django 버전. 항상 `5.2`로 고정.
- `collected_at` (Datetime): 문서가 크롤링 및 변환된 ISO 8601 타임스탬프.
- `content` (String): 마크다운 형식으로 변환된 문서 본문.
- `file_path` (String): `data_sources/django-5.2-docs/` 하위의 상대 경로. 원본 `docs/` 폴더 내의 계층 구조를 유지합니다.

### 상태 전이 (State Transitions)

1. **RST 다운로드**: Git을 통해 로컬 `.temp/django_src/docs` 폴더에 `.txt` 파일들로 저장됨.
2. **파싱 및 변환**: `docutils` 기반의 변환기를 통해 RST AST로 파싱된 후, Markdown 텍스트로 변환됨.
3. **메타데이터 추가**: 파일 경로를 분석하여 `source_url`을 생성하고, Front Matter 형태의 메타데이터를 추가.
4. **저장**: `data_sources/django-5.2-docs/` 경로에 최종 `.md` 파일로 저장됨.

### 유효성 검사 규칙 (Validation Rules)

- 생성된 Markdown 파일은 반드시 상단에 YAML Front Matter 블록(`---` 로 묶인 부분)을 포함해야 합니다.
- `source_url` 메타데이터는 `https://docs.djangoproject.com/en/5.2/`로 시작해야 합니다.
- 파일 계층 구조는 원본 저장소의 `docs/` 디렉터리 하위 구조와 1:1 매핑되어야 합니다 (예: `docs/intro/overview.txt` -> `data_sources/django-5.2-docs/intro/overview.md`).
