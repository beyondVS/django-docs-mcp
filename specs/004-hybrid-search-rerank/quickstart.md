# 퀵스타트 가이드: 하이브리드 검색 및 Rerank (004-hybrid-search-rerank)

## 개요
이 가이드는 `pg_search` 확장을 활용한 하이브리드 검색과 ONNX 기반 Reranker를 로컬 개발 환경에서 설정하고 테스트하는 방법을 설명합니다.

## 개발 환경 설정 (Setup)

### 1. ParadeDB (pg_search) 활성화
로컬 PostgreSQL 컨테이너에 `pg_search` 확장이 설치되어 있어야 합니다.
```sql
CREATE EXTENSION IF NOT EXISTS pg_search;
```

### 2. 의존성 설치
프로젝트 루트 또는 `django_server` 디렉토리에서 패키지를 추가합니다.
```bash
cd django_server
uv add optimum[onnxruntime] transformers
```
> 💡 **Tip**: 설치 후 `pyproject.toml`을 열어 자동으로 생성된 버전 표기를 `~= x.y.z` 형식으로 수정하여 API 안정성을 확보하십시오.

### 3. 모델 다운로드
검색 엔진 구동 시 자동으로 다운로드되거나, 명시적으로 미리 다운로드할 수 있습니다.
- Embedding: `BAAI/bge-m3` (ONNX 가중치 포함)
- Reranker: `keisuke-miyako/bge-reranker-base-onnx-int8`

## 검색 테스트 (Testing)

### 1. 하이브리드 검색 품질 확인
Django 쉘이나 Playground UI에서 다음 기능을 테스트합니다.
- **키워드 일치**: "filter", "aggregate" 등 특정 용어 검색 시 상위 노출 여부.
- **의도 파악**: "how to filter queryset"과 같은 문장 검색 시 Rerank 후 결과 개선 여부.

### 2. 성능 측정
성공 기준(SC-003)인 1.5초 이내 응답 여부를 확인합니다.
```python
# 예시: 검색 시간 측정
import time
from documents.services.search import get_search_service

service = get_search_service()
start = time.time()
results = service.hybrid_search_with_rerank("QuerySet filter")
print(f"Search time: {time.time() - start:.2f}s")
```

## 주요 체크포인트
- `relevance_score`가 Reranker 모델의 결과값(Sigmoid 적용)으로 반환되는지 확인하십시오.
- `extra_meta`에 `rrf_score`와 `rerank_score`가 포함되어 있는지 확인하십시오.
