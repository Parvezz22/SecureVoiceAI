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

# GET AUTHENTICATION HISTORY

def get_authentication_history(username=None, status=None):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT *
            FROM authentication_logs
            WHERE 1=1
        """

        parameters = []

        # Filter by username
        if username:
            query += " AND username LIKE ?"
            parameters.append(f"%{username}%")

        # Filter by authentication status
        if status:
            query += " AND authentication = ?"
            parameters.append(status.upper())

        query += " ORDER BY id DESC"

        records = cursor.execute(
            query, parameters
        ).fetchall()

        return [dict(row) for row in records]

    finally:
        connection.close()


# GET ALL REGISTERED USERS

def get_all_users():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        users = cursor.execute("""
            SELECT *
            FROM users
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in users]

    finally:
        connection.close()
# MAIN

if __name__ == "__main__":
    initialize_database()

    print("Database initialized successfully!")
    print(get_dashboard_stats())

# ============================================================
# GET ANALYTICS DATA FOR INTERACTIVE DASHBOARD
# ============================================================

def get_analytics_data():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # AUTHENTICATION SUMMARY
        # ----------------------------------------------------

        summary = cursor.execute("""
            SELECT
                COUNT(*) AS total_attempts,

                SUM(
                    CASE
                        WHEN authentication = 'SUCCESS'
                        THEN 1 ELSE 0
                    END
                ) AS successful_attempts,

                SUM(
                    CASE
                        WHEN authentication = 'FAILED'
                        THEN 1 ELSE 0
                    END
                ) AS failed_attempts,

                AVG(similarity_score) AS average_similarity,

                AVG(processing_time) AS average_processing_time

            FROM authentication_logs
        """).fetchone()

        # ----------------------------------------------------
        # DAILY AUTHENTICATION ACTIVITY
        # ----------------------------------------------------

        daily_activity = cursor.execute("""
            SELECT
                date(timestamp) AS activity_date,

                SUM(
                    CASE
                        WHEN authentication = 'SUCCESS'
                        THEN 1 ELSE 0
                    END
                ) AS successful,

                SUM(
                    CASE
                        WHEN authentication = 'FAILED'
                        THEN 1 ELSE 0
                    END
                ) AS failed

            FROM authentication_logs

            WHERE date(timestamp) >= date('now', 'localtime', '-6 days')

            GROUP BY date(timestamp)

            ORDER BY activity_date ASC
        """).fetchall()

        # ----------------------------------------------------
        # SIMILARITY SCORE DISTRIBUTION
        # ----------------------------------------------------

        score_distribution = cursor.execute("""
            SELECT

                CASE
                    WHEN similarity_score < 0.0 THEN 'Below 0.0'
                    WHEN similarity_score < 0.2 THEN '0.0 - 0.2'
                    WHEN similarity_score < 0.4 THEN '0.2 - 0.4'
                    WHEN similarity_score < 0.6 THEN '0.4 - 0.6'
                    WHEN similarity_score < 0.8 THEN '0.6 - 0.8'
                    ELSE '0.8 - 1.0'
                END AS score_range,

                COUNT(*) AS total

            FROM authentication_logs

            WHERE similarity_score IS NOT NULL

            GROUP BY score_range

            ORDER BY MIN(similarity_score)

        """).fetchall()

        return {

            "summary": dict(summary),

            "daily_activity": [
                dict(row) for row in daily_activity
            ],

            "score_distribution": [
                dict(row) for row in score_distribution
            ]

        }

    finally:

        connection.close()