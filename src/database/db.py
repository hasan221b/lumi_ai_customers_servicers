import sqlite3
from datetime import datetime,timedelta

import os

DB_PATH = os.getenv("DB_PATH", "chatbot.db")  # Default to local, override on Render

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at DATETIME
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            chat_name TEXT,
            summary TEXT,
            created_at DATETIME,
            last_updated DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message_type TEXT,  -- 'sent' or 'received'
            message_text TEXT,
            timestamp DATETIME,
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
    ''')
    conn.commit()
    conn.close()

def cleanup_old_chats():
    conn = get_db_connection()
    cursor = conn.cursor()
    seven_days_ago = datetime.now() - timedelta(days=7)
    cursor.execute("DELETE FROM chats WHERE last_updated < ?", (seven_days_ago,))
    cursor.execute("DELETE FROM messages WHERE chat_id NOT IN (SELECT chat_id FROM chats)")
    conn.commit()
    conn.close()

init_db()