import psycopg2
import hashlib
import random

# Connection details – adjust to your PostgreSQL setup
DB_CONFIG = {
    "dbname": "postgres",
    "user": "admin",
    "password": "admin1231",
    "host": "localhost",   # or your server IP
    "port": 5432
}

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin(username="admin", password="admin123"):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        mfa_secret TEXT NOT NULL
    );
    """)

    # Hash password
    password_hash = hash_password(password)

    # Generate a random 6-digit MFA code
    mfa_secret = str(random.randint(100000, 999999))

    # Insert admin user
    try:
        cursor.execute(
            "INSERT INTO auth_users (username, password_hash, role, mfa_secret) VALUES (%s, %s, %s, %s)",
            (username, password_hash, "admin", mfa_secret)
        )
        conn.commit()
        print(f"Admin user '{username}' created successfully.")
        print(f"Use this MFA code for login: {mfa_secret}")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print(f"User '{username}' already exists.")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_admin()
