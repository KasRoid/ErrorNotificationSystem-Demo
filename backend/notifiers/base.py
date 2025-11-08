"""
알림 채널 베이스 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseNotifier(ABC):
    """알림 채널 추상 클래스"""

    @abstractmethod
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        알림 발송

        Args:
            alert: 알림 데이터 (alerts 테이블 레코드)

        Returns:
            dict: 발송 결과
                - success: bool (성공 여부)
                - message_id: str (메시지 ID, 선택)
                - error: str (에러 메시지, 선택)
        """
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """채널 이름 반환"""
        pass
