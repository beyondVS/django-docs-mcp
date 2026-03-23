# Quickstart

이 문서는 새롭게 작성된 Django 5.2 문서 크롤러를 로컬 환경에서 실행하고 테스트하는 방법을 안내합니다.

## 전제 조건

- 파이썬 3.13 이상
- `uv` 패키지 관리자
- Git 설치 (문서 저장소 다운로드 용도)

## 환경 설정

1. 저장소 루트에서 의존성을 동기화합니다.
   ```bash
   uv sync --all-packages
   ```

## 크롤러 실행

`crawler` 디렉터리로 이동하여 5.2 문서 전용 크롤링 스크립트를 실행합니다.

```bash
cd crawler
uv run python django52_crawler.py
```

### 실행 흐름 요약

1. 크롤러가 `crawler/.temp/django_src` 폴더에 `https://github.com/django/django` 저장소의 `stable/5.2.x` 브랜치 중 `docs` 폴더만 Sparse Checkout으로 다운로드합니다.
2. `.temp/django_src/docs` 하위의 모든 `.txt` (RST) 파일을 스캔합니다.
3. 각 문서를 `docutils`를 이용해 파싱하고 Markdown으로 변환합니다.
4. 원본 파일의 디렉터리 구조를 본따 웹 URL 형태(`https://docs.djangoproject.com/en/5.2/...`)로 변환 후 메타데이터에 삽입합니다.
5. 최종 Markdown 문서를 루트 디렉터리의 `data_sources/django-5.2-docs/` 경로에 저장합니다.

## 결과물 확인

스크립트 완료 후 다음 경로에 변환된 문서들이 위치하는지 확인합니다.

```bash
ls -l ../data_sources/django-5.2-docs/
```

생성된 `.md` 파일을 열어 상단 YAML Front Matter에 올바른 `source_url`과 본문이 포함되어 있는지 점검합니다.
