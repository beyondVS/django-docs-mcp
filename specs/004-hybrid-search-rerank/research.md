# 조사 보고서: 하이브리드 검색 및 Rerank 전략 (004-hybrid-search-rerank)

## 결정 사항 (Decisions)

### 1. BM25 및 하이브리드 통합 전략
- **선택**: PostgreSQL `pg_search` (ParadeDB) 확장 + SQL 기반 RRF 통합.
- **근거**:
    - `pg_search`는 BM25 알고리즘을 DB 내부에 Rust로 구현하여 기존 FTS보다 정밀도가 높음.
    - SQL 기반 RRF 통합은 벡터 검색(`pgvector`)과 키워드 검색 결과를 애플리케이션 계층으로 가져오지 않고 DB 내에서 순위를 융합하여 반환하므로 성능이 가장 우수함.
- **구현 방식**: `WITH` 절을 사용한 1차 검색(Rank 산출) 후 `FULL OUTER JOIN`을 통한 점수 합산.

### 2. Reranker 및 최적화 전략
- **선택**: `tss-deposium/bge-reranker-v2-m3-onnx-int8` + `onnxruntime`.
- **근거**:
    - `INT8` 양자화 모델은 CPU 환경에서 메모리 점유율을 70% 이상 절감(약 500~700MB)하면서도 정확도 손실이 거의 없음.
    - `ONNX Runtime`은 멀티코어 CPU를 효율적으로 활용하여 상위 20개 청크에 대해 500ms 이내의 추론 속도를 보장함.

### 3. 임베딩 모델 실행 방식
- **선택**: `bge-m3` 역시 `onnxruntime` 기반으로 전환.
- **근거**: 임베딩과 Reranker가 동일한 `onnxruntime` 라이브러리를 공유함으로써 메모리 관리 일관성을 확보하고, 전체 검색 서버의 상주 메모리를 최적화함.

## 고려된 대안 (Alternatives Considered)

### 대안 1: Python 레벨 RRF 통합
- **평가**: 구현은 단순하지만, 정확한 융합을 위해 DB에서 대량의 데이터를 매번 가져와야 하므로 네트워크 지연 및 직렬화 비용이 발생함.
- **결정**: 거부됨 (성능 우선순위).

### 대안 2: 외부 Rerank API (Cohere 등)
- **평가**: 서버 자원은 아낄 수 있으나, 네트워크 지연과 호출 비용이 발생하며 로컬 문서 데이터가 외부로 유출됨.
- **결정**: 거부됨 (보안 및 비용 효율성).

## 미해결 사항 (Open Questions / Needs Clarification)

- [x] **질문**: `pg_search` 확장이 현재 Docker 환경(Postgres)에서 즉시 사용 가능한가?
    - **답변**: `pgvector/pgvector:pg18` 공식 이미지를 베이스로 하여 `pg_search`(ParadeDB)를 추가 설치하는 커스텀 `Dockerfile`을 생성함. 이를 통해 `pgvector`와 `pg_search`를 동시에 지원하며 향후 확장성을 보장함.

- [x] **질문**: Rerank 대상인 '상위 20개'가 충분한가?
    - **답변**: 하이브리드 검색의 재현율(Recall)이 높으므로 20개면 충분하며, 필요 시 환경 변수로 조정 가능하도록 설계함.
