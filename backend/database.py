import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# 데이터베이스 파일 경로
DB_FILE = "routine_database.db"

def get_db_connection():
    """데이터베이스 연결 생성"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn

def init_database():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 기록 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            activity TEXT NOT NULL,
            category TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            memo TEXT,
            date TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 인덱스 생성 (검색 성능 향상)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_date ON records(date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_category ON records(category)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON records(timestamp)
    """)
    
    conn.commit()
    conn.close()

def add_record(activity: str, category: str, start_time: str, end_time: str, memo: str = "", record_date: str = None) -> bool:
    """
    새 기록 추가
    
    Args:
        activity: 활동/루틴 이름
        category: 카테고리
        start_time: 시작 시간 (HH:MM 형식)
        end_time: 종료 시간 (HH:MM 형식)
        memo: 메모 (선택)
        record_date: 기록 날짜 (YYYY-MM-DD 형식, 선택 - 기본값: 오늘)
    
    Returns:
        bool: 성공 여부
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        record_id = f"record_{datetime.now().timestamp()}_{len(get_all_records())}"
        if record_date is None:
            date = datetime.now().date().isoformat()
        else:
            date = record_date
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO records (id, activity, category, start_time, end_time, memo, date, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, activity, category, start_time, end_time, memo, date, timestamp))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"기록 추가 오류: {e}")
        return False

def get_all_records() -> List[Dict]:
    """모든 기록 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM records
            ORDER BY timestamp DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"기록 조회 오류: {e}")
        return []

def get_records_by_date(date: str) -> List[Dict]:
    """
    특정 날짜의 기록 조회
    
    Args:
        date: 날짜 (YYYY-MM-DD 형식)
    
    Returns:
        List[Dict]: 해당 날짜의 기록 목록
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM records
            WHERE date = ?
            ORDER BY start_time ASC
        """, (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"날짜별 기록 조회 오류: {e}")
        return []

def get_records_by_category(category: str) -> List[Dict]:
    """
    특정 카테고리의 기록 조회
    
    Args:
        category: 카테고리명
    
    Returns:
        List[Dict]: 해당 카테고리의 기록 목록
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM records
            WHERE category = ?
            ORDER BY timestamp DESC
        """, (category,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"카테고리별 기록 조회 오류: {e}")
        return []

def get_records_by_date_range(start_date: str, end_date: str) -> List[Dict]:
    """
    날짜 범위의 기록 조회
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    
    Returns:
        List[Dict]: 해당 기간의 기록 목록
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM records
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, start_time ASC
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"기간별 기록 조회 오류: {e}")
        return []

def delete_record(record_id: str) -> bool:
    """
    기록 삭제
    
    Args:
        record_id: 기록 ID
    
    Returns:
        bool: 성공 여부
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 삭제 전에 기록이 존재하는지 확인
        cursor.execute("SELECT id FROM records WHERE id = ?", (record_id,))
        if not cursor.fetchone():
            conn.close()
            print(f"기록을 찾을 수 없습니다: {record_id}")
            return False
        
        # 기록 삭제
        cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
        
        # 삭제 확인
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            print(f"기록이 성공적으로 삭제되었습니다: {record_id}")
            return True
        else:
            print(f"기록 삭제 실패: {record_id}")
            return False
    except Exception as e:
        print(f"기록 삭제 오류: {e}")
        return False

def update_record(record_id: str, activity: str = None, category: str = None, 
                  start_time: str = None, end_time: str = None, memo: str = None) -> bool:
    """
    기록 수정
    
    Args:
        record_id: 기록 ID
        activity: 활동명 (선택)
        category: 카테고리 (선택)
        start_time: 시작 시간 (선택)
        end_time: 종료 시간 (선택)
        memo: 메모 (선택)
    
    Returns:
        bool: 성공 여부
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if activity:
            updates.append("activity = ?")
            values.append(activity)
        if category:
            updates.append("category = ?")
            values.append(category)
        if start_time:
            updates.append("start_time = ?")
            values.append(start_time)
        if end_time:
            updates.append("end_time = ?")
            values.append(end_time)
        if memo is not None:
            updates.append("memo = ?")
            values.append(memo)
        
        if not updates:
            return False
        
        values.append(record_id)
        query = f"UPDATE records SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"기록 수정 오류: {e}")
        return False

def get_statistics(start_date: str = None, end_date: str = None) -> Dict:
    """
    통계 정보 조회
    
    Args:
        start_date: 시작 날짜 (선택)
        end_date: 종료 날짜 (선택)
    
    Returns:
        Dict: 통계 정보
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 기본 쿼리
        base_query = "SELECT * FROM records"
        conditions = []
        params = []
        
        if start_date and end_date:
            conditions.append("date BETWEEN ? AND ?")
            params.extend([start_date, end_date])
        elif start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        elif end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        
        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 전체 기록 수
        cursor.execute(f"SELECT COUNT(*) FROM records{where_clause}", params)
        total_count = cursor.fetchone()[0]
        
        # 카테고리별 통계
        cursor.execute(f"""
            SELECT category, COUNT(*) as count
            FROM records{where_clause}
            GROUP BY category
            ORDER BY count DESC
        """, params)
        
        category_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 날짜별 통계
        cursor.execute(f"""
            SELECT date, COUNT(*) as count
            FROM records{where_clause}
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """, params)
        
        date_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_records": total_count,
            "category_stats": category_stats,
            "date_stats": date_stats
        }
    except Exception as e:
        print(f"통계 조회 오류: {e}")
        return {
            "total_records": 0,
            "category_stats": {},
            "date_stats": {}
        }

def migrate_from_json(json_file: str = "daily_records.json") -> int:
    """
    JSON 파일에서 데이터베이스로 마이그레이션
    
    Args:
        json_file: JSON 파일 경로
    
    Returns:
        int: 마이그레이션된 기록 수
    """
    if not os.path.exists(json_file):
        return 0
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            records = data.get('records', [])
        
        migrated_count = 0
        for record in records:
            # 기존 데이터 형식에 맞춰 변환
            activity = record.get('activity', '')
            category = record.get('category', '기타')
            
            # 시간 처리 (기존 형식: "HH:MM" 또는 "HH:MM - HH:MM")
            time_str = record.get('time', '')
            if ' - ' in time_str:
                start_time, end_time = time_str.split(' - ', 1)
            else:
                start_time = time_str
                end_time = time_str
            
            # start_time, end_time 필드가 있으면 사용
            if 'start_time' in record:
                start_time = record.get('start_time', start_time)
            if 'end_time' in record:
                end_time = record.get('end_time', end_time)
            
            memo = record.get('memo', '')
            date = record.get('date', datetime.now().date().isoformat())
            
            # 중복 체크 (같은 날짜, 같은 활동, 같은 시간)
            existing = get_records_by_date(date)
            is_duplicate = any(
                r.get('activity') == activity and 
                r.get('start_time') == start_time and
                r.get('end_time') == end_time
                for r in existing
            )
            
            if not is_duplicate:
                record_id = record.get('id', f"migrated_{datetime.now().timestamp()}_{migrated_count}")
                timestamp = record.get('timestamp', datetime.now().isoformat())
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        INSERT INTO records (id, activity, category, start_time, end_time, memo, date, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (record_id, activity, category, start_time, end_time, memo, date, timestamp))
                    
                    conn.commit()
                    migrated_count += 1
                except sqlite3.IntegrityError:
                    # 중복 ID인 경우 스킵
                    pass
                finally:
                    conn.close()
        
        return migrated_count
    except Exception as e:
        print(f"마이그레이션 오류: {e}")
        return 0

# 데이터베이스 초기화
init_database()
