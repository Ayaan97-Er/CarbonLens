import logging
import sys


def setup_logging():
    """Configure structured logging for CarbonLens application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logger = logging.getLogger("carbonlens")
    logger.setLevel(logging.INFO)
    return logger
