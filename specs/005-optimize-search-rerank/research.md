# 조사 보고서: 고성능 하이브리드 검색 및 Late Interaction 리랭커 도입

## 1. 모델 연산 및 멀티벡터 추출
- **결정(Decision)**: `gpahal/bge-m3-onnx-int8` 모델을 `optimum` 라이브러리로 로드하여 `last_hidden_state`를 추출함.
- **근거(Rationale)**: CPU 환경에서 최고의 성능을 내는 INT8 양자화 모델이며, 단일 추론으로 Dense와 Multi-vector를 모두 얻을 수 있음.
- **고려된 대안(Alternatives considered)**: FP32 모델 사용 (지연 시간 과다로 거부), 실시간 문서 임베딩 (성능 목표 미달로 거부).

## 2. 하이브리드 검색 구현 (ParadeDB)
- **결정(Decision)**: `django-paradedb`의 `BM25Index`와 `ParadeDBManager`를 활용하여 RRF 검색을 구현함.
- **근거(Rationale)**: 기존 Raw SQL 방식보다 가독성이 높고 Django ORM 표준을 준수하며, ParadeDB 최신 최적화 기능을 자동 활용함.
- **고려된 대안(Alternatives considered)**: 기존 Raw SQL 유지 (유지보수성 저하로 거부).

## 3. 멀티벡터 압축 및 저장 전략
- **결정(Decision)**: 1,024차원 -> 128차원 Slicing + int8 Scalar Quantization 적용 후 `[TokenCount(2B)][VectorData]` 포맷으로 `bytea` 필드에 저장.
- **근거(Rationale)**: 저장 공간을 32배 압축하면서도 Late Interaction 특유의 정밀도를 유지하며, 가변 길이 대응이 가능함.
- **고려된 대안(Alternatives considered)**: float32 원본 저장 (용량 폭증으로 거부), 디스크 파일 저장 (관리 복잡성 및 트랜잭션 불일치 위험으로 거부).

## 4. 리랭킹 연산 (MaxSim)
- **결정(Decision)**: NumPy 기반의 벡터화된 MaxSim 연산을 수행하고 `Mean MaxSim` 정규화를 적용함.
- **근거(Rationale)**: CPU 환경에서 병렬 연산 효율이 가장 좋으며, 쿼리 길이에 무관한 일관된 임계값(0.3) 적용이 가능함.
