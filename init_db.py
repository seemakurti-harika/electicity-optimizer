import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

# USERS TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    email TEXT,

    password TEXT

)
''')

# APPLIANCES TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS appliances (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    appliance_name TEXT,

    power REAL,

    hours REAL,

    units REAL,

    bill REAL

)
''')

conn.commit()
conn.close()

print("Database Created Successfully")