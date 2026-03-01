import sqlite3

def create_tables():
    conn = sqlite3.connect('heliosync.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            village TEXT NOT NULL,
            role TEXT NOT NULL,
            gender TEXT,
            is_new_technician INTEGER DEFAULT 0,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            issue TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            assigned_to INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            technician_id INTEGER NOT NULL,
            schedule_date TEXT NOT NULL,
            status TEXT DEFAULT 'Scheduled',
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (technician_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            from_role TEXT NOT NULL,
            to_id INTEGER NOT NULL,
            to_role TEXT NOT NULL,
            ticket_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            message TEXT,
            FOREIGN KEY (from_id) REFERENCES users (id),
            FOREIGN KEY (to_id) REFERENCES users (id),
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            technician_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (technician_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sos_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_id INTEGER NOT NULL,
        latitude REAL,
        longitude REAL,
        message TEXT DEFAULT 'Emergency SOS Alert',
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (technician_id) REFERENCES users (id)
    )
""")

    # Add gender column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")
        print("Added gender column")
    except sqlite3.OperationalError:
        print("Gender column already exists")

    # Add is_new_technician column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_new_technician INTEGER DEFAULT 0")
        print("Added is_new_technician column")
    except sqlite3.OperationalError:
        print("is_new_technician column already exists")

    conn.commit()
    conn.close()

def connect_db():
    return sqlite3.connect('heliosync.db')