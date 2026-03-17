# 구현 계획서: 하이브리드 검색 및 Rerank 전략 (004-hybrid-search-rerank)

**브랜치**: `004-hybrid-search-rerank` | **날짜**: 2026-03-18 | **명세서**: [spec.md](./spec.md)
**입력**: `/specs/004-hybrid-search-rerank/spec.md`의 기능 명세서

## 요약
PostgreSQL의 `pg_search` 확장을 도입하여 BM25 키워드 검색을 구현하고, 기존 벡터 검색과 RRF(Reciprocal Rank Fusion) 방식으로 통합합니다. 추출된 상위 20개 후보를 대상으로 ONNX Runtime 기반의 양자화된 Reranker 모델을 실행하여 검색 결과의 정밀도를 극대화합니다.

## 기술적 문맥 (Technical Context)

**언어/버전**: Python 3.14
**주요 의존성**: `optimum[onnxruntime]~=1.24.0`, `transformers~=4.48.0`, `pg_search` (ParadeDB), `pgvector`
**저장소**: PostgreSQL (pgvector/pgvector:pg18 베이스 커스텀 이미지)
**테스트**: `pytest` (신규 평가 데이터셋 포함)
**대상 플랫폼**: Linux 서버 (Docker)
**제약 사항**: CPU 환경에서의 메모리 최적화 필수 (INT8 양자화 사용)

## 헌법 준수 확인 (Constitution Check)

- [x] **RAG 정확성 확인**: 하이브리드 검색을 통해 키워드 매칭 정밀도를 높였는가? (BM25 도입)
- [x] **아키텍처 분리 확인**: 검색 로직이 `django_server/services/search.py`에 응집되었는가?
- [x] **데이터 무결성 확인**: Rerank 점수가 메타데이터와 함께 일관되게 전달되는가?
- [x] **컨테이너 환경 확인**: `pg_search`를 위한 Docker 이미지 변경이 계획에 포함되었는가?

## 프로젝트 구조 (수정 및 추가 대상)

```text
django_server/
├── src/
│   └── documents/
│       └── services/
│           ├── search.py         # 하이브리드 검색 및 Rerank 로직 통합
│           └── reranking.py      # ONNX Reranker 서비스 (신규)
├── scripts/
│   └── evaluate_search.py        # 검색 품질 평가 스크립트 (신규)
└── tests/
    └── test_search_quality.py    # 품질 지표(MRR) 검증 테스트
```

## 실행 계획 (Execution Plan)

### 0단계: 인프라 및 기반 구축
1. **DB Dockerfile 작성**: `pgvector/pgvector:pg18`을 베이스로 하고 `pg_search` 패키지 저장소 설정 및 확장을 설치하는 `Dockerfile` 생성.
2. **docker-compose 수정**: `image` 대신 `build` 설정을 사용하도록 업데이트하여 커스텀 이미지를 적용.
3. **BM25 인덱스 생성**: 마이그레이션을 통해 `documents_chunk` 테이블에 BM25 인덱스 추가.
4. **의존성 추가**: `django_server` 프로젝트에 `uv add optimum[onnxruntime] transformers` 실행 후 `pyproject.toml` 버전을 `~=` 형식으로 조정.

### 1단계: 하이브리드 검색 구현 (Retrieval)
1. **SearchService 리팩토링**: 벡터 검색과 BM25 검색을 병렬로 수행하는 SQL 작성.
2. **RRF 통합**: SQL 레벨에서 두 순위를 결합하는 `WITH` 절 쿼리 구현.
3. **성능 확인**: 하이브리드 검색만으로의 지연 시간 측정.

### 2단계: Rerank 프로세서 구현 (Refinement)
1. **RerankingService**: ONNX 모델 로딩 및 Sigmoid 점수 산출 로직 구현.
2. **파이프라인 연결**: `HybridSearch` -> `Rerank` 연쇄 호출.
3. **메모리 최적화**: 로딩 시 `INT8` 양자화 모델 경로 지정 및 세션 옵션 튜닝.

### 3단계: 평가 및 검증
1. **골든 데이터셋 생성**: 주요 질문 50개에 대한 정답셋 구축.
2. **평가 스크립트 실행**: 기존 벡터 검색 vs 하이브리드+Rerank 지표 비교.
3. **성공 기준 달성 확인**: SC-001 ~ SC-004 검증.

## 복잡성 추적

| 위반 사항 | 필요한 이유 | 더 단순한 대안을 거부한 이유 |
|-----------|------------|---------------------------|
| pg_search 도입 | 기본 FTS의 낮은 정확도 | 단순 가중치 방식은 기술 문서의 BM25 요구를 충족 못함 |
| ONNX Runtime 사용 | CPU 환경에서의 실시간성 확보 | 기본 PyTorch는 Reranker 실행 시 지연 시간이 목표 초과 우려 |
