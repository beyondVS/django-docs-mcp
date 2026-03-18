from typing import Any

import torch
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer


class RerankingService:
    """
    검색 결과의 정밀도를 향상시키기 위해 Reranker 모델을 실행하는 서비스 클래스.

    BAAI/bge-reranker-base의 ONNX 버전을 사용하여
    질문과 문서 청크 간의 관련성 점수를 정밀하게 재산출합니다.
    """

    _instance: RerankingService | None = None
    _model: ORTModelForSequenceClassification | None = None
    _tokenizer: Any = None

    def __new__(cls) -> RerankingService:
        """
        RerankingService의 싱글톤 인스턴스를 생성하거나 반환합니다.
        """
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            # BGE Reranker Base INT8 양자화 모델 활용 (CPU 최적화의 정점)
            model_id = "keisuke-miyako/bge-reranker-base-onnx-int8"

            # 1. 토크나이저 로드
            cls._tokenizer = AutoTokenizer.from_pretrained(model_id)

            # 2. ONNX Reranker 모델 로드
            # 해당 레포지토리의 양자화된 모델 파일명을 직접 지정합니다.
            cls._model = ORTModelForSequenceClassification.from_pretrained(
                model_id, provider="CPUExecutionProvider", file_name="model_quantized.onnx"
            )
        return cls._instance

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """
        사용자 질의와 문서 리스트에 대해 관련성 점수를 산출합니다.

        Args:
            query (str): 사용자 질문.
            documents (list[str]): 재정렬할 문서 청크 본문 리스트.

        Returns:
            list[float]: 각 문서에 대한 유사도 점수 리스트 (Sigmoid 적용, 0~1).
        """
        tokenizer = self._tokenizer
        model = self._model

        if model is None or tokenizer is None:
            raise RuntimeError("Reranker 모델 또는 토크나이저가 로드되지 않았습니다.")

        if not documents:
            return []

        # 1. 질문-문서 쌍 생성
        pairs = [[query, doc] for doc in documents]

        # 2. 토큰화 (Cross-Encoder 입력 형식)
        inputs = tokenizer(
            pairs, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )

        # 3. 추론 실행
        with torch.no_grad():
            outputs = model(**inputs)

        # 4. 점수 추출 및 정규화
        # BGE Reranker는 단일 로짓(Logit)을 반환함
        logits = outputs.logits.view(-1).float()
        scores = torch.sigmoid(logits)

        return [float(s) for s in scores.tolist()]


def get_reranking_service() -> RerankingService:
    """
    RerankingService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        RerankingService: 초기화된 리랭킹 서비스.
    """
    return RerankingService()
