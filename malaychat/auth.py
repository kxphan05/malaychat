"""Simple username/password authentication using Google Sheets."""

from __future__ import annotations

import hashlib
import logging

import gspread
import streamlit as st

from malaychat.progress import _get_client

logger = logging.getLogger("malaychat.auth")


def _hash_password(password: str) -> str:
    """Hash a password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _get_spreadsheet() -> gspread.Spreadsheet:
    """Open the progress spreadsheet."""
    client = _get_client()
    spreadsheet_url = st.secrets.get("PROGRESS_SHEET_URL", "")
    if not spreadsheet_url:
        raise ValueError("PROGRESS_SHEET_URL not set in Streamlit secrets.")
    return client.open_by_url(spreadsheet_url)


def _get_users_worksheet() -> gspread.Worksheet:
    """Get or create the 'users' worksheet."""
    spreadsheet = _get_spreadsheet()
    try:
        return spreadsheet.worksheet("users")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="users", rows=100, cols=2)
        ws.update(range_name="A1", values=[["username", "password_hash"]])
        return ws


def authenticate(username: str, password: str) -> bool:
    """Check if username/password match a stored user."""
    ws = _get_users_worksheet()
    rows = ws.get_all_values()
    pw_hash = _hash_password(password)
    for row in rows[1:]:  # skip header
        if len(row) >= 2 and row[0] == username and row[1] == pw_hash:
            return True
    return False


def register(username: str, password: str) -> bool:
    """Register a new user. Returns False if username already taken."""
    ws = _get_users_worksheet()
    rows = ws.get_all_values()
    for row in rows[1:]:
        if len(row) >= 1 and row[0] == username:
            return False  # username taken
    pw_hash = _hash_password(password)
    ws.append_row([username, pw_hash])
    return True


def render_login() -> str | None:
    """
    Render the login/register form. Returns username if authenticated, None otherwise.

    Call this at the top of the app — if it returns None, stop rendering the rest.
    """
    if "username" in st.session_state and st.session_state.username:
        return st.session_state.username

    st.title("MalayChat 🇲🇾")
    st.markdown("**Log in or create an account to track your progress.**")

    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            if not login_user or not login_pass:
                st.error("Please enter both username and password.")
            else:
                try:
                    if authenticate(login_user, login_pass):
                        st.session_state.username = login_user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception:
                    logger.exception("Authentication failed")
                    st.error("Could not connect to the database. Check your secrets configuration.")

    with tab_register:
        reg_user = st.text_input("Choose a username", key="reg_user")
        reg_pass = st.text_input("Choose a password", type="password", key="reg_pass")
        reg_pass2 = st.text_input("Confirm password", type="password", key="reg_pass2")
        if st.button("Create Account", use_container_width=True):
            if not reg_user or not reg_pass:
                st.error("Please fill in all fields.")
            elif len(reg_user) < 3:
                st.error("Username must be at least 3 characters.")
            elif len(reg_pass) < 4:
                st.error("Password must be at least 4 characters.")
            elif reg_pass != reg_pass2:
                st.error("Passwords do not match.")
            else:
                try:
                    if register(reg_user, reg_pass):
                        st.session_state.username = reg_user
                        st.success("Account created!")
                        st.rerun()
                    else:
                        st.error("Username already taken.")
                except Exception:
                    logger.exception("Registration failed")
                    st.error("Could not connect to the database. Check your secrets configuration.")

    return None
