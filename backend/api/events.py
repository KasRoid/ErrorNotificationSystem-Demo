"""
/events API - 이벤트 수신 및 처리
"""
from flask import Blueprint, request, jsonify
from models import Event, Alert, NotificationLog
from notifiers.console import ConsoleNotifier
from notifiers.telegram import TelegramNotifier
import logging
import os

# Blueprint 생성
events_bp = Blueprint('events', __name__)

# 로거
logger = logging.getLogger('events_api')

# 알림 채널
console_notifier = ConsoleNotifier()
telegram_notifier = TelegramNotifier()

# API 키 (환경변수에서 로드)
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('API_KEY', 'my-secret-key-12345')


def verify_api_key():
    """API 키 검증"""
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != API_KEY:
        return False
    return True


@events_bp.route('/events', methods=['POST'])
def create_event():
    """이벤트 수신 API"""
    # API 키 검증
    if not verify_api_key():
        logger.warning("⚠️ 인증 실패: 잘못된 API 키")
        return jsonify({'error': 'Unauthorized'}), 401

    # 요청 데이터 파싱
    data = request.get_json()

    # 필수 필드 검증
    required_fields = ['target_url', 'response_time_ms', 'is_success', 'timestamp']
    for field in required_fields:
        if field not in data:
            logger.warning(f"⚠️ 필수 필드 누락: {field}")
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        # 이벤트 생성
        event_id = Event.create(
            target_url=data['target_url'],
            status_code=data.get('status_code'),
            response_time_ms=data['response_time_ms'],
            is_success=data['is_success'],
            error_message=data.get('error_message')
        )

        logger.info(f"✅ 이벤트 저장 완료: event_id={event_id}, url={data['target_url']}, success={data['is_success']}")

        # 장애 감지 및 알림 처리
        if not data['is_success']:
            handle_failure(event_id, data)
        else:
            # 정상 응답 시 복구 감지
            handle_recovery(data['target_url'])

        return jsonify({
            'success': True,
            'event_id': event_id
        }), 201

    except Exception as e:
        logger.error(f"❌ 이벤트 처리 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


def handle_failure(event_id: int, data: dict):
    """장애 처리 및 알림 생성"""
    target_url = data['target_url']

    # 중복 알림 방지: 이미 OPEN 또는 ACK 상태의 알림이 있는지 확인
    existing_alert = Alert.get_open_alert_by_url(target_url)

    if existing_alert:
        logger.info(f"ℹ️ 기존 알림 존재 (중복 방지): alert_id={existing_alert['id']}, url={target_url}")
        return

    # 새 알림 생성
    message = create_error_message(data)
    alert_id = Alert.create(
        event_id=event_id,
        alert_type='ERROR',
        message=message,
        target_url=target_url
    )

    logger.warning(f"🚨 알림 생성: alert_id={alert_id}, url={target_url}")

    # 알림 발송
    send_notifications(alert_id)


def handle_recovery(target_url: str):
    """복구 감지 및 처리"""
    # OPEN 또는 ACK 상태의 알림이 있는지 확인
    existing_alert = Alert.get_open_alert_by_url(target_url)

    if existing_alert:
        logger.info(f"✅ 복구 감지: alert_id={existing_alert['id']}, url={target_url}")

        # 기존 알림을 RESOLVED로 변경
        Alert.resolve_by_url(target_url)

        # 복구 알림 생성
        event = Event.get_recent_by_url(target_url, limit=1)[0]
        alert_id = Alert.create(
            event_id=event['id'],
            alert_type='RECOVERY',
            message='서비스가 정상 복구되었습니다.',
            target_url=target_url
        )

        # 복구 알림도 즉시 RESOLVED로 설정
        Alert.update_status(alert_id, 'RESOLVED')

        # 복구 알림 발송
        send_notifications(alert_id)


def send_notifications(alert_id: int):
    """알림 발송 (모든 채널)"""
    alert = Alert.get_by_id(alert_id)

    if not alert:
        logger.error(f"❌ 알림을 찾을 수 없음: alert_id={alert_id}")
        return

    # 콘솔 알림
    console_result = console_notifier.send(alert)
    NotificationLog.create(
        alert_id=alert_id,
        channel=console_notifier.get_channel_name(),
        status='SENT' if console_result['success'] else 'FAILED',
        response_code=None,
        message_id=console_result.get('message_id'),
        error_message=console_result.get('error')
    )

    # 텔레그램 알림 (활성화된 경우만)
    if telegram_notifier.enabled:
        telegram_result = telegram_notifier.send(alert)
        NotificationLog.create(
            alert_id=alert_id,
            channel=telegram_notifier.get_channel_name(),
            status='SENT' if telegram_result['success'] else 'FAILED',
            response_code=None,
            message_id=telegram_result.get('message_id'),
            error_message=telegram_result.get('error')
        )


def create_error_message(data: dict) -> str:
    """에러 메시지 생성"""
    if data.get('error_message'):
        return data['error_message']
    elif data.get('status_code'):
        return f"HTTP {data['status_code']} 응답 코드"
    else:
        return "서비스 응답 없음"
