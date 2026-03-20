import logging
import struct
from typing import Any

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)


class RerankingService:
    """
    Late Interaction (ColBERT 스타일) 리랭킹 서비스.

    사전 저장된 멀티 벡터와 질문 멀티 벡터 간의 MaxSim 연산을 수행하여
    검색 결과의 순위를 재정렬합니다.
    """

    def __init__(self) -> None:
        self.dim = getattr(settings, "LATE_INTERACTION_DIM", 128)
        self.threshold = getattr(settings, "LATE_INTERACTION_THRESHOLD", 0.3)

    def compute_maxsim(self, query_multi_vector: bytes, document_multi_vector: bytes) -> float:
        """
        두 멀티 벡터 간의 MaxSim 점수를 계산합니다.
        """
        # 1. 바이너리 언패킹
        q_tokens, q_vecs = self._unpack_vector(query_multi_vector)
        d_tokens, d_vecs = self._unpack_vector(document_multi_vector)

        if q_tokens == 0 or d_tokens == 0:
            return 0.0

        # 2. MaxSim 연산 (NumPy 가속)
        use_onnx = getattr(settings, "USE_ONNX_EMBEDDING", True)
        if use_onnx:
            # int8 양자화 해제
            q_vecs_f = q_vecs.astype(np.float32) / 127.0
            d_vecs_f = d_vecs.astype(np.float32) / 127.0
        else:
            # float32 원본 사용
            q_vecs_f = q_vecs
            d_vecs_f = d_vecs

        scores = q_vecs_f @ d_vecs_f.T
        max_scores_per_query_token = np.max(scores, axis=1)

        # 3. 정규화 (Mean MaxSim)
        total_maxsim = np.sum(max_scores_per_query_token)
        mean_maxsim = float(total_maxsim / q_tokens)

        return mean_maxsim

    def rerank(
        self, query_multi_vector: bytes, candidates: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        후보군에 대해 리랭킹을 수행합니다.

        Args:
            query_multi_vector: 질문 멀티 벡터
            candidates: 검색 후보 리스트. 각 항목은 'multi_vector_low_dim' 필드를 포함해야 함.

        Returns:
            list: 리랭킹 및 필터링된 결과 리스트
        """
        reranked_results = []

        for cand in candidates:
            doc_multi_vec = cand.get("multi_vector_low_dim")
            if not doc_multi_vec:
                # 데이터 누락 시 기본 점수 유지 (또는 0점 처리)
                cand["rerank_score"] = 0.0
                reranked_results.append(cand)
                continue

            try:
                score = self.compute_maxsim(query_multi_vector, doc_multi_vec)
                # 임계값 필터링 (FR-006)
                if score >= self.threshold:
                    cand["rerank_score"] = score
                    # 최종 similarity 점수를 rerank 점수로 업데이트
                    cand["similarity"] = score
                    # extra_meta에도 저장 (응답 규격 준수)
                    if "extra_meta" not in cand:
                        cand["extra_meta"] = {}
                    cand["extra_meta"]["rerank_score"] = score

                    reranked_results.append(cand)
            except Exception as e:
                logger.error(f"Error computing MaxSim for chunk {cand.get('id')}: {str(e)}")
                # 오류 발생 시 해당 항목 건너뛰거나 하이브리드 점수 유지 (폴백은 호출부에서 처리)
                cand["rerank_score"] = 0.0
                reranked_results.append(cand)

        # 점수 순으로 정렬
        reranked_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return reranked_results

    def _unpack_vector(self, packed_data: bytes) -> tuple[int, np.ndarray]:
        """바이너리 패킹된 데이터를 NumPy 배열로 복원합니다."""
        if not packed_data or len(packed_data) < 2:
            return 0, np.array([], dtype=np.int8)

        # 1. 토큰 수 추출 (첫 2바이트)
        token_count = struct.unpack("<H", packed_data[:2])[0]

        # 2. 벡터 데이터 추출
        use_onnx = getattr(settings, "USE_ONNX_EMBEDDING", True)
        dtype = np.int8 if use_onnx else np.float32
        itemsize = 1 if use_onnx else 4

        expected_size = token_count * self.dim * itemsize
        actual_size = len(packed_data) - 2

        if actual_size < expected_size:
            # 데이터 손상 시 가능한 만큼만 처리하거나 에러 발생
            token_count = actual_size // (self.dim * itemsize)
            expected_size = token_count * self.dim * itemsize

        vector_data = np.frombuffer(packed_data[2 : 2 + expected_size], dtype=dtype).reshape(
            token_count, self.dim
        )

        return token_count, vector_data


def get_reranking_service() -> RerankingService:
    """RerankingService 인스턴스를 반환합니다."""
    return RerankingService()
