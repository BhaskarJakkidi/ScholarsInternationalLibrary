import os
import psycopg2
from urllib.parse import urlparse
import sys
import db_utils
# Connection details – scale to Render DATABASE_URL or local fallback
# def get_db_config():
#     database_url = os.getenv("DATABASE_URL")
#     DATABASE_URL="postgresql://postgres:TpqTueRhigoVZeNksTpfdIWggGWoircA@postgres.railway.internal:5432/railway"
                  
#     if database_url:
#         result = urlparse(database_url)
#         return {
#             "dbname": result.path.lstrip("/"),
#             "user": result.username,
#             "password": result.password,
#             "host": result.hostname,
#             "port": result.port,
#         }
#     return {
#         "dbname": "railway",
#         "user": "postgres",
#         "password": "TpqTueRhigoVZeNksTpfdIWggGWoircA",
#         "host": "crossover.proxy.rlwy.net",
#         "port": 30362,
#     }

DB_CONFIG = db_utils.get_db_config();

def setup_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create auth_users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,              -- e.g. 'admin' or 'staff'
            mfa_secret TEXT NOT NULL         -- secret key for MFA
        );
        """)

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            course TEXT,
            seat INTEGER,
            start_date DATE,
            active_status INTEGER DEFAULT 1,
            payment_plan TEXT,
            renewal_date DATE,
            payment_mode TEXT,
            remarks TEXT
        );
        """)

        # Create seats table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            id SERIAL PRIMARY KEY,
            total_seats INTEGER NOT NULL
        );
        """)

        # Initialize total seats = 110
        cursor.execute("DELETE FROM seats;")
        cursor.execute("INSERT INTO seats (total_seats) VALUES (110);")

        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] Tables created/verified successfully.", file=sys.stderr)
    except psycopg2.OperationalError as e:
        print(f"[DB ERROR] Cannot connect to database: {e}", file=sys.stderr)
        print("[DB WARNING] Using fallback mode. Database will be unavailable until connection is restored.", file=sys.stderr)
    except Exception as e:
        print(f"[DB ERROR] Unexpected error during setup: {e}", file=sys.stderr)