import streamlit as st
import sqlite3
import hashlib
import random

def connect_db():
    return sqlite3.connect("users.db")

def hash_password(password: str) -> str:
    """Hash password using SHA256 (simpler than bcrypt/passlib)."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, role, mfa_secret FROM auth_users WHERE username=?", (username,))
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
