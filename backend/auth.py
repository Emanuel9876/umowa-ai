import streamlit as st
import bcrypt
from backend.db import get_user, add_user

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed)

def login_user(username: str, password: str) -> bool:
    user = get_user(username)
    if not user:
        return False
    if check_password(password, user['password_hash'].encode()):
        st.session_state["user"] = {"id": user['id'], "username": user['username'], "role": user['role']}
        return True
    return False

def logout_user():
    if "user" in st.session_state:
        del st.session_state["user"]

def register_user(username: str, password: str) -> bool:
    hashed = hash_password(password)
    success = add_user(username, hashed.decode())
    return success

def get_current_user():
    return st.session_state.get("user", None)
