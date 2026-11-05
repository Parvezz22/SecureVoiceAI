import sqlite3
from datetime import datetime

DATABASE_NAME = "securevoice.db"


# DATABASE CONNECTION

def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# CREATE DATABASE TABLES

def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            enrolled_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authentication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            authentication TEXT NOT NULL,
            similarity_score REAL,
            threshold REAL,
            confidence TEXT,
            processing_time REAL,
            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# REGISTER NEW USER

def add_user(username):
    connection = get_connection()
    cursor = connection.cursor()

    enrolled_at = datetime.now().isoformat(timespec="seconds")

    try:
        cursor.execute("""
            INSERT INTO users (username, enrolled_at)
            VALUES (?, ?)
        """, (username, enrolled_at))

        connection.commit()

    except sqlite3.IntegrityError:
        raise ValueError(
            f"User '{username}' already exists in database."
        )

    finally:
        connection.close()


# SAVE AUTHENTICATION HISTORY

def log_authentication(result):
    connection = get_connection()
    cursor = connection.cursor()

    timestamp = datetime.now().isoformat(timespec="seconds")

    try:
        cursor.execute("""
            INSERT INTO authentication_logs (
                username,
                authentication,
                similarity_score,
                threshold,
                confidence,
                processing_time,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result["username"],
            result["authentication"],
            result.get("similarity_score"),
            result.get("threshold"),
            result.get("confidence"),
            result.get("processing_time"),
            timestamp
        ))

        connection.commit()
        print("Authentication attempt saved in database!")

    finally:
        connection.close()


# GET DASHBOARD STATISTICS

def get_dashboard_stats():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        total_users = cursor.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        total_attempts = cursor.execute(
            "SELECT COUNT(*) FROM authentication_logs"
        ).fetchone()[0]

        successful_attempts = cursor.execute("""
            SELECT COUNT(*)
            FROM authentication_logs
            WHERE authentication = 'SUCCESS'
        """).fetchone()[0]

        failed_attempts = cursor.execute("""
            SELECT COUNT(*)
            FROM authentication_logs
            WHERE authentication = 'FAILED'
        """).fetchone()[0]

        recent_activity = cursor.execute("""
            SELECT *
            FROM authentication_logs
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

        return {
            "total_users": total_users,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "recent_activity": [
                dict(row) for row in recent_activity
            ]
        }

    finally:
        connection.close()


# MAIN

if __name__ == "__main__":
    initialize_database()

    print("Database initialized successfully!")
    print(get_dashboard_stats())