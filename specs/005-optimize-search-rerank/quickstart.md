# 퀵스타트 가이드: 고성능 검색 엔진 활용 (005-optimize-search-rerank)

이 가이드는 새롭게 도입된 고성능 하이브리드 검색 및 Late Interaction 리랭커를 설정하고 사용하는 방법을 설명합니다.

## 1. 환경 설정

`uv`를 통해 의존성을 최신화합니다.
```bash
uv sync --all-packages
```

## 2. 데이터 마이그레이션 및 재인덱싱

1. 모델 필드 추가를 위한 마이그레이션을 실행합니다.
```bash
cd django_server
uv run python src/manage.py makemigrations
uv run python src/manage.py migrate
```

2. 기존 문서를 새로운 `int8` 모델 및 멀티 벡터 포맷으로 재인덱싱합니다.
```bash
# Ingestion 명령 실행 (기존 데이터 덮어쓰기)
uv run python src/manage.py ingest_docs --reindex
```

## 3. 검색 테스트

1. **Django Shell에서 테스트**:
```python
from documents.services.search import get_search_service
import asyncio

async def test():
    service = get_search_service()
    results = await service.search("django filter querysets", limit=5)
    for res in results:
        print(f"[{res['similarity']}] {res['content'][:50]}...")

asyncio.run(test())
```

2. **Playground UI**:
`http://127.0.0.1:8000/playground/` 접속 후 검색 속도와 리랭킹 점수를 확인합니다.

## 4. 모니터링 포인트
- 검색 응답 속도가 1,000ms 이하인지 확인합니다.
- `extra_meta`에 `rerank_score`가 0.0~1.0 사이로 포함되는지 확인합니다.
