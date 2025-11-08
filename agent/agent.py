"""
모니터링 Agent 메인 스크립트
대상 URL을 주기적으로 점검하고 백엔드로 데이터 전송
"""
import time
import requests
import schedule
from datetime import datetime
from config import Config, validate_config
from logger import setup_logger

# 로거 초기화
logger = setup_logger()


def check_url(url: str) -> dict:
    """
    대상 URL 점검

    Returns:
        dict: 점검 결과
            - target_url: 점검 대상 URL
            - status_code: HTTP 응답 코드 (None if error)
            - response_time_ms: 응답 시간 (밀리초)
            - timestamp: 점검 시각
            - is_success: 정상 여부
            - error_message: 에러 메시지 (있을 경우)
    """
    result = {
        'target_url': url,
        'status_code': None,
        'response_time_ms': 0,
        'timestamp': datetime.utcnow().isoformat(),
        'is_success': False,
        'error_message': None
    }

    try:
        # 시작 시간 기록
        start_time = time.time()

        # HTTP 요청
        response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)

        # 응답 시간 계산 (밀리초)
        response_time_ms = int((time.time() - start_time) * 1000)

        # 결과 설정
        result['status_code'] = response.status_code
        result['response_time_ms'] = response_time_ms
        result['is_success'] = 200 <= response.status_code < 400

        logger.info(f"✅ URL 점검 성공: {url} - {response.status_code} ({response_time_ms}ms)")

    except requests.exceptions.Timeout:
        result['response_time_ms'] = Config.REQUEST_TIMEOUT * 1000
        result['error_message'] = f"Request timed out after {Config.REQUEST_TIMEOUT}s"
        logger.warning(f"⏱️ 타임아웃: {url} - {result['error_message']}")

    except requests.exceptions.ConnectionError as e:
        result['error_message'] = f"Connection error: {str(e)}"
        logger.error(f"🔌 연결 실패: {url} - {result['error_message']}")

    except requests.exceptions.RequestException as e:
        result['error_message'] = f"Request error: {str(e)}"
        logger.error(f"❌ 요청 실패: {url} - {result['error_message']}")

    except Exception as e:
        result['error_message'] = f"Unexpected error: {str(e)}"
        logger.error(f"⚠️ 예상치 못한 오류: {url} - {result['error_message']}")

    return result


def send_to_backend(data: dict, retry_count: int = 0) -> bool:
    """
    백엔드로 점검 데이터 전송

    Args:
        data: 점검 결과 데이터
        retry_count: 현재 재시도 횟수

    Returns:
        bool: 전송 성공 여부
    """
    endpoint = f"{Config.BACKEND_URL}/events"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': Config.API_KEY
    }

    try:
        response = requests.post(
            endpoint,
            json=data,
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT
        )

        if response.status_code == 201:
            logger.info(f"📤 백엔드 전송 성공: {endpoint}")
            return True
        else:
            logger.warning(f"⚠️ 백엔드 응답 오류: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 백엔드 연결 실패: {endpoint}")

        # 재시도 로직
        if retry_count < Config.MAX_RETRIES:
            wait_time = Config.RETRY_BACKOFF_FACTOR ** retry_count
            logger.info(f"🔄 {wait_time}초 후 재시도 ({retry_count + 1}/{Config.MAX_RETRIES})...")
            time.sleep(wait_time)
            return send_to_backend(data, retry_count + 1)
        else:
            logger.error(f"❌ 최대 재시도 횟수 초과: {Config.MAX_RETRIES}회")
            return False

    except Exception as e:
        logger.error(f"⚠️ 전송 중 예상치 못한 오류: {str(e)}")
        return False


def monitoring_job():
    """주기적으로 실행되는 모니터링 작업"""
    logger.info("=" * 60)
    logger.info(f"🔍 모니터링 시작: {Config.TARGET_URL}")

    # URL 점검
    result = check_url(Config.TARGET_URL)

    # 백엔드 전송
    success = send_to_backend(result)

    if success:
        logger.info("✅ 모니터링 사이클 완료")
    else:
        logger.error("❌ 모니터링 사이클 실패 (백엔드 전송 실패)")

    logger.info("=" * 60)


def main():
    """Agent 메인 함수"""
    try:
        # 설정 검증
        validate_config()

        logger.info("🚀 모니터링 Agent 시작")
        logger.info(f"   대상 URL: {Config.TARGET_URL}")
        logger.info(f"   점검 주기: {Config.CHECK_INTERVAL_SECONDS}초")
        logger.info(f"   백엔드 URL: {Config.BACKEND_URL}")
        logger.info("-" * 60)

        # 즉시 한 번 실행
        monitoring_job()

        # 주기적 실행 스케줄 등록
        schedule.every(Config.CHECK_INTERVAL_SECONDS).seconds.do(monitoring_job)

        logger.info(f"⏰ 스케줄 등록 완료: {Config.CHECK_INTERVAL_SECONDS}초마다 실행")

        # 무한 루프 (스케줄러 실행)
        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("\n⏹️ Agent 종료 (사용자 중단)")

    except Exception as e:
        logger.error(f"💥 Agent 실행 중 치명적 오류: {str(e)}")
        raise


if __name__ == '__main__':
    main()
