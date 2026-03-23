import logging

from tqdm import tqdm


class TqdmLoggingHandler(logging.Handler):
    """tqdm.write를 사용하여 진행률 표시줄과 로그가 겹치지 않게 하는 핸들러"""

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


def get_logger(name: str) -> logging.Logger:
    """
    크롤러를 위해 구성된 로거를 반환합니다.
    tqdm과 호환되는 TqdmLoggingHandler를 사용합니다.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # 기본 StreamHandler 대신 TqdmLoggingHandler 사용
        handler = TqdmLoggingHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
