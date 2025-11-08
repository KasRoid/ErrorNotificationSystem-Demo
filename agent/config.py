"""
Agent 환경변수 설정 관리
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """Agent 설정"""

    # 점검 대상 URL
    TARGET_URL = os.getenv('TARGET_URL', 'https://www.google.com')

    # 점검 주기 (초)
    CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', '30'))

    # 백엔드 서버 URL
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

    # API 키 (백엔드 인증용)
    API_KEY = os.getenv('API_KEY', 'my-secret-key-12345')

    # HTTP 요청 타임아웃 (초)
    REQUEST_TIMEOUT = 5

    # 재시도 설정
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2  # 지수 백오프 (2^n초)


# 설정 검증
def validate_config():
    """설정값 검증"""
    if not Config.TARGET_URL:
        raise ValueError("TARGET_URL이 설정되지 않았습니다.")

    if not Config.BACKEND_URL:
        raise ValueError("BACKEND_URL이 설정되지 않았습니다.")

    if not Config.API_KEY:
        raise ValueError("API_KEY가 설정되지 않았습니다.")

    if Config.CHECK_INTERVAL_SECONDS < 1:
        raise ValueError("CHECK_INTERVAL_SECONDS는 최소 1초 이상이어야 합니다.")

    return True
