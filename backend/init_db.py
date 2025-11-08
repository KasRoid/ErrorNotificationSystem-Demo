"""
데이터베이스 초기화 스크립트
SQLite 데이터베이스 및 테이블 생성
"""
import sqlite3
import os

# 데이터베이스 파일 경로 (프로젝트 루트)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notifications.db')


def create_tables():
    """테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # events 테이블: Agent가 전송한 모든 점검 결과
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_url TEXT NOT NULL,
            status_code INTEGER,
            response_time_ms INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_success BOOLEAN NOT NULL,
            error_message TEXT
        )
    """)

    # alerts 테이블: 생성된 알림 이벤트
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            alert_type TEXT NOT NULL,  -- ERROR, WARNING, RECOVERY
            status TEXT NOT NULL DEFAULT 'OPEN',  -- OPEN, ACK, RESOLVED
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            message TEXT NOT NULL,
            target_url TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    # notification_logs 테이블: 알림 발송 기록
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            channel TEXT NOT NULL,  -- CONSOLE, TELEGRAM, EMAIL
            status TEXT NOT NULL,  -- SENT, FAILED
            attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            response_code TEXT,
            message_id TEXT,
            retry_count INTEGER DEFAULT 0,
            error_message TEXT,
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        )
    """)

    # 인덱스 생성 (성능 최적화)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_target_url ON events(target_url)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_target_url ON alerts(target_url)")

    conn.commit()
    conn.close()

    print(f"✅ 데이터베이스 초기화 완료: {DB_PATH}")
    print("✅ 테이블 생성 완료:")
    print("   - events (점검 결과)")
    print("   - alerts (알림 이벤트)")
    print("   - notification_logs (발송 기록)")


def verify_tables():
    """테이블 생성 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("\n📋 생성된 테이블 목록:")
    for table in tables:
        print(f"   - {table[0]}")

    conn.close()


if __name__ == '__main__':
    print("🚀 데이터베이스 초기화 시작...")
    create_tables()
    verify_tables()
    print("\n✅ 모든 작업 완료!")
