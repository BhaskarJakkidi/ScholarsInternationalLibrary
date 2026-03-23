import duckdb
import hashlib
import random

DB_FILE = "users.duckdb"

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin(username="admin", password="admin5312"):
    conn = duckdb.connect(DB_FILE)
    conn.execute("""CREATE SEQUENCE user_id_seq_no START 1;""")
    # Ensure table exists
    conn.execute("""
    CREATE TABLE IF NOT EXISTS auth_users (
        id INTEGER PRIMARY KEY  DEFAULT NEXTVAL('user_id_seq_no'),
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        mfa_secret TEXT NOT NULL
    )
    """)

    # Hash password
    password_hash = hash_password(password)

    # Generate a random 6-digit MFA code
    mfa_secret = str(random.randint(100000, 999999))

    # Insert admin user
    try:
        conn.execute(
            "INSERT INTO auth_users (username, password_hash, role, mfa_secret) VALUES (?, ?, ?, ?)",
            (username, password_hash, "admin", mfa_secret)
        )
        conn.commit()
        print(f"Admin user '{username}' created successfully.")
        print(f"Use this MFA code for login: {mfa_secret}")
    except duckdb.ConstraintException:
        print(f"User '{username}' already exists.")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
