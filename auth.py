import os
import streamlit as st
import psycopg2
import hashlib
import random
import db_utils
from urllib.parse import urlparse

# Connection details – scale to Render DATABASE_URL or local fallback
# def get_db_config():
#     database_url = os.getenv("DATABASE_URL")
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

DB_CONFIG = db_utils.get_db_config()

def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def hash_password(password: str) -> str:
    """Hash password using SHA256 (simpler than bcrypt/passlib)."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, role, mfa_secret FROM auth_users WHERE username=%s", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        stored_hash, role, mfa_secret = row
        if hash_password(password) == stored_hash:
            return True, role, mfa_secret
    return False, None, None

# Initialize session state
for key in ["authenticated", "username", "role", "mfa_secret", "auth_step", "menu"]:
    if key not in st.session_state:
        st.session_state[key] = None

def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        valid, role, mfa_secret = verify_user(username, password)
        if valid:
            # Step 2: MFA prompt
            st.session_state.username = username
            st.session_state.role = role
            st.session_state.mfa_secret = mfa_secret
            st.session_state.auth_step = "mfa"
           # st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def mfa_verify():
    st.title("🔑 Multi‑Factor Authentication")
    code = st.text_input("Enter MFA code")

    if st.button("Verify"):
        # Compare entered code with secret stored in DB
        if code == st.session_state.mfa_secret:
            st.session_state.authenticated = True
            st.success(f"Welcome, {st.session_state.username}!")
            st.session_state.menu = "Dashboard"
           # st.experimental_rerun()
        else:
            st.error("Invalid MFA code")

def logout():
    for key in ["authenticated", "username", "role", "mfa_secret", "auth_step", "menu"]:
        st.session_state[key] = None
    #st.experimental_rerun()
