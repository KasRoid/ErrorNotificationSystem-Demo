"""
데이터베이스 연결 및 쿼리 관리
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

# 데이터베이스 파일 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notifications.db')


@contextmanager
def get_db_connection():
    """데이터베이스 연결을 관리하는 컨텍스트 매니저"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> None:
    """쿼리 실행 (INSERT, UPDATE, DELETE)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)


def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """단일 행 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """여러 행 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def insert_and_get_id(query: str, params: tuple = ()) -> int:
    """데이터 삽입 후 자동 생성된 ID 반환"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid
