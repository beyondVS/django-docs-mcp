# 인터페이스 정의서: Django 5.2 크롤러 CLI

본 문서는 Django 5.2 공식 문서 크롤러의 커맨드 라인 인터페이스(CLI) 규격 및 동작을 정의합니다.

## 1. 명령 스키마 (Command Schema)

### 기본 실행
`uv run python django52_crawler.py [COMMAND] [OPTIONS]`

### 지원 명령 (Commands)
- **crawl**: `https://docs.djangoproject.com/en/5.2/` 웹페이지를 재귀적으로 방문하여 HTML 파일을 로컬 임시 폴더(`crawler/.temp/django-5.2-docs`)에 수집합니다.
- **convert**: 수집된 HTML 파일을 읽어 본문 추출 및 마크다운 변환을 수행하고 결과물을 `data_sources/django-5.2-docs`에 저장합니다.
- **all (기본값)**: `crawl`과 `convert`를 순차적으로 실행하여 전체 파이프라인을 완성합니다.

### 지원 옵션 (Options)
- **-c, --concurrency [INT]**: 동시 수집 요청 수를 제한합니다. (기본값: 5)
- **-f, --force**: 이미 로컬에 저장된 HTML이 있더라도 무시하고 강제로 다시 수집합니다. (Resume 기능 비활성화)
- **--cleanup**: 크롤링 완료 후, 이번 세션에서 방문하지 않은 모든 고립된 로컬 파일을 삭제합니다.
- **-v, --version [STR]**: 대상 문서 버전을 지정합니다. (기본값: 5.2)

## 2. 입출력 규격 (I/O Specifications)

### 입력 데이터 (Inputs)
- **Seed URL**: `https://docs.djangoproject.com/en/5.2/`
- **Exclusion Prefix**: `https://docs.djangoproject.com/en/5.2/releases/`

### 출력 데이터 (Outputs)
- **HTML (Temp)**: `crawler/.temp/django-5.2-docs/**/*.html`
- **Markdown (Source)**: `data_sources/django-5.2-docs/**/*.md`

### CLI 출력 (Terminal UX)
- **Progress Bar**: `tqdm`을 사용한 실시간 수집 및 변환 진행률 표시.
- **Status Log**: 현재 작업 중인 URL, 성공/실패 여부, 세션 종료 통계(총 수집/변환 수) 출력.

## 3. 에러 처리 (Error Handling)

- **HTTP 404/500**: `tenacity`를 통해 최대 5회 지수 백오프 재시도를 수행합니다. 재시도 실패 시 로그를 남기고 해당 URL은 건너뜁니다.
- **Parse Error**: HTML 구조가 예상과 달라 본문 추출이 불가능할 경우, 경고 메시지를 출력하고 해당 파일은 변환하지 않습니다.
- **Network Timeout**: 타임아웃 발생 시 재시도 로직을 가동하며, 네트워크 단절 시 전체 작업을 중지하고 현재까지 수집된 상태를 보존(Resume 가능)합니다.
