"""
텔레그램 봇 알림 채널
"""
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from .base import BaseNotifier

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger('telegram_notifier')


class TelegramNotifier(BaseNotifier):
    """텔레그램 봇으로 알림 전송"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        # 텔레그램 설정 확인
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ 텔레그램 봇 설정이 없습니다. 텔레그램 알림이 비활성화됩니다.")
            self.enabled = False
        else:
            self.enabled = True
            # telegram 라이브러리는 실제 사용 시에만 import
            try:
                from telegram import Bot
                from telegram.error import TelegramError
                self.Bot = Bot
                self.TelegramError = TelegramError
            except ImportError:
                logger.warning("⚠️ python-telegram-bot 라이브러리가 설치되지 않았습니다.")
                self.enabled = False

    def get_channel_name(self) -> str:
        return "TELEGRAM"

    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        텔레그램으로 알림 전송

        Args:
            alert: 알림 데이터

        Returns:
            dict: 발송 결과
        """
        # 텔레그램이 비활성화된 경우
        if not self.enabled:
            return {
                'success': False,
                'message_id': None,
                'error': 'Telegram not configured or library not installed'
            }

        try:
            # 봇 인스턴스 생성
            bot = self.Bot(token=self.bot_token)

            # 메시지 포맷팅
            message = self._format_alert_message(alert)

            # 메시지 전송
            sent_message = bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )

            logger.info(f"✅ 텔레그램 전송 성공: message_id={sent_message.message_id}")

            return {
                'success': True,
                'message_id': str(sent_message.message_id),
                'error': None
            }

        except self.TelegramError as e:
            logger.error(f"❌ 텔레그램 전송 실패: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"⚠️ 예상치 못한 오류: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """알림 메시지 포맷팅 (Markdown)"""
        # 알림 타입에 따른 이모지
        emoji_map = {
            'ERROR': '🚨',
            'WARNING': '⚠️',
            'RECOVERY': '✅'
        }
        emoji = emoji_map.get(alert['alert_type'], '📢')

        message = f"""
{emoji} *{alert['alert_type']}* 알림

*URL:* {alert['target_url']}
*메시지:* {alert['message']}
*상태:* {alert['status']}
*발생 시각:* {alert['created_at']}
"""

        if alert.get('resolved_at'):
            message += f"*해결 시각:* {alert['resolved_at']}\n"

        return message.strip()
