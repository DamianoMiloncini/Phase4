import sqlite3

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create the Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_id TEXT NOT NULL,
        username TEXT NOT NULL
    )
""")

# Insert preset data
preset_data = [
    ("53C7A80E", "Damiano"),
    ("53c7a8e", "Damiano2"),
]

cursor.executemany("INSERT INTO Users (rfid_id, username) VALUES (?, ?)", preset_data)
conn.commit()
conn.close()
