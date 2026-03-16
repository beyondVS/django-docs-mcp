from typing import Any

import torch
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    텍스트 데이터를 벡터 임베딩으로 변환하는 싱글톤 서비스 클래스.

    BAAI/bge-m3 모델을 사용하여 1024차원의 밀집 벡터를 생성합니다.
    GPU 사용이 가능할 경우 자동으로 CUDA 가속을 활용합니다.
    """

    _instance: EmbeddingService | None = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> EmbeddingService:
        """
        EmbeddingService의 싱글톤 인스턴스를 생성하거나 반환합니다.

        Returns:
            EmbeddingService: 싱글톤 서비스 인스턴스.
        """
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            # 모델은 한 번만 로드함
            model_name = "BAAI/bge-m3"
            # GPU 사용 가능 여부에 따라 디바이스 설정
            device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._model = SentenceTransformer(model_name, device=device)
        return cls._instance

    def embed_text(self, text: str) -> list[float]:
        """
        단일 텍스트 문자열을 1024차원 벡터로 변환합니다.

        Args:
            text (str): 임베딩할 텍스트 문자열.

        Returns:
            list[float]: 생성된 벡터 임베딩 리스트 (L2 정규화 포함).
        """
        model = self._get_model()

        # 정규화: bge-m3 모델은 일반적으로 정규화 시 성능이 향상됨
        embedding: Any = model.encode(text, normalize_embeddings=True)
        return [float(x) for x in embedding.tolist()]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        여러 텍스트 문자열 리스트를 각각 벡터로 변환합니다.

        Args:
            texts (list[str]): 임베딩할 텍스트 문자열 리스트.

        Returns:
            list[list[float]]: 생성된 벡터 임베딩 리스트의 리스트.
        """
        model = self._get_model()

        embeddings: Any = model.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in e.tolist()] for e in embeddings]

    def _get_model(self) -> SentenceTransformer:
        """
        로드된 모델을 반환하거나, 로드되지 않았을 경우 에러를 발생시킵니다.
        """
        if self._model is not None:
            return self._model

        # 싱글톤 구조상 발생하기 어렵지만 mypy 대응을 위해 추가
        model_name = "BAAI/bge-m3"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(model_name, device=device)
        self.__class__._model = model

        return model


def get_embedding_service() -> EmbeddingService:
    """
    EmbeddingService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        EmbeddingService: 초기화된 임베딩 서비스.
    """
    return EmbeddingService()
