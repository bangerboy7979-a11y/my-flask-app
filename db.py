import sqlite3

conn = sqlite3.connect("database.db")

# ---------- USERS ----------
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    profile_pic TEXT
)
""")

# ---------- POSTS ----------
conn.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image TEXT,
    video TEXT,
    user TEXT,
    likes INTEGER DEFAULT 0
)
""")

# ---------- COMMENTS ----------
conn.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    user TEXT,
    text TEXT
)
""")

# ---------- FOLLOWERS ----------
conn.execute("""
CREATE TABLE IF NOT EXISTS followers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower TEXT,
    following TEXT
)
""")

# ---------- MESSAGES ----------
conn.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    text TEXT,
    image TEXT
)
""")

# 🔥 ---------- BLOCK TABLE (NEW) ----------
conn.execute("""
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    blocker TEXT,
    blocked TEXT
)
""")

conn.commit()
conn.close()

print("Database ready ✅")