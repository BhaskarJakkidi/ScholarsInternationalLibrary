import duckdb
from datetime import datetime, timedelta

DB_NAME = "library.duckdb"

def connect_db():
    # Persistent DuckDB file
    return duckdb.connect(DB_NAME)

def register_user(name, phone, email, course, seat, plan, start_date, payment_mode):
    conn = connect_db()

    # Prevent duplicate seat allocation
    result = conn.execute("SELECT COUNT(*) FROM users WHERE seat=? AND active_status=1", (seat,)).fetchone()
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

    conn.execute("""
        INSERT INTO users (name, phone, email, course, seat, start_date, active_status, payment_plan, renewal_date, payment_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, email, course, seat, start_date, 1, plan, renewal.strftime("%Y-%m-%d"), payment_mode))

    conn.commit()
    conn.close()
    return True, f"User {name} registered successfully!"

def change_seat(user_id, new_seat):
    conn = connect_db()

    # Cast to plain Python int
    user_id = int(user_id)

    new_seat = int(new_seat)
    result = conn.execute("SELECT COUNT(*) FROM users WHERE seat=? AND id!=?", (new_seat, user_id)).fetchone()
    
    if result[0] > 0:
        conn.close()
        return False, f"Seat {new_seat} is already taken."

    conn.execute("UPDATE users SET seat=? WHERE id=?", (new_seat, user_id))
    conn.commit()
    conn.close()
    return True, "Seat updated successfully!"

def deactivate_user(user_id):
    conn = connect_db()

    # Cast to plain Python int
    user_id = int(user_id)
    conn.execute("UPDATE users SET active_status=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True, "User deactivated successfully!"

def activate_user(user_id, start_date, plan, payment_mode, remarks):
    conn = connect_db()
    # Cast to plain Python int
    user_id = int(user_id)
    conn.execute(
        "UPDATE users SET active_status=1, start_date=?, payment_plan=?, remarks=?, payment_mode=? WHERE id=?",
        (start_date, plan, remarks, payment_mode, user_id)
    )
    conn.commit()
    conn.close()
    return True, "User activated successfully!"

def get_users():
    conn = connect_db()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return rows

def get_total_seats():
    conn = connect_db()
    result = conn.execute("SELECT total_seats FROM seats LIMIT 1").fetchone()
    conn.close()
    return result[0] if result else 0

def get_upcoming_renewals():
    days = 3
    conn = connect_db()
    cutoff_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    results = conn.execute("""
        SELECT id, name, phone, seat, renewal_date, payment_mode, payment_plan
        FROM users
        WHERE renewal_date IS NOT NULL
        AND DATE(renewal_date) <= DATE(?) AND active_status=1
        ORDER BY renewal_date ASC
    """, (cutoff_date,)).fetchall()
    conn.close()
    return results

def update_renewal(user_id, plan, payment_mode, renewal_date):
    conn = connect_db()
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

    conn.execute("""
        UPDATE users
        SET renewal_date=?, payment_mode=?, payment_plan=?
        WHERE id=?
    """, (new_date.strftime("%Y-%m-%d"), payment_mode, plan, user_id))
    conn.commit()
    conn.close()
    return new_date