import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, level=logging.INFO):
    """
    Setup logger với file handler và console handler
    Logs được lưu vào backend/logs/
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create logs directory
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)

    # File handler
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str):
    """Lấy logger instance"""
    return setup_logger(name)
