import sqlite3

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create the Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_id TEXT NOT NULL,
        username TEXT NOT NULL,
        light_threshold INTEGER,
        temperature_threshold INTEGER
    )
""")

# Insert preset data
preset_data = [
    ("53c7a8e", "Damiano", 28, 45),
]

#For dropping table
#drop_table_query = "DROP TABLE IF EXISTS Users;"

cursor.executemany("INSERT INTO Users (rfid_id, username, light_threshold, temperature_threshold) VALUES (?, ?, ?, ?)", preset_data)
# dropping table:
#cursor.execute(drop_table_query)
conn.commit()
conn.close()
