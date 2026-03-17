# 데이터 모델 정의: 하이브리드 검색 및 Rerank (004-hybrid-search-rerank)

## 엔티티 정의 (Entities)

### 1. HybridSearchEngine (Logic)
- **역할**: BM25 검색과 벡터 검색을 조합하여 후보군을 추출하는 핵심 엔진.
- **주요 속성**:
    - `bm25_weight`: BM25 순위 기여도 (RRF 상수 k와 연동).
    - `vector_weight`: 벡터 순위 기여도.
    - `top_k`: 1차 검색에서 추출할 후보 수 (기본 20개).

### 2. RerankProcessor (Service)
- **역할**: 1차 검색 결과를 ONNX 기반 Reranker 모델로 재정렬.
- **주요 속성**:
    - `model_name`: `tss-deposium/bge-reranker-v2-m3-onnx-int8`.
    - `threshold`: 최종 반환할 유사도 임계값.

### 3. SearchEvaluationPair (Evaluation)
- **역할**: 검색 품질 측정을 위한 질문-정답 쌍.
- **필드**:
    - `query`: 사용자 질문 (str).
    - `expected_chunk_ids`: 정답 청크 ID 리스트 (list[UUID]).
    - `category`: 질문 카테고리 (Ref, Tutorial 등).

## 데이터베이스 스키마 보완

### BM25 Index (ParadeDB)
- **대상 테이블**: `documents_chunk`
- **대상 컬럼**: `content`
- **인덱스 유형**: `USING bm25`
- **설정**: `WITH (key_field = 'id')`

## 관계 (Relationships)
- `Document` --(1:N)--> `Section` --(1:N)--> `Chunk`.
- `Chunk` --(인덱싱)--> `BM25 Index`.
- `SearchEvaluationPair` --(검증)--> `Chunk`.
