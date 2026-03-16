"""
PhishGuard AI - Database Management Module
SQLite database for logging scan results and user management
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from threading import Lock

DB_FILE = os.path.join(os.path.dirname(__file__), 'phishguard.db')
db_lock = Lock()


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def initialize_database():
    """Initialize database tables if they don't exist."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # scan_results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    result TEXT NOT NULL,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT
                )
            ''')
            
            # users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    ip_address TEXT NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # banned_users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    ban_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scan_results_time 
                ON scan_results(scan_time DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scan_results_user 
                ON scan_results(user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_status 
                ON users(status)
            ''')


def log_scan_result(url, risk_score, result, source, user_id=None, ip_address=None):
    """Log a scan result to the database."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_results 
                (url, risk_score, result, source, user_id, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, risk_score, result, source, user_id, ip_address))


def track_user(user_id, ip_address):
    """Track or update user activity."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                # Update existing user
                cursor.execute('''
                    UPDATE users 
                    SET request_count = request_count + 1, 
                        last_seen = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
            else:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (user_id, ip_address, request_count)
                    VALUES (?, ?, 1)
                ''', (user_id, ip_address))


def is_user_banned(user_id):
    """Check if a user is banned."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None


def get_stats():
    """Get statistics about scans."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total scans
            cursor.execute('SELECT COUNT(*) as count FROM scan_results')
            total_scans = cursor.fetchone()['count']
            
            # Phishing detections
            cursor.execute("SELECT COUNT(*) as count FROM scan_results WHERE result = 'Phishing'")
            phishing_count = cursor.fetchone()['count']
            
            # Safe detections
            cursor.execute("SELECT COUNT(*) as count FROM scan_results WHERE result = 'Safe'")
            safe_count = cursor.fetchone()['count']
            
            # Active users
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE status = 'active'")
            active_users = cursor.fetchone()['count']
            
            return {
                'total_scans': total_scans,
                'phishing_detections': phishing_count,
                'safe_detections': safe_count,
                'active_users': active_users,
                'system_status': 'OPERATIONAL'
            }


def get_recent_scans(limit=50):
    """Get recent scan results."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, url, risk_score, result, scan_time, source 
                FROM scan_results 
                ORDER BY scan_time DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]


def get_users(limit=100):
    """Get all users."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, ip_address, request_count, status, 
                       first_seen, last_seen 
                FROM users 
                ORDER BY last_seen DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]


def get_banned_users(limit=100):
    """Get all banned users."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, ip_address, ban_time, reason 
                FROM banned_users 
                ORDER BY ban_time DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]


def ban_user(user_id, reason=None):
    """Ban a user."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get user's IP address
            cursor.execute('SELECT ip_address FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            ip_address = result['ip_address'] if result else 'unknown'
            
            # Add to banned_users
            cursor.execute('''
                INSERT INTO banned_users (user_id, ip_address, reason)
                VALUES (?, ?, ?)
            ''', (user_id, ip_address, reason))
            
            # Update user status
            cursor.execute('''
                UPDATE users SET status = 'banned' WHERE user_id = ?
            ''', (user_id,))


def unban_user(user_id):
    """Unban a user."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Remove from banned_users
            cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
            
            # Update user status
            cursor.execute('''
                UPDATE users SET status = 'active' WHERE user_id = ?
            ''', (user_id,))


def get_detection_stats():
    """Get detection stats for the last 7 days by detection type."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    result,
                    COUNT(*) as count,
                    DATE(scan_time) as date
                FROM scan_results
                WHERE scan_time >= datetime('now', '-7 days')
                GROUP BY result, DATE(scan_time)
                ORDER BY date ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]


def get_scan_history(user_id, limit=50):
    """Get scan history for a specific user."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, url, risk_score, result, scan_time, source 
                FROM scan_results 
                WHERE user_id = ? 
                ORDER BY scan_time DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]


def clear_old_logs(days=30):
    """Delete scan logs older than specified days."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM scan_results 
                WHERE scan_time < datetime('now', '-' || ? || ' days')
            ''', (days,))
