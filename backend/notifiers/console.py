"""
콘솔 출력 알림 채널
"""
import logging
from typing import Dict, Any
from .base import BaseNotifier

# 로거 설정
logger = logging.getLogger('console_notifier')


class ConsoleNotifier(BaseNotifier):
    """콘솔 및 로그 파일로 알림 출력"""

    def get_channel_name(self) -> str:
        return "CONSOLE"

    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        콘솔에 알림 출력 및 로그 파일에 기록

        Args:
            alert: 알림 데이터

        Returns:
            dict: 발송 결과
        """
        try:
            # 알림 타입에 따른 이모지 선택
            emoji_map = {
                'ERROR': '🚨',
                'WARNING': '⚠️',
                'RECOVERY': '✅'
            }
            emoji = emoji_map.get(alert['alert_type'], '📢')

            # 알림 메시지 포맷팅
            message = self._format_alert_message(alert, emoji)

            # 콘솔 및 로그 파일에 출력
            if alert['alert_type'] == 'ERROR':
                logger.error(message)
            elif alert['alert_type'] == 'WARNING':
                logger.warning(message)
            else:
                logger.info(message)

            # 구분선 출력
            logger.info("=" * 80)

            return {
                'success': True,
                'message_id': None,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

    def _format_alert_message(self, alert: Dict[str, Any], emoji: str) -> str:
        """알림 메시지 포맷팅"""
        lines = [
            "=" * 80,
            f"{emoji} {alert['alert_type']} 알림",
            "-" * 80,
            f"대상 URL: {alert['target_url']}",
            f"메시지: {alert['message']}",
            f"상태: {alert['status']}",
            f"발생 시각: {alert['created_at']}"
        ]

        if alert.get('resolved_at'):
            lines.append(f"해결 시각: {alert['resolved_at']}")

        return '\n'.join(lines)
