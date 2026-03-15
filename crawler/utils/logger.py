import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    크롤러를 위해 구성된 로거를 반환합니다.

    Args:
        name (str): 로거의 이름 (일반적으로 __name__ 사용).

    Returns:
        logging.Logger: 설정이 완료된 로거 인스턴스.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
