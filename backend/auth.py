
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
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)

    columns = {
        row[1] for row in connection.execute(
            "PRAGMA table_info(workers)"
        ).fetchall()
    }

    if "status" not in columns:
        connection.execute("""
            ALTER TABLE workers
            ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'
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
                INSERT INTO workers (username, password_hash, status)
                VALUES (?, ?, 'pending')
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
            SELECT id, username, password_hash, status
            FROM workers
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if worker is None:
        return None

    if not password_hash.verify(password, worker[2]):
        return None

    if worker[3] != "approved":
        return None

    return {"id": worker[0], "username": worker[1]}


def list_pending_workers():
    with connect_auth_db() as connection:
        workers = connection.execute(
            """
            SELECT username
            FROM workers
            WHERE status = 'pending'
            ORDER BY username
            """
        ).fetchall()

    return [{"username": worker[0]} for worker in workers]


def approve_worker(username):
    username = username.strip().lower()

    with connect_auth_db() as connection:
        cursor = connection.execute(
            """
            UPDATE workers
            SET status = 'approved'
            WHERE username = ? AND status = 'pending'
            """,
            (username,),
        )

        if cursor.rowcount == 0:
            raise ValueError("Pending worker account not found.")

    return True
