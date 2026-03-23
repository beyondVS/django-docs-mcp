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
            from django.conf import settings
            from documents.services.embedding import get_embedding_service

            # 환경 설정에 따른 모델명 결정
            use_onnx = getattr(settings, "USE_ONNX_EMBEDDING", True)
            model_display_name = "BGE-M3 (ONNX INT8)" if use_onnx else "BGE-M3 (Standard)"

            logger.info(f"Starting AI search model warm-up: {model_display_name}")

            # tqdm 로딩 바 설정 (임베딩 모델 1단계)
            with tqdm(
                total=1,
                desc="🚀 AI Search Model",
                bar_format="{l_bar}{bar:25}{r_bar}",
            ) as pbar:
                pbar.set_postfix_str(f"Loading {model_display_name}...")
                get_embedding_service()
                pbar.update(1)
                pbar.set_description(f"🚀 AI Search: {model_display_name} Loaded")

                pbar.set_postfix_str("All Ready! ✅")

            logger.info("All AI search models loaded successfully.")

        except Exception as e:
            logger.error(f"Search Models Warm-up failed: {e}")
            # 사용자에게 가시적으로 에러를 한 번 더 출력
            print(f"\n⚠️  [ERROR] AI Model Loading Failed: {e}\n")
