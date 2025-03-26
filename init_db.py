import sqlite3

# Connect to SQLite database (this will create the file if it doesn't exist)
conn = sqlite3.connect("expense_tracker.db")
cursor = conn.cursor()

# Drop existing tables if they exist
cursor.execute("DROP TABLE IF EXISTS expenses")
cursor.execute("DROP TABLE IF EXISTS users")

# Create users table
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# Create expenses table
cursor.execute('''
    CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database initialized successfully!")
