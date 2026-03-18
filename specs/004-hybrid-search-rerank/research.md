# 조사 보고서: 하이브리드 검색 및 Rerank 전략 (004-hybrid-search-rerank)

## 결정 사항 (Decisions)

### 1. BM25 및 하이브리드 통합 전략
- **선택**: PostgreSQL `pg_search` (ParadeDB) 확장 + SQL 기반 RRF 통합.
- **근거**:
    - `pg_search`는 BM25 알고리즘을 DB 내부에 Rust로 구현하여 기존 FTS보다 정밀도가 높음.
    - SQL 기반 RRF 통합은 벡터 검색(`pgvector`)과 키워드 검색 결과를 애플리케이션 계층으로 가져오지 않고 DB 내에서 순위를 융합하여 반환하므로 성능이 가장 우수함.
- **구현 방식**: `WITH` 절을 사용한 1차 검색(Rank 산출) 후 `FULL OUTER JOIN`을 통한 점수 합산. 이때 RRF 상수 `k=60`(업계 표준)을 적용하여 정밀도와 재현율의 균형을 맞춤.

### 2. Reranker 및 최적화 전략
- **선택**: `keisuke-miyako/bge-reranker-base-onnx-int8` + `onnxruntime` + 비동기 처리(`sync_to_async`).
- **근거**:
    - `INT8` 양자화된 Base 모델(~110M 파라미터)은 CPU 환경에서 v2-m3 대비 추론 속도가 압도적으로 빠르며(0.5초 이내), 메모리 점유율을 대폭 절감함.
    - 리랭커의 컨텍스트 한계(512 토큰)에 맞춰 문서 Chunk Size를 기존 2500자에서 1500자로 하향 조정하여, 리랭킹 과정에서의 정보 누락(Truncation)을 방지함.
    - 리랭커의 무거운 연산이 장고 이벤트 루프를 블로킹하지 않도록 `sync_to_async`로 래핑함.

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
    - **답변**: `paradedb/paradedb:latest-pg18` 공식 이미지를 사용함. 이 이미지는 `pgvector`, `pg_search`, `pg_vectorscale`을 모두 기본 포함하고 있어 별도의 빌드 과정 없이 즉시 통합 검색 환경 구축이 가능함.

- [x] **질문**: Rerank 대상인 '상위 20개'가 충분한가?
    - **답변**: 하이브리드 검색의 재현율(Recall)이 높으므로 20개면 충분하며, 필요 시 환경 변수로 조정 가능하도록 설계함.

### 4. 검색 정밀도 향상을 위한 다중 컬럼 인덱싱
- **결정**: `pg_search` 인덱스 생성 시 `Chunk.content` 뿐만 아니라 상위 `Section.title` 정보를 가상 컬럼으로 결합하여 인덱싱한다.
- **근거**: 헌법의 '데이터 계층화' 원칙에 따라 본문만으로는 부족한 문맥 정보를 섹션 제목을 통해 보완하여 BM25 검색의 정확도를 극대화하기 위함이다.
