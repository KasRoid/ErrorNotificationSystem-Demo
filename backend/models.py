"""
데이터 모델 및 비즈니스 로직
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import insert_and_get_id, fetch_one, fetch_all, execute_query


class Event:
    """이벤트 모델 (URL 점검 결과)"""

    @staticmethod
    def create(target_url: str, status_code: Optional[int], response_time_ms: int,
               is_success: bool, error_message: Optional[str] = None) -> int:
        """이벤트 생성"""
        query = """
            INSERT INTO events (target_url, status_code, response_time_ms, is_success, error_message)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (target_url, status_code, response_time_ms, is_success, error_message)
        return insert_and_get_id(query, params)

    @staticmethod
    def get_by_id(event_id: int) -> Optional[Dict[str, Any]]:
        """ID로 이벤트 조회"""
        query = "SELECT * FROM events WHERE id = ?"
        return fetch_one(query, (event_id,))

    @staticmethod
    def get_recent_by_url(target_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """특정 URL의 최근 이벤트 조회"""
        query = """
            SELECT * FROM events
            WHERE target_url = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        return fetch_all(query, (target_url, limit))


class Alert:
    """알림 모델"""

    @staticmethod
    def create(event_id: int, alert_type: str, message: str, target_url: str) -> int:
        """알림 생성"""
        query = """
            INSERT INTO alerts (event_id, alert_type, message, target_url, status)
            VALUES (?, ?, ?, ?, 'OPEN')
        """
        params = (event_id, alert_type, message, target_url)
        return insert_and_get_id(query, params)

    @staticmethod
    def get_by_id(alert_id: int) -> Optional[Dict[str, Any]]:
        """ID로 알림 조회"""
        query = "SELECT * FROM alerts WHERE id = ?"
        return fetch_one(query, (alert_id,))

    @staticmethod
    def get_open_alert_by_url(target_url: str) -> Optional[Dict[str, Any]]:
        """특정 URL의 OPEN 또는 ACK 상태 알림 조회 (중복 방지용)"""
        query = """
            SELECT * FROM alerts
            WHERE target_url = ? AND status IN ('OPEN', 'ACK')
            ORDER BY created_at DESC
            LIMIT 1
        """
        return fetch_one(query, (target_url,))

    @staticmethod
    def get_all(status: Optional[str] = None) -> List[Dict[str, Any]]:
        """알림 목록 조회 (상태별 필터링 가능)"""
        if status:
            query = "SELECT * FROM alerts WHERE status = ? ORDER BY created_at DESC"
            return fetch_all(query, (status,))
        else:
            query = "SELECT * FROM alerts ORDER BY created_at DESC"
            return fetch_all(query)

    @staticmethod
    def update_status(alert_id: int, new_status: str) -> None:
        """알림 상태 변경"""
        if new_status == 'RESOLVED':
            query = """
                UPDATE alerts
                SET status = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
        else:
            query = "UPDATE alerts SET status = ? WHERE id = ?"

        execute_query(query, (new_status, alert_id))

    @staticmethod
    def resolve_by_url(target_url: str) -> None:
        """특정 URL의 모든 OPEN/ACK 알림을 RESOLVED로 변경"""
        query = """
            UPDATE alerts
            SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP
            WHERE target_url = ? AND status IN ('OPEN', 'ACK')
        """
        execute_query(query, (target_url,))


class NotificationLog:
    """알림 발송 로그 모델"""

    @staticmethod
    def create(alert_id: int, channel: str, status: str, response_code: Optional[str] = None,
               message_id: Optional[str] = None, retry_count: int = 0,
               error_message: Optional[str] = None) -> int:
        """알림 발송 로그 생성"""
        query = """
            INSERT INTO notification_logs
            (alert_id, channel, status, response_code, message_id, retry_count, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (alert_id, channel, status, response_code, message_id, retry_count, error_message)
        return insert_and_get_id(query, params)

    @staticmethod
    def get_by_alert_id(alert_id: int) -> List[Dict[str, Any]]:
        """특정 알림의 발송 로그 조회"""
        query = """
            SELECT * FROM notification_logs
            WHERE alert_id = ?
            ORDER BY attempted_at DESC
        """
        return fetch_all(query, (alert_id,))

    @staticmethod
    def get_recent(limit: int = 50) -> List[Dict[str, Any]]:
        """최근 발송 로그 조회"""
        query = """
            SELECT * FROM notification_logs
            ORDER BY attempted_at DESC
            LIMIT ?
        """
        return fetch_all(query, (limit,))
