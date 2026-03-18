# 임베딩 및 리트리벌 전략서 (Retrieval & Ranking Spec)

문서를 벡터화하여 저장하고, 최적의 관련 문서를 검색 및 재순위화(Reranking)하기 위한 전략을 정의합니다.

## 1. 모델 및 런타임 (Models & Runtime)

*   **Embedding Model:** BAAI/bge-m3
    *   **특징:** 다국어 특화, 1024 차원 벡터 생성, 8,192 토큰 컨텍스트 지원.
    *   **추론 가속:** **ONNX Runtime** 기반의 고속 추론을 활용하여 CPU 환경에서의 지연 시간을 최소화합니다.
*   **Reranker Model:** BAAI/bge-reranker-base (ONNX INT8 양자화)
    *   **특징:** 질문-문서 쌍의 의미적 연관성을 정밀 점수화(0~1).
    *   **최적화:** **INT8 양자화된 ONNX 모델**을 사용하여 메모리 사용량을 절감하고 실행 속도를 높였습니다.

## 2. 청킹 전략 (Chunking Strategy)

의미론적 구조를 보존하는 2단계 청킹 파이프라인을 수행합니다.

*   **Phase 1: MarkdownHeaderTextSplitter**: 헤더(H1~H3) 기반 논리 섹션 분할.
*   **Phase 2: MarkdownTextSplitter**: 코드 블록(```) 보호를 최우선으로 하며 1,500 ~ 2,500자 단위로 재분할.
*   **Overlap**: 청크 간 문맥 유지를 위해 약 200자 중첩 구간 설정.

## 3. 리트리벌 및 순위화 전략 (Retrieval & Ranking)

단순 벡터 검색의 한계를 극복하기 위해 **하이브리드 리트리벌 + Reranking** 3단계 파이프라인을 적용합니다.

### 3.1 하이브리드 리트리벌 (Hybrid Retrieval)
*   **Vector Search**: `pgvector` 기반 코사인 유사도 검색 (의미적 유사성 포착).
*   **Keyword Search**: `pg_search` (BM25) 기반 키워드 매칭 (고유 명사, API 명칭 등 정확도 확보).

### 3.2 RRF 통합 (Reciprocal Rank Fusion)
*   벡터 검색 결과와 키워드 검색 결과의 순위를 아래 공식을 통해 통합하여 상위 10개 후보를 도출합니다.
    *   `Score = Σ (1 / (rank + k))` (k=60 기본값)
*   이 과정은 PostgreSQL 내부에서 SQL `WITH` 절을 통해 효율적으로 수행됩니다.

### 3.3 ONNX Reranking (Refinement)
*   **최종 검증**: RRF로 추출된 상위 10개 청크를 Reranker 모델에 입력합니다.
*   **점수 산출**: 질문과 각 청크 간의 Sigmoid 점수를 계산하여 최종 순위를 정렬합니다.
*   **임계값 필터링**: 관련성이 현저히 낮은 청크(예: 점수 0.1 이하)는 결과에서 제외하여 환각 가능성을 줄입니다.

## 4. 품질 평가 및 관리 (Quality Assurance)

*   **평가 지표**: MRR (Mean Reciprocal Rank), Hit Rate @5 지표를 기준으로 검색 엔진의 성능을 주기적으로 측정합니다.
*   **골든 데이터셋**: 기술 문서의 핵심 질문과 정답 문서 ID를 매칭한 50개 이상의 고품질 평가셋을 통해 로직 변경 시 성능 퇴보 여부를 확인합니다.
*   **Playground 피드백**: 시각화된 검색 점수 분석을 통해 특정 키워드에 대한 BM25 가중치 등을 미세 조정합니다.
