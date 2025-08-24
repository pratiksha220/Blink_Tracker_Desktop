# local_queue.py
import sqlite3
import json
from pathlib import Path

DB_PATH = Path("local_sync_queue.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY,
        payload TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) 
    """)
    conn.commit()
    conn.close()

def enqueue(item: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO queue (payload) VALUES (?)", (json.dumps(item),))
    conn.commit()
    conn.close()

def fetch_batch(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, payload FROM queue ORDER BY id LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [(r[0], json.loads(r[1])) for r in rows]

def delete_ids(ids):
    if not ids:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM queue WHERE id IN ({})".format(",".join("?"*len(ids))), ids)
    conn.commit()
    conn.close()
def delete_all():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM queue")
    conn.commit()
    conn.close()