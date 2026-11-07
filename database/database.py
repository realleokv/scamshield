import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS rpc_cache (
                    key TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    fetched_at REAL NOT NULL, expires_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY, wallet TEXT NOT NULL,
                    analyzed_at TEXT NOT NULL, created_at REAL NOT NULL,
                    report_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS quotas (
                    bucket TEXT PRIMARY KEY, count INTEGER NOT NULL,
                    expires_at REAL NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, key):
        with self.connect() as db:
            row = db.execute('SELECT payload,fetched_at FROM rpc_cache WHERE key=? AND expires_at>?', (key, time.time())).fetchone()
        return (json.loads(row[0]), row[1]) if row else None

    def put(self, key, payload, ttl):
        now = time.time()
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO rpc_cache VALUES (?,?,?,?)', (key, json.dumps(payload, ensure_ascii=False), now, now + ttl))
        return now

    def reserve(self, bucket, maximum, seconds):
        """Atomic fixed-window counter, also shared by WSGI threads."""
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT count,expires_at FROM quotas WHERE bucket=?', (bucket,)).fetchone()
            count, expiry = row if row and row[1] > now else (0, now + seconds)
            if count >= maximum:
                return False, max(1, int(expiry - now) + 1)
            db.execute('INSERT OR REPLACE INTO quotas VALUES (?,?,?)', (bucket, count + 1, expiry))
        return True, 0

    def save_report(self, report):
        with self.connect() as db:
            db.execute('INSERT INTO analysis_history (wallet,analyzed_at,created_at,report_json) VALUES (?,?,?,?)',
                       (report['wallet'], report['analyzed_at'], time.time(), json.dumps(report, ensure_ascii=False)))

    def cleanup(self):
        now = time.time()
        with self.connect() as db:
            db.execute('DELETE FROM rpc_cache WHERE expires_at<?', (now,))
            db.execute('DELETE FROM rpc_cache WHERE key NOT IN (SELECT key FROM rpc_cache ORDER BY fetched_at DESC LIMIT 2000)')
            db.execute('DELETE FROM quotas WHERE expires_at<?', (now,))
            db.execute('DELETE FROM analysis_history WHERE created_at<?', (now - 7 * 86400,))
            db.execute('DELETE FROM analysis_history WHERE id NOT IN (SELECT id FROM analysis_history ORDER BY id DESC LIMIT 500)')

