from typing import Any

import torch
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer


class EmbeddingService:
    """
    텍스트 데이터를 벡터 임베딩으로 변환하는 싱글톤 서비스 클래스.

    optimum 및 onnxruntime을 사용하여 BAAI/bge-m3 모델의 ONNX 버전을 실행합니다.
    CPU 환경에서의 메모리 효율과 추론 속도를 최적화합니다.
    """

    _instance: EmbeddingService | None = None
    _model: ORTModelForFeatureExtraction | None = None
    _tokenizer: Any = None

    def __new__(cls) -> EmbeddingService:
        """
        EmbeddingService의 싱글톤 인스턴스를 생성하거나 반환합니다.

        Returns:
            EmbeddingService: 싱글톤 서비스 인스턴스.
        """
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            model_name = "BAAI/bge-m3"

            # 1. 토크나이저 로드 (Hugging Face 자동 다운로드 활용)
            cls._tokenizer = AutoTokenizer.from_pretrained(model_name)

            # 2. ONNX 모델 로드 (Hugging Face 리포지토리의 onnx/ 서브폴더에서 자동 로드)
            # 프로젝트 헌법 및 기술 표준에 따라 CPU 환경 최적화를 위해 ONNX Runtime 사용
            cls._model = ORTModelForFeatureExtraction.from_pretrained(
                model_name, subfolder="onnx", provider="CPUExecutionProvider"
            )
        return cls._instance

    def embed_text(self, text: str) -> list[float]:
        """
        단일 텍스트 문자열을 1024차원 벡터로 변환합니다.

        Args:
            text (str): 임베딩할 텍스트 문자열.

        Returns:
            list[float]: 생성된 벡터 임베딩 리스트 (L2 정규화 포함).
        """
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        여러 텍스트 문자열 리스트를 각각 벡터로 변환합니다.

        Args:
            texts (list[str]): 임베딩할 텍스트 문자열 리스트.

        Returns:
            list[list[float]]: 생성된 벡터 임베딩 리스트의 리스트.
        """
        tokenizer = self._tokenizer
        model = self._model

        if model is None or tokenizer is None:
            raise RuntimeError("모델 또는 토크나이저가 로드되지 않았습니다.")

        # 1. 토큰화
        encoded_input = tokenizer(
            texts, padding=True, truncation=True, max_length=8192, return_tensors="pt"
        )

        # 2. ONNX 추론
        with torch.no_grad():
            model_output = model(**encoded_input)

        # 3. Pooling (BGE-M3는 일반적으로 [CLS] 토큰 활용)
        # last_hidden_state의 0번 인덱스 (Batch, Sequence, Hidden) -> (Batch, Hidden)
        sentence_embeddings = model_output.last_hidden_state[:, 0, :]

        # 4. L2 Normalization
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

        return [[float(x) for x in e] for e in sentence_embeddings.tolist()]


def get_embedding_service() -> EmbeddingService:
    """
    EmbeddingService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        EmbeddingService: 초기화된 임베딩 서비스.
    """
    return EmbeddingService()
