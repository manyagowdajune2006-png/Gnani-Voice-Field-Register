
"""Authentication helpers for ASHA worker accounts."""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "./data/visits.db"))
password_hash = PasswordHash.recommended()


def connect_auth_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    return connection


def create_worker(username, password):
    username = username.strip().lower()

    if len(username) < 3:
        raise ValueError("Username must contain at least 3 characters.")

    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")

    hashed_password = password_hash.hash(password)

    try:
        with connect_auth_db() as connection:
            connection.execute(
                """
                INSERT INTO workers (username, password_hash)
                VALUES (?, ?)
                """,
                (username, hashed_password),
            )
    except sqlite3.IntegrityError:
        raise ValueError("This username already exists.")

    return True


def authenticate_worker(username, password):
    username = username.strip().lower()

    with connect_auth_db() as connection:
        worker = connection.execute(
            """
            SELECT id, username, password_hash
            FROM workers
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if worker is None:
        return None

    if not password_hash.verify(password, worker[2]):
        return None

    return {
        "id": worker[0],
        "username": worker[1]
    }
