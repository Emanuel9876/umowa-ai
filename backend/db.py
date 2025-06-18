import sqlite3
from datetime import datetime
import json

DB_PATH = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabela użytkowników
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    # Tabela analiz
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            result TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(user_id, text, result_dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    result_json = json.dumps(result_dict, ensure_ascii=False)
    c.execute('INSERT INTO analyses (user_id, text, result, date) VALUES (?, ?, ?, ?)',
              (user_id, text, result_json, datetime.now()))
    conn.commit()
    conn.close()

def get_analysis_history(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, result, date FROM analyses WHERE user_id = ? ORDER BY date DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    history = []
    for row in rows:
        result = json.loads(row[1])
        summary = result.get("summary", "")[:100]
        history.append({"id": row[0], "result": result, "date": row[2], "summary": summary})
    return history

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username, password_hash, role FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "password_hash": user[2], "role": user[3]}
    return None

def add_user(username, password_hash, role='user'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                  (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
