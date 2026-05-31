"""
應用程式日誌設定

用法:
    from src.logging_config import get_logger
    log = get_logger(__name__)
    log.info("message")
    log.warning("message")
    log.error("message", exc_info=True)
"""
import logging
import sys

_FORMAT = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
_DATE_FMT = "%H:%M:%S"

_initialized = False


def setup_logging(*, level: int = logging.INFO) -> None:
    """初始化全域日誌設定（僅執行一次）"""
    global _initialized
    if _initialized:
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FMT))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # 抑制第三方 library 的噪音
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("lxml").setLevel(logging.WARNING)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """取得具名 logger"""
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)
