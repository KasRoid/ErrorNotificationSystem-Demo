# 웹서비스 장애 알림 시스템

실시간으로 웹서비스 상태를 모니터링하고 장애 발생 시 알림을 발송하는 시스템입니다.

## 시스템 구성

- **Agent**: 대상 URL을 주기적으로 점검하고 백엔드로 데이터 전송
- **Backend**: 이벤트 수신, 장애 감지, 알림 발송
- **Database**: SQLite (이벤트, 알림, 발송 로그 저장)
- **알림 채널**: 콘솔 출력, 텔레그램 봇 (선택)

## 주요 기능

- URL 상태 주기적 점검 (기본 30초)
- HTTP 응답 코드 및 응답 시간 수집
- 장애 감지 및 자동 알림 발송
- 중복 알림 방지
- 복구 감지 및 알림
- 알림 상태 관리 (OPEN/ACK/RESOLVED)

## 프로젝트 구조

```
.
├── agent/                      # 모니터링 Agent
│   ├── agent.py               # Agent 메인 스크립트
│   ├── config.py              # 설정 관리
│   ├── logger.py              # 로그 설정
│   └── agent.log              # Agent 로그 (실행 후 생성)
├── backend/                    # Flask 백엔드 서버
│   ├── app.py                 # Flask 서버 엔트리
│   ├── database.py            # SQLite 연결 및 쿼리
│   ├── models.py              # 데이터 모델
│   ├── init_db.py             # DB 초기화 스크립트
│   ├── api/
│   │   ├── events.py          # /events API
│   │   └── alerts.py          # /alerts API
│   ├── notifiers/
│   │   ├── base.py            # 알림 채널 인터페이스
│   │   ├── console.py         # 콘솔 출력 채널
│   │   └── telegram.py        # 텔레그램 채널
│   └── server.log             # 서버 로그 (실행 후 생성)
├── notifications.db            # SQLite 데이터베이스 (초기화 후 생성)
├── .env                        # 환경변수 설정
├── .env.example                # 환경변수 예시
├── requirements.txt            # Python 패키지 목록
└── README.md                   # 이 파일
```

## 설치 및 실행

### 1. 환경 준비

```bash
# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 수정하여 설정을 변경할 수 있습니다.

```bash
# Agent 설정
TARGET_URL=https://www.google.com          # 점검 대상 URL
CHECK_INTERVAL_SECONDS=30                   # 점검 주기 (초)
BACKEND_URL=http://localhost:5000           # 백엔드 서버 URL
API_KEY=my-secret-key-12345                 # API 인증 키

# Backend 설정
FLASK_PORT=5000                             # Flask 서버 포트
FLASK_DEBUG=true                            # 디버그 모드

# [선택] 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN=                         # 텔레그램 봇 토큰
TELEGRAM_CHAT_ID=                           # 텔레그램 채팅 ID
```

### 3. 데이터베이스 초기화

```bash
cd backend
python init_db.py
```

### 4. 백엔드 서버 실행

**터미널 1:**
```bash
cd backend
python app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

### 5. Agent 실행

**터미널 2:**
```bash
cd agent
python agent.py
```

Agent가 30초마다 대상 URL을 점검하고 백엔드로 데이터를 전송합니다.

## API 엔드포인트

### 헬스체크
```bash
GET /
```

### 이벤트 수신
```bash
POST /events
Headers: X-API-Key: <API_KEY>
Body: {
  "target_url": "https://example.com",
  "status_code": 200,
  "response_time_ms": 150,
  "timestamp": "2025-01-08T10:30:00",
  "is_success": true,
  "error_message": null
}
```

### 알림 목록 조회
```bash
GET /alerts
GET /alerts?status=OPEN
```

### 알림 상세 조회
```bash
GET /alerts/<alert_id>
```

### 알림 상태 변경
```bash
PATCH /alerts/<alert_id>
Body: {
  "status": "ACK"  # OPEN, ACK, RESOLVED
}
```

### 알림 발송 로그 조회
```bash
GET /notification_logs
GET /notification_logs?limit=100
```

## 데이터베이스 조회

```bash
# events 테이블 (최근 5개)
sqlite3 notifications.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 5;"

# OPEN 상태 알림
sqlite3 notifications.db "SELECT * FROM alerts WHERE status='OPEN';"

# 발송 로그 (최근 5개)
sqlite3 notifications.db "SELECT * FROM notification_logs ORDER BY attempted_at DESC LIMIT 5;"
```

## 로그 확인

```bash
# 서버 로그 (실시간)
tail -f backend/server.log

# Agent 로그 (실시간)
tail -f agent/agent.log
```

## 텔레그램 봇 설정 (선택)

### 1. 텔레그램 봇 생성

1. 텔레그램에서 [@BotFather](https://t.me/botfather) 검색
2. `/newbot` 명령어 실행
3. 봇 이름 및 username 설정
4. API 토큰 받기

### 2. Chat ID 확인

1. 생성한 봇과 대화 시작 (아무 메시지나 보내기)
2. 다음 URL 접속: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. 응답에서 `chat.id` 값 확인

### 3. 환경변수 설정

`.env` 파일에 다음 추가:
```bash
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here
```

## 테스트 시나리오

### 1. 정상 동작 테스트

```bash
# .env 파일에서 정상 URL 설정
TARGET_URL=https://www.google.com
```

- Agent가 정상적으로 점검
- events 테이블에 is_success=1로 저장
- 알림 생성 안 됨

### 2. 장애 발생 테스트

```bash
# .env 파일에서 존재하지 않는 URL 설정
TARGET_URL=https://nonexistent-domain-12345.com
```

- Agent가 타임아웃 감지
- alerts 테이블에 OPEN 상태 알림 생성
- 콘솔에 알림 출력
- notification_logs에 SENT 기록

### 3. 중복 알림 방지 테스트

- 동일 URL에 장애가 계속 발생
- 기존 OPEN 알림 유지
- 새 알림 생성 안 됨

### 4. 복구 감지 테스트

```bash
# 장애 URL을 다시 정상 URL로 변경
TARGET_URL=https://www.google.com
```

- 복구 감지
- 기존 알림 RESOLVED 상태로 변경
- RECOVERY 타입 알림 발송

## 문제 해결

### Agent가 백엔드에 연결하지 못하는 경우

```bash
# 백엔드 서버가 실행 중인지 확인
curl http://localhost:5000/

# 방화벽 확인
# .env 파일의 BACKEND_URL 확인
```

### 텔레그램 알림이 발송되지 않는 경우

```bash
# 봇 토큰 및 채팅 ID 확인
# python-telegram-bot 라이브러리 설치 확인
pip list | grep telegram

# 서버 로그 확인
tail -f backend/server.log
```

### 데이터베이스 초기화

```bash
# 데이터베이스 파일 삭제 후 재생성
rm notifications.db
cd backend
python init_db.py
```

## 라이센스

MIT License

## 작성자

- 장애 알림 시스템 데모 프로젝트
