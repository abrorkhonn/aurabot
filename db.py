import sqlite3

def init_db():
    conn = sqlite3.connect("aura.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aura (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            aura INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def change_aura(user_id, username, delta):
    conn = sqlite3.connect("aura.db")
    cursor = conn.cursor()
    cursor.execute("SELECT aura FROM aura WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE aura SET aura = aura + ? WHERE user_id = ?", (delta, user_id))
    else:
        cursor.execute("INSERT INTO aura (user_id, username, aura) VALUES (?, ?, ?)", (user_id, username, delta))
    conn.commit()
    conn.close()

def get_aura(user_id):
    conn = sqlite3.connect("aura.db")
    cursor = conn.cursor()
    cursor.execute("SELECT aura FROM aura WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0
