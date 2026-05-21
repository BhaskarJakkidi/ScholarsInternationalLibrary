import os
import time
import streamlit as st

# Session defaults
defaults = {
    "authenticated": False,
    "auth_step": "login",
    "menu": None,
    "login_time": None,   # track login timestamp
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Session timeout (15 minutes)
SESSION_TIMEOUT = 15 * 60  

# Passcode stored in environment variable (set in Railway/Render or .env file)
PASSCODE = os.getenv("APP_PASSCODE", "556889")  # fallback default

def check_session_timeout():
    """Auto-logout if session exceeds timeout."""
    if st.session_state.authenticated and st.session_state.login_time:
        elapsed = time.time() - st.session_state.login_time
        if elapsed > SESSION_TIMEOUT:
            st.warning("Session expired. Please log in again.")
            logout()

def login():
    st.title("🔐 Passcode Login")
    code = st.text_input("Enter passcode", type="password", key="passcode_input")

    if st.button("Login", key="login_btn"):
        if code == PASSCODE:
            st.session_state.authenticated = True
            st.session_state.username = "Jakkidi Bhaskar Reddy"  # Hardcoded for demo
            st.session_state.role = "Admin"  # Hardcoded for demo
            st.session_state.menu = "Dashboard"
            st.session_state.login_time = time.time()
            st.success("Welcome! You are logged in.")
           # st.experimental_rerun()
        else:
            st.error("Invalid passcode")

def logout():
    for key, val in defaults.items():
        st.session_state[key] = val
    st.experimental_rerun()

# Run timeout check at the start of each rerun
check_session_timeout()

# Routing
if not st.session_state.authenticated:
    login()
else:
    st.title("📊 Dashboard")
    st.write("You are logged in with passcode authentication.")
    if st.button("Logout"):
        logout()
