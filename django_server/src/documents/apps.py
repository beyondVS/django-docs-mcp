import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "documents"

    def ready(self) -> None:
        """
        Django 서버 시작 시 검색에 필요한 임베딩 및 리랭커 모델을 미리 메모리에 로드(Warm-up)합니다.
        이를 통해 첫 번째 검색 요청에서의 응답 지연을 방지합니다.
        """
        import os
        import sys

        # 1. 환경 변수로 명시적 비활성화 가능
        if os.environ.get("SKIP_AI_MODELS") == "1":
            return

        # 2. 모델 로딩이 불필요한 상황인지 체크
        # manage.py로 실행되는 경우 중 runserver, ingest_docs가 아니면 건너뜀
        script_name = os.path.basename(sys.argv[0])
        if script_name == "manage.py":
            allowed_commands = {"runserver", "ingest_docs"}
            if not any(arg in allowed_commands for arg in sys.argv):
                return

        # 3. 테스트 환경(pytest 등)인 경우 건너뜀 (테스트 코드 내에서 필요 시 레이지 로딩됨)
        if "pytest" in sys.modules or "test" in sys.argv:
            return

        # 4. 실제 모델 로드 (Warm-up)
        try:
            from tqdm import tqdm

            from documents.services.embedding import get_embedding_service
            from documents.services.reranking import get_reranking_service

            logger.info("Starting AI search models warm-up...")

            # tqdm 로딩 바 설정 (총 2단계: 임베딩, 리랭커)
            with tqdm(
                total=2,
                desc="🚀 AI Search Models",
                bar_format="{l_bar}{bar:30}{r_bar}",
            ) as pbar:
                # 1. 임베딩 모델 로드
                pbar.set_postfix_str("Loading Embedding (BGE-M3)...")
                get_embedding_service()
                pbar.update(1)

                # 2. 리랭커 모델 로드
                pbar.set_postfix_str("Loading Reranker (ONNX INT8)...")
                get_reranking_service()
                pbar.update(1)

                pbar.set_postfix_str("All Ready! ✅")

            logger.info("All AI search models loaded successfully.")

        except Exception as e:
            logger.error(f"Search Models Warm-up failed: {e}")
            # 사용자에게 가시적으로 에러를 한 번 더 출력
            print(f"\n⚠️  [ERROR] AI Model Loading Failed: {e}\n")
