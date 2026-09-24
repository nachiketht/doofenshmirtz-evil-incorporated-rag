import logging

logger = logging.getLogger("ingest")


def configure_logging() -> None:
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.name = "console"
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


def log(step: str, message: str) -> None:
    configure_logging()
    logger.info("%s %s", step, message)
