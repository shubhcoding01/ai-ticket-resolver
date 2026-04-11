import os
import sqlite3
import logging
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "database/tickets.db")


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    Called by db_logger and dashboard whenever DB access is needed.

    Returns:
        sqlite3.Connection object
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """
    Create all database tables if they do not already exist.
    Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
    Called once at startup from main.py.
    """
    log.info(f"Initializing database at: {DB_PATH}")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_logs (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id         INTEGER NOT NULL,
                category          TEXT    NOT NULL,
                priority          TEXT    NOT NULL DEFAULT 'medium',
                action_taken      TEXT,
                resolved_by       TEXT,
                status            TEXT    NOT NULL DEFAULT 'OPEN',
                created_at        TEXT    NOT NULL,
                updated_at        TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id     INTEGER NOT NULL,
                script_name   TEXT    NOT NULL,
                machine_name  TEXT    NOT NULL,
                success       INTEGER NOT NULL DEFAULT 0,
                output        TEXT,
                error         TEXT,
                duration_secs REAL    DEFAULT 0.0,
                ran_at        TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_logs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id        INTEGER NOT NULL,
                subject          TEXT,
                category         TEXT    NOT NULL,
                priority         TEXT    NOT NULL,
                can_auto_resolve INTEGER NOT NULL DEFAULT 0,
                suggested_action TEXT,
                confidence       TEXT,
                classified_at    TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id     INTEGER NOT NULL,
                recipient     TEXT    NOT NULL,
                notif_type    TEXT    NOT NULL,
                subject       TEXT,
                success       INTEGER NOT NULL DEFAULT 0,
                sent_at       TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                date                TEXT    NOT NULL UNIQUE,
                total_tickets       INTEGER DEFAULT 0,
                auto_resolved       INTEGER DEFAULT 0,
                escalated           INTEGER DEFAULT 0,
                kb_guide_sent       INTEGER DEFAULT 0,
                avg_resolve_mins    REAL    DEFAULT 0.0,
                top_category        TEXT,
                created_at          TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_logs_ticket_id
            ON ticket_logs(ticket_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_logs_status
            ON ticket_logs(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_logs_category
            ON ticket_logs(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticket_logs_created_at
            ON ticket_logs(created_at)
        """)

        conn.commit()
        log.info("Database initialized successfully. All tables ready.")

    except sqlite3.Error as e:
        log.error(f"Database initialization error: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def reset_database() -> None:
    """
    Drop all tables and recreate them.
    WARNING — this deletes all data. Use only during development.
    """
    log.warning("RESETTING DATABASE — all data will be deleted!")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        tables = [
            "ticket_logs",
            "automation_logs",
            "classification_logs",
            "notification_logs",
            "daily_summary",
        ]

        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            log.info(f"Dropped table: {table}")

        conn.commit()
        log.info("All tables dropped.")

    finally:
        conn.close()

    initialize_database()
    log.info("Database reset complete.")


def get_table_stats() -> dict:
    """
    Return row counts for all tables.
    Useful for verifying data is being logged correctly.

    Returns:
        Dict of table_name -> row_count
    """
    conn   = get_connection()
    cursor = conn.cursor()
    stats  = {}

    tables = [
        "ticket_logs",
        "automation_logs",
        "classification_logs",
        "notification_logs",
        "daily_summary",
    ]

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        except sqlite3.Error:
            stats[table] = "ERROR"

    conn.close()
    return stats


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("DATABASE SETUP TEST")
    print("=" * 60 + "\n")

    initialize_database()

    print("\nTable row counts after initialization:")
    stats = get_table_stats()
    for table, count in stats.items():
        print(f"  {table:<30} : {count} rows")

    print("\nDatabase setup complete.")