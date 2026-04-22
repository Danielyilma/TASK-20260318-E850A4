from __future__ import annotations

import re


def validate_password_complexity(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain a digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must contain a special character")


def validate_username(username: str) -> None:
    if len(username) < 3 or len(username) > 100:
        raise ValueError("Username must be between 3 and 100 characters")
    if not re.fullmatch(r"[A-Za-z0-9_]+", username):
        raise ValueError("Username must contain only letters, digits, and underscores")
