# 웹서비스 장애 알림 시스템

실시간으로 웹서비스 상태를 모니터링하고 장애 발생 시 알림을 발송하는 시스템입니다.

## 시스템 개요

- **Agent**: 대상 URL을 주기적으로 점검 (기본 30초)하고 백엔드로 데이터 전송
- **Backend**: 이벤트 수신, 장애 감지, 알림 발송 (콘솔 + 텔레그램)
- **Database**: SQLite로 이벤트, 알림, 발송 로그 저장
- **핵심 기능**: 장애 감지, 중복 알림 방지, 복구 감지, 상태 관리

---

## 🚀 빠른 시작 (Quick Start)

### 1단계: 환경 준비

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 데이터베이스 초기화

```bash
cd backend
python init_db.py
cd ..
```

**예상 출력:**
```
✅ 데이터베이스 초기화 완료: /path/to/notifications.db
✅ 테이블 생성 완료:
   - events (점검 결과)
   - alerts (알림 이벤트)
   - notification_logs (발송 기록)
```

### 3단계: 백엔드 서버 실행

**터미널 1을 열고:**

```bash
cd backend
source ../venv/bin/activate
python app.py
```

**예상 출력:**
```
🚀 Error Notification System 백엔드 서버 시작
   포트: 5001
   디버그 모드: True
 * Running on http://127.0.0.1:5001
```

**서버 확인 (새 터미널에서):**
```bash
curl http://localhost:5001/
```

**예상 응답:**
```json
{
  "service": "Error Notification System",
  "status": "healthy",
  "version": "1.0.0"
}
```

### 4단계: Agent 실행

**터미널 2를 열고:**

```bash
cd agent
source ../venv/bin/activate
python agent.py
```

**예상 출력:**
```
🚀 모니터링 Agent 시작
   대상 URL: https://www.google.com
   점검 주기: 30초
   백엔드 URL: http://localhost:5001
============================================================
🔍 모니터링 시작: https://www.google.com
✅ URL 점검 성공: https://www.google.com - 200 (364ms)
📤 백엔드 전송 성공: http://localhost:5001/events
✅ 모니터링 사이클 완료
============================================================
⏰ 스케줄 등록 완료: 30초마다 실행
```

**축하합니다! 시스템이 정상 작동하고 있습니다.** 🎉

---

## 📋 테스트 시나리오

실제로 시스템이 어떻게 작동하는지 단계별로 테스트해보세요.

### 시나리오 1: 정상 동작 확인

**목적**: URL이 정상일 때 시스템이 올바르게 동작하는지 확인

#### 1-1. 현재 상태 확인

`.env` 파일을 확인하세요:
```bash
cat .env | grep TARGET_URL
```

**결과:**
```
TARGET_URL=https://www.google.com
```

#### 1-2. 데이터베이스 확인

30초 이상 기다린 후 events 테이블을 확인하세요:

```bash
sqlite3 notifications.db "SELECT id, target_url, status_code, response_time_ms, is_success FROM events ORDER BY timestamp DESC LIMIT 3;"
```

**예상 결과:**
```
3|https://www.google.com|200|302|1
2|https://www.google.com|200|364|1
1|https://www.google.com|200|350|1
```

#### 1-3. 알림 확인

알림이 생성되지 않았는지 확인:

```bash
sqlite3 notifications.db "SELECT * FROM alerts;"
```

**예상 결과:** (빈 출력 - 정상 URL이므로 알림 없음)

✅ **테스트 통과**: 정상 URL은 알림을 발생시키지 않습니다.

---

### 시나리오 2: 장애 감지 및 알림 발송

**목적**: 장애가 발생했을 때 알림이 제대로 발송되는지 확인

#### 2-1. 장애 URL로 변경

**Agent를 중지하세요 (Ctrl+C)**

`.env` 파일을 수정:
```bash
# .env 파일 열기
nano .env  # 또는 vim, code 등

# TARGET_URL을 다음으로 변경:
TARGET_URL=https://nonexistent-domain-test-12345.com
```

#### 2-2. Agent 재시작

```bash
cd agent
python agent.py
```

**예상 출력 (즉시 확인):**
```
🔍 모니터링 시작: https://nonexistent-domain-test-12345.com
🔌 연결 실패: https://nonexistent-domain-test-12345.com - Connection error: ...
📤 백엔드 전송 성공: http://localhost:5001/events
✅ 모니터링 사이클 완료
```

#### 2-3. 백엔드 서버 로그 확인 (터미널 1)

백엔드 터미널에서 다음과 같은 알림 출력을 확인하세요:

```
🚨 알림 생성: alert_id=1, url=https://nonexistent-domain-test-12345.com
================================================================================
🚨 ERROR 알림
--------------------------------------------------------------------------------
대상 URL: https://nonexistent-domain-test-12345.com
메시지: Connection error: HTTPSConnectionPool(host='nonexistent-domain-test-12345.com', port=443): Max retries exceeded...
상태: OPEN
발생 시각: 2025-11-08 07:45:26
================================================================================
```

#### 2-4. 데이터베이스 확인

**알림 생성 확인:**
```bash
sqlite3 notifications.db "SELECT id, alert_type, status, target_url FROM alerts;"
```

**예상 결과:**
```
1|ERROR|OPEN|https://nonexistent-domain-test-12345.com
```

**발송 로그 확인:**
```bash
sqlite3 notifications.db "SELECT alert_id, channel, status FROM notification_logs;"
```

**예상 결과:**
```
1|CONSOLE|SENT
```

✅ **테스트 통과**: 장애가 감지되고 알림이 발송되었습니다!

---

### 시나리오 3: 중복 알림 방지

**목적**: 동일한 장애에 대해 중복 알림이 발생하지 않는지 확인

#### 3-1. 30초 대기

Agent를 그대로 실행 상태로 두고 30초를 기다리세요. Agent가 다시 점검을 수행합니다.

#### 3-2. 백엔드 로그 확인

백엔드 터미널에서 다음 메시지를 확인하세요:

```
✅ 이벤트 저장 완료: event_id=4, url=https://nonexistent-domain-test-12345.com, success=False
ℹ️ 기존 알림 존재 (중복 방지): alert_id=1, url=https://nonexistent-domain-test-12345.com
```

#### 3-3. 알림 개수 확인

```bash
sqlite3 notifications.db "SELECT COUNT(*) FROM alerts WHERE target_url='https://nonexistent-domain-test-12345.com';"
```

**예상 결과:**
```
1
```

**이벤트는 계속 쌓이지만 알림은 1개만 유지됩니다:**

```bash
sqlite3 notifications.db "SELECT COUNT(*) FROM events WHERE target_url='https://nonexistent-domain-test-12345.com';"
```

**예상 결과:**
```
2  # 또는 3, 4... (점검 횟수만큼)
```

✅ **테스트 통과**: 중복 알림이 방지되었습니다!

---

### 시나리오 4: 복구 감지

**목적**: 서비스가 복구되었을 때 자동으로 감지하고 알림을 발송하는지 확인

#### 4-1. 정상 URL로 변경

**Agent를 중지하세요 (Ctrl+C)**

`.env` 파일을 수정:
```bash
TARGET_URL=https://www.google.com
```

Agent 재시작:
```bash
python agent.py
```

#### 4-2. 백엔드 로그 확인

백엔드 터미널에서 복구 알림을 확인하세요:

```
✅ 복구 감지: alert_id=1, url=https://nonexistent-domain-test-12345.com
================================================================================
✅ RECOVERY 알림
--------------------------------------------------------------------------------
대상 URL: https://nonexistent-domain-test-12345.com
메시지: 서비스가 정상 복구되었습니다.
상태: RESOLVED
발생 시각: 2025-11-08 07:46:31
해결 시각: 2025-11-08 07:46:31
================================================================================
```

#### 4-3. 알림 상태 확인

```bash
sqlite3 notifications.db "SELECT id, alert_type, status FROM alerts ORDER BY created_at;"
```

**예상 결과:**
```
1|ERROR|RESOLVED
2|RECOVERY|RESOLVED
```

✅ **테스트 통과**: 복구가 감지되고 기존 알림이 해결되었습니다!

---

## 🔍 시스템 모니터링 방법

### 실시간 로그 확인

**Agent 로그 (새 터미널):**
```bash
tail -f agent/agent.log
```

**백엔드 서버 로그 (새 터미널):**
```bash
tail -f backend/server.log
```

### 데이터베이스 조회

**최근 이벤트 조회:**
```bash
sqlite3 notifications.db "
  SELECT
    id,
    target_url,
    status_code,
    response_time_ms,
    is_success,
    datetime(timestamp, 'localtime') as time
  FROM events
  ORDER BY timestamp DESC
  LIMIT 10;
"
```

**OPEN 상태 알림 조회:**
```bash
sqlite3 notifications.db "
  SELECT
    id,
    alert_type,
    status,
    message,
    datetime(created_at, 'localtime') as created
  FROM alerts
  WHERE status = 'OPEN';
"
```

**알림 발송 통계:**
```bash
sqlite3 notifications.db "
  SELECT
    channel,
    status,
    COUNT(*) as count
  FROM notification_logs
  GROUP BY channel, status;
"
```

### API로 확인

**알림 목록 조회:**
```bash
curl -s http://localhost:5001/alerts | python -m json.tool
```

**OPEN 상태 알림만 조회:**
```bash
curl -s "http://localhost:5001/alerts?status=OPEN" | python -m json.tool
```

**발송 로그 조회:**
```bash
curl -s http://localhost:5001/notification_logs | python -m json.tool
```

---

## 🧪 추가 테스트 시나리오

### 404 에러 테스트

```bash
# .env 파일 수정
TARGET_URL=https://www.google.com/this-page-does-not-exist-404

# Agent 재시작 후 확인
```

**예상 결과**: HTTP 404 응답으로 ERROR 알림 발생

### 타임아웃 테스트

```bash
# .env 파일 수정
TARGET_URL=https://httpbin.org/delay/10

# Agent 재시작 후 확인
```

**예상 결과**: 5초 타임아웃으로 ERROR 알림 발생

### API 직접 호출 테스트

백엔드 API를 직접 호출하여 이벤트를 생성할 수 있습니다:

```bash
curl -X POST http://localhost:5001/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secret-key-12345" \
  -d '{
    "target_url": "https://test.example.com",
    "status_code": 500,
    "response_time_ms": 2000,
    "timestamp": "2025-11-08T10:00:00",
    "is_success": false,
    "error_message": "Internal Server Error"
  }'
```

---

## ⚙️ 설정 변경

### 점검 주기 변경

`.env` 파일에서 `CHECK_INTERVAL_SECONDS`를 수정:

```bash
# 10초마다 점검
CHECK_INTERVAL_SECONDS=10

# 1분마다 점검
CHECK_INTERVAL_SECONDS=60
```

### 포트 변경

`.env` 파일에서 포트를 변경:

```bash
# 백엔드 포트
FLASK_PORT=8080

# Agent도 같이 변경해야 함
BACKEND_URL=http://localhost:8080
```

### 여러 URL 동시 모니터링

현재는 단일 URL만 지원하지만, Agent를 여러 개 실행하여 여러 URL을 모니터링할 수 있습니다:

```bash
# 각 URL마다 별도의 .env 파일 생성
cp .env .env.service1
cp .env .env.service2

# service1용 Agent 실행
cd agent
export ENV_FILE=../.env.service1
python agent.py &

# service2용 Agent 실행
export ENV_FILE=../.env.service2
python agent.py &
```

---

## 🔔 텔레그램 봇 설정 (선택)

### 1단계: 텔레그램 봇 생성

1. 텔레그램에서 [@BotFather](https://t.me/botfather) 검색
2. `/newbot` 명령어 실행
3. 봇 이름 입력 (예: My Monitor Bot)
4. 봇 username 입력 (예: my_monitor_bot)
5. **API 토큰 받기** (예: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2단계: Chat ID 확인

1. 생성한 봇과 대화 시작 (아무 메시지나 보내기)
2. 브라우저에서 다음 URL 접속:
   ```
   https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
   ```
   (123456789:ABC... 부분을 본인의 토큰으로 교체)

3. 응답에서 `chat.id` 값 확인:
   ```json
   {
     "ok": true,
     "result": [{
       "message": {
         "chat": {
           "id": 987654321,  // 이 값이 Chat ID
           "first_name": "Your Name"
         }
       }
     }]
   }
   ```

### 3단계: 환경변수 설정

`.env` 파일에 추가:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

### 4단계: 백엔드 재시작

백엔드를 재시작하면 텔레그램 알림이 활성화됩니다.

**테스트**: 장애 URL로 변경하고 텔레그램 메시지 수신 확인

---

## 🛠️ 문제 해결

### 백엔드가 실행되지 않는 경우

**문제**: `Address already in use` 에러

**해결**:
```bash
# 포트 5001을 사용하는 프로세스 확인
lsof -i :5001

# 프로세스 종료
kill -9 <PID>

# 또는 .env에서 다른 포트로 변경
FLASK_PORT=5002
BACKEND_URL=http://localhost:5002
```

### Agent가 백엔드에 연결하지 못하는 경우

**문제**: `🔌 백엔드 연결 실패` 로그

**확인 사항**:
1. 백엔드 서버가 실행 중인지 확인
   ```bash
   curl http://localhost:5001/
   ```

2. `.env` 파일의 `BACKEND_URL`이 올바른지 확인
   ```bash
   cat .env | grep BACKEND_URL
   ```

3. API 키가 일치하는지 확인
   ```bash
   cat .env | grep API_KEY
   ```

### 데이터베이스가 없는 경우

**문제**: `no such table: events` 에러

**해결**:
```bash
cd backend
python init_db.py
```

### 로그 파일이 너무 큰 경우

**해결**:
```bash
# 로그 파일 비우기
> agent/agent.log
> backend/server.log

# 또는 삭제
rm agent/agent.log backend/server.log
```

### 데이터베이스 초기화

**모든 데이터를 삭제하고 처음부터 시작:**
```bash
rm notifications.db
cd backend
python init_db.py
cd ..
```

---

## 📊 프로젝트 구조

```
.
├── agent/                      # 모니터링 Agent
│   ├── agent.py               # Agent 메인 스크립트
│   ├── config.py              # 환경변수 관리
│   ├── logger.py              # 로그 설정
│   └── agent.log              # Agent 로그 (자동 생성)
│
├── backend/                    # Flask 백엔드 서버
│   ├── app.py                 # Flask 애플리케이션
│   ├── database.py            # SQLite 연결 및 쿼리
│   ├── models.py              # 데이터 모델 (Event, Alert, NotificationLog)
│   ├── init_db.py             # DB 초기화 스크립트
│   │
│   ├── api/
│   │   ├── events.py          # POST /events - 이벤트 수신
│   │   └── alerts.py          # GET /alerts - 알림 조회
│   │
│   ├── notifiers/
│   │   ├── base.py            # 알림 채널 베이스 클래스
│   │   ├── console.py         # 콘솔 출력 채널
│   │   └── telegram.py        # 텔레그램 봇 채널
│   │
│   └── server.log             # 서버 로그 (자동 생성)
│
├── notifications.db            # SQLite 데이터베이스
├── .env                        # 환경변수 설정
├── .env.example                # 환경변수 예시
├── requirements.txt            # Python 패키지 목록
├── README.md                   # 이 파일
└── VERIFICATION_REPORT.md      # 테스트 검증 리포트
```

---

## 📚 API 레퍼런스

### POST /events
이벤트 수신 및 저장

**Headers:**
```
Content-Type: application/json
X-API-Key: <API_KEY>
```

**Request Body:**
```json
{
  "target_url": "https://example.com",
  "status_code": 200,
  "response_time_ms": 150,
  "timestamp": "2025-11-08T10:00:00",
  "is_success": true,
  "error_message": null
}
```

**Response (201):**
```json
{
  "success": true,
  "event_id": 1
}
```

### GET /alerts
알림 목록 조회

**Query Parameters:**
- `status` (optional): OPEN, ACK, RESOLVED

**Response (200):**
```json
{
  "success": true,
  "count": 2,
  "alerts": [
    {
      "id": 1,
      "event_id": 3,
      "alert_type": "ERROR",
      "status": "OPEN",
      "created_at": "2025-11-08 07:45:26",
      "message": "Connection error...",
      "target_url": "https://example.com"
    }
  ]
}
```

### GET /alerts/:id
알림 상세 조회

**Response (200):**
```json
{
  "success": true,
  "alert": {...},
  "notification_logs": [
    {
      "id": 1,
      "alert_id": 1,
      "channel": "CONSOLE",
      "status": "SENT",
      "attempted_at": "2025-11-08 07:45:26"
    }
  ]
}
```

### PATCH /alerts/:id
알림 상태 변경

**Request Body:**
```json
{
  "status": "ACK"
}
```

**Response (200):**
```json
{
  "success": true,
  "alert": {...}
}
```

### GET /notification_logs
알림 발송 로그 조회

**Query Parameters:**
- `limit` (optional, default: 50): 조회할 로그 개수

**Response (200):**
```json
{
  "success": true,
  "count": 3,
  "logs": [...]
}
```

---

## 📝 라이센스

MIT License

---

## 👨‍💻 개발 정보

- **개발 환경**: Python 3.13, Flask 3.1.2, SQLite 3
- **테스트 완료**: 2025-11-08
- **상태**: ✅ 프로덕션 준비 완료

더 자세한 테스트 결과는 `VERIFICATION_REPORT.md`를 참고하세요.
