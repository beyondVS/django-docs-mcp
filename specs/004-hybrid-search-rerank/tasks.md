# 작업 목록 (Tasks): 하이브리드 검색 및 Rerank 전략을 통한 검색 품질 개선

**기능**: `004-hybrid-search-rerank` | **날짜**: 2026-03-18
**참고**: 이 파일은 구현 상태를 추적하기 위한 체크리스트입니다. 각 작업은 독립적으로 실행 및 테스트 가능해야 합니다.

## 요약
- **총 작업 수**: 18개
- **사용자 스토리별 작업**: US1(5개), US2(5개), US3(3개)
- **병렬 가능 작업**: 6개 ([P] 표시)
- **MVP 범위**: 3단계 (US1: 하이브리드 검색 엔진 구축)

## 구현 단계 (Phases)

### 1단계: 설정 및 인프라 구축 (Setup)
- [ ] T001 `django_server/db.Dockerfile`을 생성하여 `pgvector/pgvector:pg18` 기반에 `pg_search` 확장 설치 로직 구현
- [ ] T002 `docker-compose.yml`의 `db` 서비스를 커스텀 Dockerfile 빌드 방식으로 업데이트
- [ ] T003 `django_server` 디렉토리에서 `uv add "optimum[onnxruntime]~=1.24.0" "transformers~=4.48.0"` 실행 및 `pyproject.toml` 버전 기법(`~=`) 조정
- [ ] T004 [P] `django_server/src/documents/migrations/`에 `pg_search` 확장을 활성화하고 `documents_chunk` 테이블에 BM25 인덱스를 생성하는 `RunSQL` 마이그레이션 작성

### 2단계: 기초 로직 리팩토링 (Foundational)
- [ ] T005 `django_server/src/documents/services/embedding.py`를 `SentenceTransformers` 대신 `optimum` 및 `onnxruntime` 기반의 `bge-m3` 임베딩 생성 로직으로 전환
- [ ] T006 `django_server/src/documents/services/search.py`의 기존 `vector_search` 로직을 하이브리드 검색 확장이 용이하도록 인터페이스 리팩토링

### 3단계: [US1] 하이브리드 검색 엔진 구축 (P1)
- [ ] T007 [US1] `django_server/src/documents/services/search.py`에 `pg_search`를 활용한 BM25 검색 메서드 구현
- [ ] T008 [US1] `django_server/src/documents/services/search.py`에 SQL `WITH` 절 및 `FULL OUTER JOIN`을 사용한 RRF(Reciprocal Rank Fusion) 통합 쿼리 구현
- [ ] T009 [P] [US1] `django_server/tests/test_search.py`에 하이브리드 검색 결과의 키워드 매칭 정확도를 검증하는 단위 테스트 추가
- [ ] T010 [US1] `django_server/src/documents/services/search.py`의 `hybrid_search` 결과를 기존 `search_django_knowledge` 규격에 맞게 변환하는 래퍼 작성

### 4단계: [US2] Rerank 프로세서 구현 (P1)
- [ ] T011 [US2] `django_server/src/documents/services/reranking.py` 신설 및 `optimum` 기반의 `bge-reranker-v2-m3-onnx-int8` 모델 로드 로직 구현
- [ ] T012 [US2] `RerankingService.rerank` 메서드에서 [질문, 청크] 쌍에 대한 유사도 점수 산출 및 Sigmoid 적용 로직 구현
- [ ] T013 [US2] `django_server/src/documents/services/search.py`에서 하이브리드 검색 결과 상위 20개를 Reranker에 전달하고 최종 순위를 정렬하는 파이프라인 연결
- [ ] T014 [P] [US2] `django_server/tests/test_search.py`에 Rerank 후 검색 결과의 정밀도 향상을 검증하는 테스트 케이스 추가

### 5단계: [US3] 성능 최적화 및 품질 평가 (P2)
- [ ] T015 [US3] `django_server/scripts/evaluate_search.py`를 생성하여 주요 질문 50개 이상의 골든 데이터셋 구축 로직 구현
- [ ] T016 [US3] `evaluate_search.py`에서 MRR 및 Hit Rate(Top-3) 지표를 계산하고 기존 방식과 비교 분석하는 기능 구현
- [ ] T017 [P] [US3] 전체 검색 프로세스(Retrieval + Rerank)의 응답 시간을 측정하고 1.5초 이내(p95) 목표 달성 여부 검증

### 6단계: 다듬기 및 통합 (Polish)
- [ ] T018 `django_server/src/documents/templates/playground/` 웹 UI에서 하이브리드/Rerank 점수를 시각적으로 확인할 수 있도록 업데이트

## 의존성 및 실행 순서
1. **인프라 (T001-T004)**: DB 확장이 설치되어야 모든 검색 로직 테스트가 가능함.
2. **임베딩 전환 (T005)**: 모든 검색의 기초인 임베딩 생성 방식이 먼저 ONNX로 전환되어야 함.
3. **하이브리드 (T007-T010)**: 1차 검색 후보군이 추출되어야 Rerank 단계로 진행 가능함.
4. **Rerank (T011-T013)**: 1차 검색 결과와 모델 로더가 준비되어야 함.
5. **평가 (T015-T017)**: 기능 구현 완료 후 대량의 질의를 통해 최종 품질을 확정함.

## 구현 전략 (MVP First)
- **우선순위**: US1 > US2 > US3.
- **병렬 실행**: 마이그레이션(T004), 테스트 코드(T009, T014), 성능 측정(T017)은 로직 구현과 병렬로 진행 가능.
- **검증**: `evaluate_search.py`를 통해 실제 검색 품질이 수치적으로 개선되었음을 증명한 후 완료 처리.
