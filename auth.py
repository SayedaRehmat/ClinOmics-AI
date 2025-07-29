# auth.py
import json
import os
import hashlib

USERS_FILE = "users.json"

def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, plan="free"):
    """Register a new user."""
    users = _load_users()
    if username in users:
        return False, "User already exists."
    users[username] = {
        "password": _hash_password(password),
        "plan": plan,
        "searches_today": 0
    }
    _save_users(users)
    return True, "Registration successful."

def login_user(username, password):
    """Authenticate a user."""
    users = _load_users()
    if username not in users:
        return False, "User not found."
    if users[username]["password"] != _hash_password(password):
        return False, "Incorrect password."
    return True, users[username]

def upgrade_plan(username, new_plan="pro"):
    """Upgrade user plan."""
    users = _load_users()
    if username in users:
        users[username]["plan"] = new_plan
        _save_users(users)
        return True, "Plan upgraded."
    return False, "User not found."

def track_search(username):
    """Track daily searches for Free users."""
    users = _load_users()
    if username not in users:
        return False, "User not found."
    user = users[username]
    if user["plan"] == "free" and user["searches_today"] >= 5:
        return False, "Daily search limit reached (Free plan)."
    user["searches_today"] += 1
    _save_users(users)
    return True, "Search recorded."
