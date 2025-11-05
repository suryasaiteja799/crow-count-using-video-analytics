import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), '..', 'data.db')
DB = os.path.abspath(DB)
if not os.path.exists(DB):
    print('data.db not found at', DB)
else:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(video_record)")
    rows = cur.fetchall()
    if not rows:
        print('video_record table not found or empty')
    else:
        print('video_record columns:')
        for r in rows:
            print(f" - {r[1]} (type:{r[2]})")
    conn.close()
