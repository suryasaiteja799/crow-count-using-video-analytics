import sqlite3
import os
import hashlib
import base64
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

def generate_password_hash(password: str, iterations: int = 260000, salt_length: int = 8) -> str:
    # create a hex salt (similar to werkzeug's token_hex behavior)
    salt = secrets.token_hex(salt_length)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    digest = base64.b64encode(dk).decode('ascii').rstrip('=')
    return f'pbkdf2:sha256:{iterations}${salt}${digest}'

def ensure_db():
    created = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create user table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT 0
    )
    ''')

    # Create video_record table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS video_record (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        filename TEXT NOT NULL,
        total_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        processed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()

    # Ensure default admin exists
    cur.execute("SELECT id FROM user WHERE email = ?", ('admin@local',))
    row = cur.fetchone()
    if not row:
        pw = 'adminpass'
        pw_hash = generate_password_hash(pw)
        cur.execute('INSERT INTO user (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                    ('Admin', 'admin@local', pw_hash, 1))
        conn.commit()
        print('Created default admin: admin@local / adminpass')
    else:
        print('Admin already present')

    conn.close()
    if created:
        print('Database created at', DB_PATH)
    else:
        print('Database exists at', DB_PATH)

if __name__ == '__main__':
    ensure_db()
