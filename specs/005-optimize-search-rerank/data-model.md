# 데이터 모델 정의: 고성능 하이브리드 검색 및 Late Interaction 리랭커

## 1. DocumentChunk (기존 모델 확장)

- **테이블**: `documents_chunk`
- **필드 추가**:
    - `multi_vector_low_dim`: `BinaryField` (또는 `bytea` 직접 매핑).
        - **설명**: 128차원으로 축소되고 int8 양자화된 멀티 벡터 데이터.
        - **포맷**: `[Token Count (2바이트 소엔디언 정수)][벡터 데이터 (N * 128바이트)]`.
- **기존 필드 유지**: `id`, `content`, `embedding`, `section_id` 등.

## 2. Ingestion 파이프라인 흐름

1. 문서 로드 및 청킹 (기존 로직).
2. `gpahal/bge-m3-onnx-int8` 모델 추론.
3. 결과물 처리:
    - `pooled_output` -> `embedding` 필드 저장 (1,024차원).
    - `last_hidden_state` -> 128차원 슬라이싱 -> int8 캐스팅 -> 바이너리 패킹 -> `multi_vector_low_dim` 저장.

## 3. 검색 서비스 엔티티

- **SearchQuery**: 사용자 입력 텍스트 및 필터 조건.
- **RerankCandidate**: 1차 검색 결과 중 리랭킹 대상이 되는 청크 및 관련 메타데이터.
