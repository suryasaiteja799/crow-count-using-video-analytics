import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

def add_column(cursor, table, column_def):
    print(f'Adding column: {column_def}')
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

def migrate():
    if not os.path.exists(DB_PATH):
        print('Database file not found:', DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    table = 'video_record'
    needed = [
        ("status", "status TEXT DEFAULT 'pending'"),
        ("error_message", "error_message TEXT"),
        ("processed_at", "processed_at DATETIME")
    ]

    for col, col_def in needed:
        if not column_exists(cur, table, col):
            try:
                add_column(cur, table, col_def)
                conn.commit()
                print(f'Column {col} added successfully')
            except Exception as e:
                print('Failed to add column', col, 'error:', e)
                print('Attempting table rebuild fallback')
                # Fallback: create new table, copy data
                cur.execute(f"PRAGMA table_info({table})")
                cols = [row[1] for row in cur.fetchall()]
                new_cols = cols + [c for c, _ in needed if c not in cols]
                cols_select = ','.join(cols)
                cur.execute('BEGIN TRANSACTION;')
                cur.execute(f"CREATE TABLE video_record_new ({', '.join([col + ' TEXT' for col in new_cols])})")
                cur.execute(f"INSERT INTO video_record_new({cols_select}) SELECT {cols_select} FROM {table}")
                cur.execute(f"DROP TABLE {table}")
                cur.execute(f"ALTER TABLE video_record_new RENAME TO {table}")
                conn.commit()
                print('Fallback rebuild completed')

    conn.close()

if __name__ == '__main__':
    migrate()
