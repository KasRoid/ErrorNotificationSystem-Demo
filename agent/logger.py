"""
Agent 로거 설정
"""
import logging
import os
from logging.handlers import RotatingFileHandler

# 로그 파일 경로
LOG_FILE = os.path.join(os.path.dirname(__file__), 'agent.log')


def setup_logger(name='agent', level=logging.INFO):
    """로거 설정 및 반환"""

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 이미 핸들러가 있으면 중복 추가 방지
    if logger.handlers:
        return logger

    # 포맷터 설정
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 파일 핸들러 (로그 파일에 기록, 최대 5MB, 백업 3개)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # 콘솔 핸들러 (터미널 출력)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
