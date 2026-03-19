import logging
import struct
from typing import Any

import numpy as np
import torch
from django.conf import settings
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    텍스트 데이터를 벡터 임베딩으로 변환하는 싱글톤 서비스 클래스.

    BGE-M3 ONNX INT8 모델을 사용하여 Dense 벡터와 Late Interaction용 멀티 벡터를 생성합니다.
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
            model_name = getattr(settings, "EMBEDDING_MODEL_NAME", "gpahal/bge-m3-onnx-int8")

            try:
                # 1. 토크나이저 로드
                cls._tokenizer = AutoTokenizer.from_pretrained(model_name)

                # 2. ONNX 모델 로드
                # gpahal/bge-m3-onnx-int8은 model_quantized.onnx 파일을 사용함
                cls._model = ORTModelForFeatureExtraction.from_pretrained(
                    model_name, file_name="model_quantized.onnx", provider="CPUExecutionProvider"
                )
                logger.info(f"Successfully loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model {model_name}: {str(e)}")
                raise
        return cls._instance

    def embed_text(self, text: str) -> dict[str, Any]:
        """
        단일 텍스트를 Dense 벡터와 압축된 멀티 벡터로 변환합니다.
        """
        results = self.embed_batch([text])
        return results[0]

    def embed_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """
        여러 텍스트를 배치 처리하여 Dense 벡터와 압축된 멀티 벡터를 생성합니다.
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
        onnx_inputs = {k: v.cpu().numpy() for k, v in encoded_input.items()}
        onnx_outputs = model.model.run(None, onnx_inputs)

        # 3. 출력 데이터 파싱 (gpahal/bge-m3-onnx-int8 모델 기준)
        # onnx_outputs[0]: dense_vecs [Batch, 1024]
        # onnx_outputs[1]: sparse_vecs [Batch, Seq, 1]
        # onnx_outputs[2]: colbert_vecs [Batch, Seq', 1024]
        pooler_output = onnx_outputs[0]
        last_hidden_state = onnx_outputs[2]

        # 4. Dense 벡터 처리 (L2 정규화)
        dense_embeddings = torch.from_numpy(pooler_output)
        dense_embeddings = torch.nn.functional.normalize(dense_embeddings, p=2, dim=1)
        dense_list = dense_embeddings.tolist()

        # 5. 멀티 벡터 처리 (Late Interaction 최적화)
        results = []
        dim = getattr(settings, "LATE_INTERACTION_DIM", 128)

        for i in range(len(texts)):
            # 해당 문장의 실제 출력 토큰 수 확인 (last_hidden_state의 1번 차원)
            actual_seq_len = last_hidden_state.shape[1]

            # 유효 토큰 마스크 확인 (Attention Mask 활용)
            mask = onnx_inputs["attention_mask"][i]
            valid_token_count = int(np.sum(mask))

            # mask와 actual_seq_len 중 작은 값 사용 (안정성 확보)
            n_tokens = min(valid_token_count, actual_seq_len)

            # 유효 토큰만 추출 및 차원 슬라이싱 (Matryoshka: 상위 128차원)
            multi_vec = last_hidden_state[i, :n_tokens, :dim]

            # L2 정규화 (MaxSim 정확도 확보)
            multi_vec_tensor = torch.from_numpy(multi_vec)
            multi_vec_tensor = torch.nn.functional.normalize(multi_vec_tensor, p=2, dim=1)
            multi_vec = multi_vec_tensor.numpy()

            # int8 양자화 (-128 ~ 127)
            multi_vec_int8 = (multi_vec * 127).astype(np.int8)

            # 바이너리 패킹: [TokenCount(2B)][VectorData]
            header = struct.pack("<H", n_tokens)
            data = multi_vec_int8.tobytes()

            results.append(
                {
                    "dense_vector": [float(x) for x in dense_list[i]],
                    "multi_vector_bytes": header + data,
                    "token_count": n_tokens,
                }
            )

        return results


def get_embedding_service() -> EmbeddingService:
    """EmbeddingService 인스턴스를 반환합니다."""
    return EmbeddingService()
