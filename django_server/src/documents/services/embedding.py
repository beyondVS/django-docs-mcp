from typing import Any

import torch
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer


class EmbeddingService:
    """
    텍스트 데이터를 벡터 임베딩으로 변환하는 싱글톤 서비스 클래스.

    optimum 및 onnxruntime을 사용하여 BAAI/bge-m3 모델의 ONNX 버전을 실행합니다.
    """

    _instance: EmbeddingService | None = None
    _model: ORTModelForFeatureExtraction | None = None
    _tokenizer: Any = None

    def __new__(cls) -> EmbeddingService:
        """
        EmbeddingService의 싱글톤 인스턴스를 생성하거나 반환합니다.
        """
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            model_name = "BAAI/bge-m3"

            # 1. 토크나이저 로드
            cls._tokenizer = AutoTokenizer.from_pretrained(model_name)

            # 2. ONNX 모델 로드
            cls._model = ORTModelForFeatureExtraction.from_pretrained(
                model_name, subfolder="onnx", provider="CPUExecutionProvider"
            )
        return cls._instance

    def embed_text(self, text: str) -> list[float]:
        """단일 텍스트를 벡터로 변환합니다."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """여러 텍스트를 배치 처리하여 벡터로 변환합니다."""
        tokenizer = self._tokenizer
        model = self._model

        if model is None or tokenizer is None:
            raise RuntimeError("모델 또는 토크나이저가 로드되지 않았습니다.")

        # 1. 토큰화
        encoded_input = tokenizer(
            texts, padding=True, truncation=True, max_length=8192, return_tensors="pt"
        )

        # 2. 저수준 ONNX 추론 (optimum의 forward 에러 우회)
        # model.model은 실제 onnxruntime.InferenceSession 객체입니다.
        onnx_inputs = {k: v.cpu().numpy() for k, v in encoded_input.items()}

        # ONNX 실행 및 모든 출력 확보
        # outputs는 리스트 형태로 반환됩니다.
        onnx_outputs = model.model.run(None, onnx_inputs)

        # 3. 임베딩 추출 및 Pooling
        # bge-m3 ONNX 공식 모델의 출력 순서: [0] sequence_output, [1] pooled_output (또는 그 반대)
        # 대개 첫 번째 출력(index 0)이 sequence_output(Batch, Seq, Hidden)입니다.
        embeddings_np = onnx_outputs[0]
        embeddings = torch.from_numpy(embeddings_np)

        # 3차원(Batch, Seq, Hidden)이라면 CLS 토큰(0번 인덱스)만 추출
        if len(embeddings.shape) == 3:
            embeddings = embeddings[:, 0, :]

        # 4. L2 정규화 및 리스트 변환
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return [[float(x) for x in e] for e in embeddings.tolist()]


def get_embedding_service() -> EmbeddingService:
    """EmbeddingService 인스턴스를 반환합니다."""
    return EmbeddingService()
