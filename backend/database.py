"""
database.py
-----------
Simple JSON file-based user storage.
Stores users as: { "email": { "name": ..., "password": ... } }
"""

import json
import os

DB_FILE = "users.json"


def load_users() -> dict:
    """Load all users from file."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_users(users: dict):
    """Save all users to file."""
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_user(email: str) -> dict | None:
    """Get a single user by email."""
    users = load_users()
    return users.get(email)


def create_user(name: str, email: str, hashed_password: str) -> dict:
    """Create and save a new user."""
    users = load_users()
    if email in users:
        return None   # user already exists
    users[email] = {
        "name":     name,
        "email":    email,
        "password": hashed_password,
        "role":     "HR Admin"
    }
    save_users(users)
    return users[email]