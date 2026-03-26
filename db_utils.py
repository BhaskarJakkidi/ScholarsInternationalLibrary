import os
import psycopg2
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime, timedelta

# Connection details – scale to Render DATABASE_URL or local fallback
def get_db_config():
    database_url = os.getenv("DATABASE_URL")
    DATABASE_URL="DATABASE_URL=postgresql://postgres:TpqTueRhigoVZeNksTpfdIWggGWoircA@crossover.proxy.rlwy.net:30362/railway"
    if database_url:
        result = urlparse(database_url)
        return {
            "dbname": result.path.lstrip("/"),
            "user": result.username,
            "password": result.password,
            "host": result.hostname,
            "port": result.port,
        }
    return {
        "dbname": "railway",
        "user": "postgres",
        "password": "TpqTueRhigoVZeNksTpfdIWggGWoircA",
        "host": "crossover.proxy.rlwy.net",
        "port": 30362,
    }

DB_CONFIG = get_db_config()

def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def register_user(name, phone, email, course, seat, plan, start_date, payment_mode):
    conn = connect_db()
    cursor = conn.cursor()

    # Prevent duplicate seat allocation
    cursor.execute("SELECT COUNT(*) FROM users WHERE seat=%s AND active_status=1", (seat,))
    result = cursor.fetchone()
    if result[0] > 0:
        conn.close()
        return False, f"Seat {seat} is already assigned."

    # Calculate renewal date
    if plan == "15 days":
        renewal = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=15)
    elif plan == "1 month":
        renewal = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=30)
    else:
        renewal = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=90)

    cursor.execute("""
        INSERT INTO users (name, phone, email, course, seat, start_date, active_status, payment_plan, renewal_date, payment_mode)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, phone, email, course, seat, start_date, 1, plan, renewal.strftime("%Y-%m-%d"), payment_mode))

    conn.commit()
    conn.close()
    return True, f"User {name} registered successfully!"

def change_seat(user_id, new_seat):
    conn = connect_db()
    cursor = conn.cursor()

    # Cast to plain Python int
    user_id = int(user_id)

    new_seat = int(new_seat)
    cursor.execute("SELECT COUNT(*) FROM users WHERE seat=%s AND id!=%s", (new_seat, user_id))
    result = cursor.fetchone()
    
    if result[0] > 0:
        conn.close()
        return False, f"Seat {new_seat} is already taken."

    cursor.execute("UPDATE users SET seat=%s WHERE id=%s", (new_seat, user_id))
    conn.commit()
    conn.close()
    return True, "Seat updated successfully!"

def get_user_details():
    conn = connect_db()
    query = """
        SELECT  name, phone, seat, start_date, renewal_date,active_status,payment_plan,payment_mode
        FROM users where active_status=1
        ORDER BY seat asc
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def deactivate_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Cast to plain Python int
    user_id = int(user_id)
    cursor.execute("UPDATE users SET active_status=0 WHERE id=%s", (user_id,))
    conn.commit()
    conn.close()
    return True, "User deactivated successfully!"

def activate_user(user_id, start_date, plan, payment_mode, remarks, seat):
    conn = connect_db()
    cursor = conn.cursor()
    # Cast to plain Python int
    user_id = int(user_id)
    seat = int(seat)

    # Prevent duplicate seat allocation for active users
    cursor.execute("SELECT COUNT(*) FROM users WHERE seat=%s AND active_status=1 AND id!=%s", (seat, user_id))
    result = cursor.fetchone()
    if result[0] > 0:
        conn.close()
        return False, f"Seat {seat} is already assigned to another active user."
    # Calculate renewal date
    if plan == "15 days":
        renewal = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=15)
    elif plan == "1 month":
        renewal = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=30)
    else:
        renewal = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=90)
    cursor.execute(
        "UPDATE users SET active_status=1, start_date=%s, payment_plan=%s, remarks=%s, payment_mode=%s, seat=%s, renewal_date=%s WHERE id=%s",
        (start_date, plan, remarks, payment_mode, seat, renewal, user_id)
    )
    conn.commit()
    conn.close()
    return True, "User activated successfully!"

def get_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users order by seat asc")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_total_seats():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT total_seats FROM seats LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_upcoming_renewals():
    days = 3
    conn = connect_db()
    cursor = conn.cursor()
    cutoff_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT id, name, phone, seat, renewal_date, payment_mode, payment_plan
        FROM users
        WHERE renewal_date IS NOT NULL
        AND DATE(renewal_date) <= DATE(%s) AND active_status=1
        ORDER BY seat ASC
    """, (cutoff_date,))
    results = cursor.fetchall()
    conn.close()
    return results

def update_renewal(user_id, plan, payment_mode, renewal_date):
    conn = connect_db()
    cursor = conn.cursor()
    if isinstance(renewal_date, str):
        renewal_date = datetime.strptime(renewal_date, "%Y-%m-%d")

    if plan == "15 days":
        new_date = renewal_date + timedelta(days=15)
    elif plan == "1 month":
        new_date = renewal_date + timedelta(days=30)
    elif plan == "3 months":
        new_date = renewal_date + timedelta(days=90)
    else:
        new_date = datetime.now()

    cursor.execute("""
        UPDATE users
        SET renewal_date=%s, payment_mode=%s, payment_plan=%s
        WHERE id=%s
    """, (new_date.strftime("%Y-%m-%d"), payment_mode, plan, user_id))
    conn.commit()
    conn.close()
    return new_date