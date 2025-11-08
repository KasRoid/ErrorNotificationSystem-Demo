# 웹서비스 장애 알림 시스템 간단 구현 전략

**Purpose**: 최소 구성으로 실제 동작하는 알림 시스템 구현
**Project**: [[웹서비스 장애 알림 시스템 과제]]

---

## 🎯 구현 목표

**핵심**:
- URL 상태를 주기적으로 점검하는 수집 Agent
- 이벤트를 수신하고 알림을 발송하는 백엔드 서버
- 알림 발신 및 수신 확인 가능한 시스템
- **Docker 없이 Python 가상환경만으로 실행**

**검증 포인트**:
- Agent → 백엔드 데이터 전송 성공
- 장애 감지 시 알림 발송 (발신 확인)
- 알림 실제 수신 확인 (도착 증명)
- 중복 알림 방지 및 상태 관리

---

## 🛠️ 기술 스택 선택

### 수집 Agent: Python 스크립트

**선택 이유**:
- 간단한 HTTP 요청 및 스케줄링 (`requests`, `schedule` 라이브러리)
- 환경변수로 설정 관리 (`.env` 파일)
- 자체 로그 파일 생성 (`agent.log`)
- 별도 웹 프레임워크 불필요

### 백엔드 서버: Python (Flask)

**선택 이유**:
- `/events` REST API 엔드포인트 구현 간단
- 최소 코드로 이벤트 처리 및 알림 로직 구현
- 동기 처리로도 충분 (비동기 프레임워크 불필요)

### 데이터베이스: SQLite

**선택 이유**:
- 별도 설치 불필요 (Python 내장)
- 파일 기반으로 관리 간단 (`notifications.db` 파일 하나로 완결)
- 테이블 3개면 충분 (Events, Alerts, NotificationLogs)
- **서버형 DB(PostgreSQL/MySQL) 불필요 = Docker 컨테이너 불필요**

### 알림 채널: 콘솔 출력 (필수) + 텔레그램 봇 (선택)

**선택 이유**:
- 콘솔 출력: 설정 없이 즉시 확인 가능 (로그 파일에 기록)
- 텔레그램 봇: 무료, API 간단, 실제 메시지 수신 확인 가능
- 이메일/슬랙보다 설정이 간단함

---

## 📋 구현 단계 (6단계)

### STEP 1: 환경 준비 (Docker 없이 로컬 실행)

**목표**: Python 가상환경만으로 격리된 개발 환경 구성

**작업**:
1. Python 가상환경 생성 (`python -m venv venv`)
2. 가상환경 활성화 (`source venv/bin/activate`)
3. 필요한 패키지 설치
   - Flask (백엔드 서버)
   - requests (HTTP 요청)
   - python-dotenv (환경변수 관리)
   - schedule (주기적 작업)
   - [선택] python-telegram-bot (텔레그램 알림)

**Docker를 사용하지 않는 이유**:
- Python 가상환경만으로 충분한 격리 환경 제공
- SQLite는 파일 기반 DB로 컨테이너 불필요
- Agent와 서버를 로컬에서 바로 실행 가능
- 개발/디버깅 간편

**완료 기준**:
- 가상환경 활성화됨
- `pip list`에서 Flask, requests 확인
- `.env` 파일 생성 준비

---

### STEP 2: 데이터베이스 설계 및 초기화

**목표**: SQLite 데이터베이스에 테이블 생성 및 초기 설정

**테이블 구조**:

**events 테이블** (Agent가 전송한 모든 점검 결과):
- id (정수, 기본키, 자동증가)
- target_url (텍스트, 점검 대상 URL)
- status_code (정수, HTTP 응답 코드)
- response_time_ms (정수, 응답 시간 밀리초)
- timestamp (타임스탬프, 점검 시각)
- is_success (불린, 정상 여부)
- error_message (텍스트, 에러 메시지 - nullable)

**alerts 테이블** (생성된 알림 이벤트):
- id (정수, 기본키, 자동증가)
- event_id (정수, events.id 참조)
- alert_type (텍스트, ERROR/WARNING/RECOVERY)
- status (텍스트, OPEN/ACK/RESOLVED)
- created_at (타임스탬프)
- resolved_at (타임스탬프, nullable)
- message (텍스트, 알림 메시지)

**notification_logs 테이블** (알림 발송 기록):
- id (정수, 기본키, 자동증가)
- alert_id (정수, alerts.id 참조)
- channel (텍스트, CONSOLE/TELEGRAM/EMAIL 등)
- status (텍스트, SENT/FAILED)
- attempted_at (타임스탬프)
- response_code (텍스트, 결과 코드 - nullable)
- message_id (텍스트, 메시지 ID - nullable)
- retry_count (정수, 재시도 횟수)

**완료 기준**:
- `notifications.db` 파일 생성됨
- 3개 테이블 생성 확인
- 초기 데이터 없음 (Agent 실행 후 자동 수집)

---

### STEP 3: 수집 Agent 구현

**목표**: 대상 URL을 주기적으로 점검하고 백엔드로 데이터 전송

**구현 기능**:

1. **환경변수 설정** (`.env` 파일)
   ```env
   TARGET_URL=https://example.com
   CHECK_INTERVAL_SECONDS=30
   BACKEND_URL=http://localhost:5000
   API_KEY=your-secret-key
   ```

2. **URL 점검 로직**
   - `requests.get(TARGET_URL, timeout=5)`로 대상 URL 요청
   - 응답 코드, 응답 시간, 타임스탬프 수집
   - 타임아웃/네트워크 에러 처리

3. **백엔드 전송**
   - `/events` API로 POST 요청
   - 재시도 로직 (최대 3회, 지수 백오프)
   - 전송 실패 시 로컬 로그 기록

4. **자체 로그 기록**
   - `agent.log` 파일에 기록
   - 로그 포맷: `[timestamp] [LEVEL] message`
   - 전송 시도, 응답 코드, 실패 사유 기록

**완료 기준**:
- Agent가 주기적으로 URL 점검 (30초마다)
- `/events` API로 데이터 전송 성공
- `agent.log` 파일에 로그 기록 확인
- 네트워크 오류 시 재시도 동작 확인

---

### STEP 4: 백엔드 서버 구현

**목표**: 이벤트 수신, 장애 감지, 알림 발송

**구현할 API**:

1. **POST /events** (이벤트 수신)
   - 요청 검증 (API 키, 필수 필드)
   - events 테이블에 저장
   - 비정상 응답 감지 (status_code >= 400 or timeout)
   - 알림 이벤트 생성

2. **GET /alerts** (알림 목록 조회)
   - 상태별 필터링 (OPEN/ACK/RESOLVED)
   - 최근 알림부터 정렬

3. **PATCH /alerts/:id** (알림 상태 변경)
   - ACK (확인), RESOLVED (해결) 상태로 변경

**알림 로직 구현**:

1. **장애 감지 조건**
   - HTTP 상태 코드 >= 400
   - 타임아웃 발생
   - 네트워크 에러

2. **중복 알림 방지**
   - 동일 URL에 대해 OPEN 상태 알림이 있으면 새로 생성하지 않음
   - 연속 실패 횟수 카운트 (3회 이상 시 알림)

3. **알림 상태 관리**
   - OPEN: 새로 생성된 알림
   - ACK: 담당자가 확인함
   - RESOLVED: 정상 복구 확인됨

4. **복구 감지**
   - OPEN/ACK 상태 알림이 있을 때 정상 응답 수신 시
   - 자동으로 RESOLVED 상태로 변경
   - RECOVERY 타입 알림 발송

**완료 기준**:
- Flask 서버가 `http://localhost:5000`에서 실행됨
- `/events` API로 데이터 수신 및 저장 성공
- 비정상 응답 감지 시 alerts 테이블에 알림 생성
- 중복 알림 방지 동작 확인

---

### STEP 5: 알림 채널 구현

**목표**: 알림을 실제로 발송하고 수신 확인 가능한 채널 구현

**필수: 콘솔 출력 채널**

- 알림 발생 시 터미널에 출력
- 로그 파일에도 기록 (`server.log`)
- 출력 포맷:
  ```
  [2025-01-08 15:30:45] [ALERT] ERROR - https://example.com
  Status: 503 Service Unavailable
  Response Time: 5000ms
  Message: Service is down
  ```

**선택: 텔레그램 봇 채널**

1. **텔레그램 봇 생성**
   - BotFather에서 봇 생성 (`/newbot`)
   - API 토큰 발급

2. **환경변수 추가**
   ```env
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

3. **메시지 전송**
   - `python-telegram-bot` 라이브러리 사용
   - 알림 발생 시 텔레그램 메시지 전송
   - 메시지 포맷:
     ```
     🚨 서비스 장애 알림

     URL: https://example.com
     상태: 503 Service Unavailable
     응답시간: 5000ms
     발생시각: 2025-01-08 15:30:45
     ```

**NotificationLog 기록**:
- 모든 알림 시도를 notification_logs 테이블에 기록
- 발송 성공/실패 상태
- 재시도 횟수
- 텔레그램 메시지 ID (성공 시)

**완료 기준**:
- 콘솔에 알림 출력 확인
- `server.log` 파일에 알림 기록 확인
- [선택] 텔레그램 메시지 수신 확인
- notification_logs 테이블에 SENT/FAILED 기록 확인

---

### STEP 6: 통합 테스트 및 검증

**목표**: 전체 시스템 동작 확인 및 요구사항 검증

**테스트 시나리오**:

**시나리오 1: 정상 동작**
1. Agent가 정상 URL 점검 (예: https://google.com)
2. 200 응답 코드 수신
3. `/events` API로 전송
4. alerts 테이블에 알림 생성되지 않음

**시나리오 2: 장애 발생**
1. Agent가 비정상 URL 점검 (예: 존재하지 않는 URL)
2. 404 또는 타임아웃 발생
3. `/events` API로 전송
4. 백엔드가 장애 감지
5. alerts 테이블에 OPEN 상태 알림 생성
6. 콘솔에 알림 출력
7. [선택] 텔레그램 메시지 수신
8. notification_logs에 SENT 기록

**시나리오 3: 중복 알림 방지**
1. 동일 URL에 장애가 계속 발생
2. 이미 OPEN 상태 알림 존재
3. 새로운 알림 생성하지 않음
4. 기존 알림 유지

**시나리오 4: 복구 감지**
1. OPEN 상태 알림 존재
2. URL이 정상 복구됨
3. 백엔드가 복구 감지
4. 기존 알림 RESOLVED 상태로 변경
5. RECOVERY 타입 알림 발송

**검증 항목**:
- Agent 로그 확인 (`agent.log`)
- 서버 로그 확인 (`server.log`)
- events 테이블 데이터 확인
- alerts 테이블 상태 변경 확인
- notification_logs 테이블 발송 기록 확인
- 실제 알림 수신 확인 (콘솔 또는 텔레그램)

**완료 기준**:
- 모든 시나리오 통과
- 발신 확인 (notification_logs의 SENT/FAILED)
- 수신 확인 (콘솔 로그 또는 텔레그램 메시지)
- 중복 알림 방지 동작
- 복구 감지 및 상태 변경 동작

---

## 🎯 필수 구현 vs 선택 구현

### 필수 (과제 요구사항 충족)

**Agent**:
- ✅ 주기적 URL 점검
- ✅ /events API 전송
- ✅ 재시도 로직
- ✅ 자체 로그 기록

**Backend**:
- ✅ /events API 구현
- ✅ 데이터 검증 및 저장
- ✅ 장애 감지 및 알림 생성
- ✅ 중복 알림 방지
- ✅ 알림 상태 관리 (OPEN/ACK/RESOLVED)
- ✅ 콘솔 출력 채널
- ✅ NotificationLog 기록

**검증**:
- ✅ 발신 확인 (로그/DB)
- ✅ 수신 확인 (콘솔 로그)

### 선택 (추가 기능)

**Agent**:
- ⭐ 여러 URL 동시 모니터링
- ⭐ 응답 본문 검증 (특정 문자열 포함 확인)
- ⭐ 메트릭 수집 (평균 응답 시간 등)

**Backend**:
- ⭐ 텔레그램 봇 채널
- ⭐ 이메일 채널
- ⭐ 웹훅 채널
- ⭐ 알림 규칙 설정 (연속 N회 실패 시 알림)
- ⭐ 대시보드 UI (Flask + HTML/CSS)
- ⭐ API 문서 (Swagger)

---

## 📂 프로젝트 구조

### 전체 구조

```text
notification-system/
├── agent/
│   ├── agent.py              # Agent 메인 스크립트
│   ├── config.py             # 설정 관리
│   ├── logger.py             # 로그 설정
│   └── agent.log             # Agent 로그 파일
├── backend/
│   ├── app.py                # Flask 서버 엔트리
│   ├── database.py           # SQLite 초기화 및 쿼리
│   ├── models.py             # 데이터 모델
│   ├── api/
│   │   ├── events.py         # /events API
│   │   └── alerts.py         # /alerts API
│   ├── notifiers/
│   │   ├── base.py           # 알림 채널 인터페이스
│   │   ├── console.py        # 콘솔 출력 채널
│   │   └── telegram.py       # 텔레그램 채널 (선택)
│   ├── init_db.py            # DB 테이블 생성
│   └── server.log            # 서버 로그 파일
├── notifications.db          # SQLite 데이터베이스
├── .env                      # 환경변수 (gitignore)
├── .env.example              # 환경변수 예시
├── requirements.txt          # 패키지 목록
└── README.md                 # 실행 방법
```

### 핵심 파일 설명

**agent/agent.py**:
- URL 점검 로직
- 스케줄링 (30초마다)
- /events API 전송
- 재시도 로직

**backend/app.py**:
- Flask 서버 초기화
- API 라우트 등록
- 알림 트리거 로직

**backend/notifiers/console.py**:
- 콘솔 출력 및 로그 파일 기록
- NotificationLog 저장

**backend/init_db.py**:
- 테이블 생성 SQL 실행
- 초기 데이터 없음 (Agent가 수집)

---

## 🚀 실행 순서 (Docker 없이 로컬 실행)

### 1. 환경 준비

```bash
# 1. Python 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install flask requests python-dotenv schedule

# [선택] 텔레그램 봇 사용 시
pip install python-telegram-bot

# 3. requirements.txt 생성 (재현성)
pip freeze > requirements.txt
```

### 2. 환경변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
# Agent 설정
TARGET_URL=https://example.com
CHECK_INTERVAL_SECONDS=30
BACKEND_URL=http://localhost:5000
API_KEY=my-secret-key-12345

# Backend 설정
FLASK_PORT=5000
FLASK_DEBUG=true

# [선택] 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
EOF
```

### 3. 데이터베이스 초기화

```bash
# SQLite DB 생성 및 테이블 생성
cd backend
python init_db.py

# → notifications.db 파일 생성됨
# → 테이블 3개 생성됨 (events, alerts, notification_logs)
```

### 4. 백엔드 서버 실행

```bash
# 백엔드 서버 실행 (터미널 1)
cd backend
python app.py

# → http://localhost:5000 에서 실행 중
# → /events API 대기 중
```

### 5. Agent 실행

```bash
# Agent 실행 (터미널 2)
cd agent
python agent.py

# → 30초마다 URL 점검
# → /events API로 데이터 전송
# → agent.log에 로그 기록
```

### 6. 동작 확인

```bash
# events 테이블 확인
sqlite3 notifications.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 5;"

# alerts 테이블 확인
sqlite3 notifications.db "SELECT * FROM alerts WHERE status='OPEN';"

# notification_logs 확인
sqlite3 notifications.db "SELECT * FROM notification_logs ORDER BY attempted_at DESC LIMIT 5;"

# 서버 로그 확인
tail -f backend/server.log

# Agent 로그 확인
tail -f agent/agent.log
```

---

## ✅ 검증 체크리스트

### Agent 검증

- [ ] Agent가 주기적으로 실행됨 (30초마다)
- [ ] URL 점검 성공 (정상 URL)
- [ ] URL 점검 실패 감지 (비정상 URL)
- [ ] `/events` API로 데이터 전송 성공
- [ ] 재시도 로직 동작 (네트워크 오류 시)
- [ ] `agent.log`에 전송 시도 기록됨
- [ ] `agent.log`에 실패 사유 기록됨

### Backend 검증

- [ ] Flask 서버가 정상 실행됨 (`http://localhost:5000`)
- [ ] `/events` API로 데이터 수신 및 저장 성공
- [ ] events 테이블에 데이터 존재
- [ ] 비정상 응답 감지 시 alerts 생성
- [ ] 중복 알림 방지 동작 (OPEN 상태 알림 존재 시)
- [ ] 복구 감지 시 RESOLVED 상태 변경
- [ ] 콘솔에 알림 출력됨
- [ ] notification_logs에 SENT/FAILED 기록
- [ ] [선택] 텔레그램 메시지 수신됨

### 발신 확인 (과제 요구사항)

- [ ] `server.log`에 알림 발송 기록 존재
- [ ] notification_logs 테이블에 SENT 상태 기록
- [ ] 재시도 시 retry_count 증가 확인
- [ ] 실패 시 FAILED 상태 및 에러 메시지 기록

### 수신 확인 (과제 요구사항)

- [ ] 콘솔 출력으로 알림 메시지 확인 가능
- [ ] `server.log` 파일에 알림 메시지 기록됨
- [ ] [선택] 텔레그램 메시지 스크린샷 캡처
- [ ] [선택] 텔레그램 message_id 기록 확인

### 상태 관리 검증

- [ ] OPEN 상태 알림 생성
- [ ] ACK 상태로 변경 가능 (API 호출)
- [ ] RESOLVED 상태로 자동 변경 (복구 감지)
- [ ] 상태별 알림 목록 조회 가능

---

## 📊 예상 결과

### 정상 동작 시나리오

**시간 0초**:
- Agent가 `https://google.com` 점검
- 응답 코드: 200, 응답 시간: 150ms
- `/events` API 전송
- events 테이블에 저장 (is_success=true)
- 알림 생성 안 됨

**시간 30초**:
- Agent가 `https://nonexistent-site-12345.com` 점검
- 타임아웃 발생
- `/events` API 전송
- events 테이블에 저장 (is_success=false)
- alerts 테이블에 OPEN 상태 알림 생성
- 콘솔 출력:
  ```
  [2025-01-08 15:31:00] [ALERT] ERROR - https://nonexistent-site-12345.com
  Status: Timeout
  Message: Request timed out after 5000ms
  ```
- notification_logs에 SENT 기록
- [선택] 텔레그램 메시지 발송

**시간 60초**:
- Agent가 동일 URL 다시 점검
- 여전히 타임아웃
- `/events` API 전송
- 중복 알림 방지 (기존 OPEN 알림 유지)
- 새로운 알림 생성 안 됨

**시간 90초**:
- URL 복구됨 (200 응답)
- `/events` API 전송
- 백엔드가 복구 감지
- 기존 알림 RESOLVED 상태로 변경
- RECOVERY 타입 알림 발송
- 콘솔 출력:
  ```
  [2025-01-08 15:32:30] [ALERT] RECOVERY - https://nonexistent-site-12345.com
  Status: 200 OK
  Message: Service has been recovered
  ```

### 데이터베이스 예시

**events 테이블**:
```
id | target_url              | status_code | response_time_ms | timestamp           | is_success
1  | https://google.com      | 200         | 150              | 2025-01-08 15:30:00 | 1
2  | https://nonexist...com  | NULL        | 5000             | 2025-01-08 15:30:30 | 0
3  | https://nonexist...com  | NULL        | 5000             | 2025-01-08 15:31:00 | 0
4  | https://nonexist...com  | 200         | 200              | 2025-01-08 15:31:30 | 1
```

**alerts 테이블**:
```
id | event_id | alert_type | status   | created_at          | resolved_at         | message
1  | 2        | ERROR      | RESOLVED | 2025-01-08 15:30:30 | 2025-01-08 15:31:30 | Service is down
```

**notification_logs 테이블**:
```
id | alert_id | channel  | status | attempted_at        | retry_count | message_id
1  | 1        | CONSOLE  | SENT   | 2025-01-08 15:30:30 | 0           | NULL
2  | 1        | TELEGRAM | SENT   | 2025-01-08 15:30:31 | 0           | 12345
3  | 1        | CONSOLE  | SENT   | 2025-01-08 15:31:30 | 0           | NULL
```

---

## 🎓 학습 포인트

### 모니터링 시스템 핵심 개념

**이벤트 수집**:
- 주기적 점검 (Polling)
- 메트릭 수집 (응답 코드, 지연 시간)
- 에러 핸들링 및 재시도

**장애 감지**:
- 임계값 기반 감지 (status_code >= 400)
- 연속 실패 카운팅
- 복구 감지

**알림 관리**:
- 중복 알림 방지
- 상태 전이 (OPEN → ACK → RESOLVED)
- 알림 채널 추상화 (다양한 채널 지원)

### 실무 적용 시나리오

**확장 가능한 구조**:
- 알림 채널 인터페이스 → 쉽게 새 채널 추가
- SQLite → PostgreSQL로 교체 가능
- 단일 URL → 다중 URL 모니터링 확장

**운영 고려사항**:
- 로그 로테이션 (용량 관리)
- 알림 빈도 제어 (알림 피로도 방지)
- 에스컬레이션 정책 (심각도별 다른 채널)

**성능 최적화**:
- 비동기 처리 (asyncio, Celery)
- 배치 처리 (여러 이벤트 한 번에 처리)
- 캐싱 (중복 감지 성능 개선)

---

## 🔗 참고 자료

- **Flask 공식 문서**: https://flask.palletsprojects.com/
- **Requests 라이브러리**: https://requests.readthedocs.io/
- **Python Schedule**: https://schedule.readthedocs.io/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **SQLite**: https://www.sqlite.org/

---

## 📝 다음 단계 (선택)

실습 완료 후 추가로 학습하고 싶다면:

1. **알림 규칙 엔진** (연속 N회 실패, 특정 시간대만 알림 등)
2. **대시보드 UI** (Flask + Chart.js로 모니터링 현황 시각화)
3. **메트릭 집계** (평균 응답 시간, 가동률 계산)
4. **웹훅 채널** (외부 시스템 연동)
5. **다중 Agent** (여러 서버에서 동시 모니터링)
6. **API 인증** (JWT 기반 인증)
7. **Docker 컨테이너화** (프로덕션 배포)
8. **Kubernetes 배포** (스케일 아웃)

---

_Tags: #monitoring #alerting #flask #python #실습 #간단구현 #로컬서버_
