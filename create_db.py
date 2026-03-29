import sqlite3

conn = sqlite3.connect("gradvox.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
rating INTEGER,
feedback TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully")