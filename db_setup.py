import duckdb

# Connect to a persistent DuckDB file
conn = duckdb.connect("library.duckdb")

# Create auth_users table
conn.execute("""
CREATE TABLE IF NOT EXISTS auth_users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,              -- e.g. 'admin' or 'staff'
    mfa_secret TEXT NOT NULL         -- secret key for MFA
);
""")

conn.execute("""DROP SEQUENCE IF EXISTS user_id_seq;""")
conn.execute("""CREATE SEQUENCE user_id_seq START 1;""")

# Create users table
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY DEFAULT NEXTVAL('user_id_seq'),
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    course TEXT,
    seat INTEGER ,
    start_date TEXT,
    active_status INTEGER DEFAULT 1,
    payment_plan TEXT,             
    renewal_date TEXT,
    payment_mode TEXT,
    remarks TEXT
);
""")

# Create seats table
conn.execute("""
CREATE TABLE IF NOT EXISTS seats (
    id INTEGER PRIMARY KEY,
    total_seats INTEGER NOT NULL
);
""")

# Initialize total seats = 110
conn.execute("DELETE FROM seats")
conn.execute("INSERT INTO seats (id,total_seats) VALUES (1,110)")

# Commit changes
conn.commit()
conn.close()
