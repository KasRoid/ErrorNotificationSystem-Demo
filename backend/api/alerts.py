"""
/alerts API - 알림 조회 및 상태 변경
"""
from flask import Blueprint, request, jsonify
from models import Alert, NotificationLog
import logging

# Blueprint 생성
alerts_bp = Blueprint('alerts', __name__)

# 로거
logger = logging.getLogger('alerts_api')


@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """알림 목록 조회 API"""
    # 쿼리 파라미터에서 상태 필터링
    status = request.args.get('status')

    try:
        # 알림 목록 조회
        if status:
            alerts = Alert.get_all(status=status.upper())
            logger.info(f"📋 알림 목록 조회: status={status}, count={len(alerts)}")
        else:
            alerts = Alert.get_all()
            logger.info(f"📋 알림 목록 조회: 전체, count={len(alerts)}")

        return jsonify({
            'success': True,
            'count': len(alerts),
            'alerts': alerts
        }), 200

    except Exception as e:
        logger.error(f"❌ 알림 목록 조회 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id: int):
    """특정 알림 상세 조회 API"""
    try:
        alert = Alert.get_by_id(alert_id)

        if not alert:
            logger.warning(f"⚠️ 알림을 찾을 수 없음: alert_id={alert_id}")
            return jsonify({'error': 'Alert not found'}), 404

        # 알림 발송 로그도 함께 조회
        notification_logs = NotificationLog.get_by_alert_id(alert_id)

        logger.info(f"📄 알림 상세 조회: alert_id={alert_id}")

        return jsonify({
            'success': True,
            'alert': alert,
            'notification_logs': notification_logs
        }), 200

    except Exception as e:
        logger.error(f"❌ 알림 상세 조회 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/alerts/<int:alert_id>', methods=['PATCH'])
def update_alert_status(alert_id: int):
    """알림 상태 변경 API"""
    data = request.get_json()

    # 상태 필드 검증
    if 'status' not in data:
        logger.warning("⚠️ 필수 필드 누락: status")
        return jsonify({'error': 'Missing required field: status'}), 400

    new_status = data['status'].upper()

    # 유효한 상태 값 검증
    valid_statuses = ['OPEN', 'ACK', 'RESOLVED']
    if new_status not in valid_statuses:
        logger.warning(f"⚠️ 잘못된 상태 값: {new_status}")
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    try:
        # 알림 존재 확인
        alert = Alert.get_by_id(alert_id)
        if not alert:
            logger.warning(f"⚠️ 알림을 찾을 수 없음: alert_id={alert_id}")
            return jsonify({'error': 'Alert not found'}), 404

        # 상태 변경
        Alert.update_status(alert_id, new_status)
        logger.info(f"✅ 알림 상태 변경: alert_id={alert_id}, {alert['status']} → {new_status}")

        # 업데이트된 알림 조회
        updated_alert = Alert.get_by_id(alert_id)

        return jsonify({
            'success': True,
            'alert': updated_alert
        }), 200

    except Exception as e:
        logger.error(f"❌ 알림 상태 변경 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/notification_logs', methods=['GET'])
def get_notification_logs():
    """알림 발송 로그 조회 API"""
    # 쿼리 파라미터에서 limit 가져오기 (기본값: 50)
    limit = request.args.get('limit', default=50, type=int)

    try:
        logs = NotificationLog.get_recent(limit=limit)
        logger.info(f"📋 알림 발송 로그 조회: count={len(logs)}")

        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        }), 200

    except Exception as e:
        logger.error(f"❌ 알림 발송 로그 조회 중 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500
