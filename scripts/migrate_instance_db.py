import sqlite3
import os

BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, '..', 'instance', 'data.db')
DB_PATH = os.path.abspath(DB_PATH)

if not os.path.exists(DB_PATH):
    print('instance data.db not found at', DB_PATH)
    raise SystemExit(0)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

needed = [
    ("status", "status TEXT DEFAULT 'pending'"),
    ("error_message", "error_message TEXT"),
    ("processed_at", "processed_at DATETIME")
]

for col, col_def in needed:
    if not column_exists(cur, 'video_record', col):
        try:
            print(f'Adding column {col} to instance/data.db')
            cur.execute(f"ALTER TABLE video_record ADD COLUMN {col_def}")
            conn.commit()
            print('Added', col)
        except Exception as e:
            print('Failed to add column', col, 'error:', e)
            print('Attempting fallback rebuild')
            cur.execute("PRAGMA table_info(video_record)")
            cols = [row[1] for row in cur.fetchall()]
            new_cols = cols + [c for c, _ in needed if c not in cols]
            cols_select = ','.join(cols)
            cur.execute('BEGIN TRANSACTION;')
            cur.execute(f"CREATE TABLE video_record_new ({', '.join([c + ' TEXT' for c in new_cols])})")
            cur.execute(f"INSERT INTO video_record_new({cols_select}) SELECT {cols_select} FROM video_record")
            cur.execute(f"DROP TABLE video_record")
            cur.execute(f"ALTER TABLE video_record_new RENAME TO video_record")
            conn.commit()
            print('Fallback complete')

conn.close()
print('Migration for instance/data.db finished')
