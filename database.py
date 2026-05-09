import sqlite3
import os

DB_NAME = 'fitai.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create User Profile table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            goal TEXT,
            activity_level TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Progress Log table
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            weight REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_profile(profile_data):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if a profile exists
    c.execute('SELECT id FROM user_profile LIMIT 1')
    row = c.fetchone()
    
    if row:
        # Update
        c.execute('''
            UPDATE user_profile 
            SET age=?, gender=?, height=?, weight=?, goal=?, activity_level=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (profile_data.get('age'), profile_data.get('gender'), profile_data.get('height'), 
              profile_data.get('weight'), profile_data.get('goal'), profile_data.get('activity_level'), row['id']))
    else:
        # Insert
        c.execute('''
            INSERT INTO user_profile (age, gender, height, weight, goal, activity_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (profile_data.get('age'), profile_data.get('gender'), profile_data.get('height'), 
              profile_data.get('weight'), profile_data.get('goal'), profile_data.get('activity_level')))
    
    conn.commit()
    conn.close()

def get_profile():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM user_profile LIMIT 1')
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def log_progress(date, weight, notes):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO progress_log (date, weight, notes)
        VALUES (?, ?, ?)
    ''', (date, weight, notes))
    conn.commit()
    conn.close()

def get_progress():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM progress_log ORDER BY date ASC')
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
