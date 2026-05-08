# import os
# import sqlite3
# import logging
# from dotenv import load_dotenv

# load_dotenv()

# log = logging.getLogger(__name__)

# DB_PATH = os.getenv("DB_PATH", "database/tickets.db")


# def get_connection() -> sqlite3.Connection:
#     """
#     Create and return a SQLite database connection.
#     Called by db_logger and dashboard whenever DB access is needed.

#     Returns:
#         sqlite3.Connection object
#     """
#     os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     return conn


# def initialize_database() -> None:
#     """
#     Create all database tables if they do not already exist.
#     Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
#     Called once at startup from main.py.
#     """
#     log.info(f"Initializing database at: {DB_PATH}")

#     conn = get_connection()

#     try:
#         cursor = conn.cursor()

#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS ticket_logs (
#                 id                INTEGER PRIMARY KEY AUTOINCREMENT,
#                 ticket_id         INTEGER NOT NULL,
#                 category          TEXT    NOT NULL,
#                 priority          TEXT    NOT NULL DEFAULT 'medium',
#                 action_taken      TEXT,
#                 resolved_by       TEXT,
#                 status            TEXT    NOT NULL DEFAULT 'OPEN',
#                 created_at        TEXT    NOT NULL,
#                 updated_at        TEXT    NOT NULL
#             )
#         """)

#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS automation_logs (
#                 id            INTEGER PRIMARY KEY AUTOINCREMENT,
#                 ticket_id     INTEGER NOT NULL,
#                 script_name   TEXT    NOT NULL,
#                 machine_name  TEXT    NOT NULL,
#                 success       INTEGER NOT NULL DEFAULT 0,
#                 output        TEXT,
#                 error         TEXT,
#                 duration_secs REAL    DEFAULT 0.0,
#                 ran_at        TEXT    NOT NULL
#             )
#         """)

#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS classification_logs (
#                 id               INTEGER PRIMARY KEY AUTOINCREMENT,
#                 ticket_id        INTEGER NOT NULL,
#                 subject          TEXT,
#                 category         TEXT    NOT NULL,
#                 priority         TEXT    NOT NULL,
#                 can_auto_resolve INTEGER NOT NULL DEFAULT 0,
#                 suggested_action TEXT,
#                 confidence       TEXT,
#                 classified_at    TEXT    NOT NULL
#             )
#         """)

#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS notification_logs (
#                 id            INTEGER PRIMARY KEY AUTOINCREMENT,
#                 ticket_id     INTEGER NOT NULL,
#                 recipient     TEXT    NOT NULL,
#                 notif_type    TEXT    NOT NULL,
#                 subject       TEXT,
#                 success       INTEGER NOT NULL DEFAULT 0,
#                 sent_at       TEXT    NOT NULL
#             )
#         """)

#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS daily_summary (
#                 id                  INTEGER PRIMARY KEY AUTOINCREMENT,
#                 date                TEXT    NOT NULL UNIQUE,
#                 total_tickets       INTEGER DEFAULT 0,
#                 auto_resolved       INTEGER DEFAULT 0,
#                 escalated           INTEGER DEFAULT 0,
#                 kb_guide_sent       INTEGER DEFAULT 0,
#                 avg_resolve_mins    REAL    DEFAULT 0.0,
#                 top_category        TEXT,
#                 created_at          TEXT    NOT NULL
#             )
#         """)

#         cursor.execute("""
#             CREATE INDEX IF NOT EXISTS idx_ticket_logs_ticket_id
#             ON ticket_logs(ticket_id)
#         """)

#         cursor.execute("""
#             CREATE INDEX IF NOT EXISTS idx_ticket_logs_status
#             ON ticket_logs(status)
#         """)

#         cursor.execute("""
#             CREATE INDEX IF NOT EXISTS idx_ticket_logs_category
#             ON ticket_logs(category)
#         """)

#         cursor.execute("""
#             CREATE INDEX IF NOT EXISTS idx_ticket_logs_created_at
#             ON ticket_logs(created_at)
#         """)

#         conn.commit()
#         log.info("Database initialized successfully. All tables ready.")

#     except sqlite3.Error as e:
#         log.error(f"Database initialization error: {e}")
#         conn.rollback()
#         raise

#     finally:
#         conn.close()


# def reset_database() -> None:
#     """
#     Drop all tables and recreate them.
#     WARNING — this deletes all data. Use only during development.
#     """
#     log.warning("RESETTING DATABASE — all data will be deleted!")

#     conn = get_connection()

#     try:
#         cursor = conn.cursor()

#         tables = [
#             "ticket_logs",
#             "automation_logs",
#             "classification_logs",
#             "notification_logs",
#             "daily_summary",
#         ]

#         for table in tables:
#             cursor.execute(f"DROP TABLE IF EXISTS {table}")
#             log.info(f"Dropped table: {table}")

#         conn.commit()
#         log.info("All tables dropped.")

#     finally:
#         conn.close()

#     initialize_database()
#     log.info("Database reset complete.")


# def get_table_stats() -> dict:
#     """
#     Return row counts for all tables.
#     Useful for verifying data is being logged correctly.

#     Returns:
#         Dict of table_name -> row_count
#     """
#     conn   = get_connection()
#     cursor = conn.cursor()
#     stats  = {}

#     tables = [
#         "ticket_logs",
#         "automation_logs",
#         "classification_logs",
#         "notification_logs",
#         "daily_summary",
#     ]

#     for table in tables:
#         try:
#             cursor.execute(f"SELECT COUNT(*) FROM {table}")
#             stats[table] = cursor.fetchone()[0]
#         except sqlite3.Error:
#             stats[table] = "ERROR"

#     conn.close()
#     return stats


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(message)s"
#     )

#     print("\n" + "=" * 60)
#     print("DATABASE SETUP TEST")
#     print("=" * 60 + "\n")

#     initialize_database()

#     print("\nTable row counts after initialization:")
#     stats = get_table_stats()
#     for table, count in stats.items():
#         print(f"  {table:<30} : {count} rows")

#     print("\nDatabase setup complete.")

import os
import sqlite3
import logging
from pathlib import Path
from dotenv  import load_dotenv

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() == "true"
DB_PATH   = os.getenv("DB_PATH",   "database/tickets.db")


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    Automatically creates the database directory if it
    does not exist yet.
    Called by db_logger and dashboard whenever DB access
    is needed.

    Returns:
        sqlite3.Connection with row_factory set to
        sqlite3.Row so results can be accessed as dicts
    """
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")

    return conn


def initialize_database() -> None:
    """
    Create all database tables if they do not already exist.
    Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
    Also creates indexes for fast dashboard queries.
    Called once at startup from main.py and demo_runner.py.
    """
    log.info(f"Initializing database at: {DB_PATH}")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_logs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id    INTEGER NOT NULL,
                category     TEXT    NOT NULL,
                priority     TEXT    NOT NULL DEFAULT 'medium',
                action_taken TEXT,
                resolved_by  TEXT,
                status       TEXT    NOT NULL DEFAULT 'OPEN',
                created_at   TEXT    NOT NULL,
                updated_at   TEXT    NOT NULL
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
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id  INTEGER NOT NULL,
                recipient  TEXT    NOT NULL,
                notif_type TEXT    NOT NULL,
                subject    TEXT,
                success    INTEGER NOT NULL DEFAULT 0,
                sent_at    TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                date             TEXT    NOT NULL UNIQUE,
                total_tickets    INTEGER DEFAULT 0,
                auto_resolved    INTEGER DEFAULT 0,
                escalated        INTEGER DEFAULT 0,
                kb_guide_sent    INTEGER DEFAULT 0,
                avg_resolve_mins REAL    DEFAULT 0.0,
                top_category     TEXT,
                created_at       TEXT    NOT NULL
            )
        """)

        _create_indexes(cursor)

        conn.commit()
        log.info(
            "Database initialized successfully. "
            "All tables ready."
        )

    except sqlite3.Error as e:
        log.error(f"Database initialization error: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def _create_indexes(cursor: sqlite3.Cursor) -> None:
    """
    Create all database indexes for fast dashboard queries.
    Uses IF NOT EXISTS so safe to call on existing databases.

    Args:
        cursor : Active SQLite cursor from initialize_database()
    """
    indexes = [
        (
            "idx_ticket_logs_ticket_id",
            "ticket_logs(ticket_id)",
        ),
        (
            "idx_ticket_logs_status",
            "ticket_logs(status)",
        ),
        (
            "idx_ticket_logs_category",
            "ticket_logs(category)",
        ),
        (
            "idx_ticket_logs_created_at",
            "ticket_logs(created_at)",
        ),
        (
            "idx_ticket_logs_resolved_by",
            "ticket_logs(resolved_by)",
        ),
        (
            "idx_ticket_logs_priority",
            "ticket_logs(priority)",
        ),
        (
            "idx_automation_logs_ticket_id",
            "automation_logs(ticket_id)",
        ),
        (
            "idx_automation_logs_success",
            "automation_logs(success)",
        ),
        (
            "idx_classification_logs_ticket_id",
            "classification_logs(ticket_id)",
        ),
        (
            "idx_classification_logs_category",
            "classification_logs(category)",
        ),
        (
            "idx_notification_logs_ticket_id",
            "notification_logs(ticket_id)",
        ),
        (
            "idx_notification_logs_recipient",
            "notification_logs(recipient)",
        ),
    ]

    for index_name, table_col in indexes:
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_col}"
        )
        log.debug(f"Index ready: {index_name}")


def reset_database() -> None:
    """
    Drop all tables and recreate them from scratch.
    WARNING — this permanently deletes ALL data.
    Use only during development or to clear demo data.
    """
    log.warning(
        "RESETTING DATABASE — all data will be deleted!"
    )

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
    Useful for verifying data is being logged correctly
    and for the dashboard health check.

    Returns:
        Dict of table_name -> row_count (int or 'ERROR')
    """
    tables = [
        "ticket_logs",
        "automation_logs",
        "classification_logs",
        "notification_logs",
        "daily_summary",
    ]

    stats = {}

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        for table in tables:
            try:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table}"
                )
                stats[table] = cursor.fetchone()[0]
            except sqlite3.Error:
                stats[table] = "ERROR"

        return stats

    except sqlite3.Error as e:
        log.error(f"DB error fetching table stats: {e}")
        return {t: "ERROR" for t in tables}

    finally:
        conn.close()


def get_database_info() -> dict:
    """
    Return detailed information about the database file
    including path, size, and table stats.
    Used by the dashboard settings and startup summary.

    Returns:
        Dict with path, size_kb, tables, and exists flag
    """
    db_file   = Path(DB_PATH)
    exists    = db_file.exists()
    size_kb   = round(db_file.stat().st_size / 1024, 2) if exists else 0.0
    table_stats = get_table_stats() if exists else {}

    return {
        "path"       : str(db_file.resolve()),
        "exists"     : exists,
        "size_kb"    : size_kb,
        "demo_mode"  : DEMO_MODE,
        "tables"     : table_stats,
    }


def backup_database(backup_path: str = None) -> bool:
    """
    Create a backup copy of the database file.
    Useful before running reset_database() or before
    switching from demo to live mode.

    Args:
        backup_path : Optional custom path for backup file.
                      Defaults to database/tickets_backup.db

    Returns:
        True if backup created successfully, False otherwise
    """
    if not backup_path:
        backup_path = DB_PATH.replace(".db", "_backup.db")

    source = Path(DB_PATH)

    if not source.exists():
        log.warning(
            f"Cannot backup — database file not found: {DB_PATH}"
        )
        return False

    try:
        source_conn = sqlite3.connect(DB_PATH)
        backup_conn = sqlite3.connect(backup_path)

        source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        backup_size = round(
            Path(backup_path).stat().st_size / 1024, 2
        )
        log.info(
            f"Database backed up to: {backup_path} "
            f"({backup_size} KB)"
        )
        return True

    except sqlite3.Error as e:
        log.error(f"Database backup failed: {e}")
        return False

    except Exception as e:
        log.error(f"Unexpected backup error: {e}")
        return False


def check_database_health() -> dict:
    """
    Run a quick health check on the database.
    Verifies all tables exist, indexes are present,
    and the database is readable.
    Called at startup to catch any corruption issues.

    Returns:
        Dict with status (OK/ERROR), tables_ok (bool),
        row_counts (dict), and any error message
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        required_tables = [
            "ticket_logs",
            "automation_logs",
            "classification_logs",
            "notification_logs",
        ]

        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table'"
        )
        existing_tables = {
            row[0] for row in cursor.fetchall()
        }

        missing = [
            t for t in required_tables
            if t not in existing_tables
        ]

        if missing:
            conn.close()
            return {
                "status"     : "ERROR",
                "tables_ok"  : False,
                "missing"    : missing,
                "row_counts" : {},
                "error"      : f"Missing tables: {missing}",
            }

        row_counts = {}
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_counts[table] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index'"
        )
        index_count = len(cursor.fetchall())

        conn.close()

        return {
            "status"      : "OK",
            "tables_ok"   : True,
            "missing"     : [],
            "row_counts"  : row_counts,
            "index_count" : index_count,
            "error"       : None,
        }

    except sqlite3.Error as e:
        log.error(f"Database health check failed: {e}")
        return {
            "status"     : "ERROR",
            "tables_ok"  : False,
            "missing"    : [],
            "row_counts" : {},
            "error"      : str(e),
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
    )

    print("\n" + "=" * 60)
    print("DATABASE SETUP TEST")
    print("=" * 60)
    print(f"  DB Path   : {DB_PATH}")
    print(
        f"  Demo Mode : "
        f"{'YES' if DEMO_MODE else 'NO'}"
    )
    print()

    print("Step 1 — Initializing database...")
    initialize_database()

    print("\nStep 2 — Table row counts:")
    stats = get_table_stats()
    for table, count in stats.items():
        print(f"  {table:<35} : {count} rows")

    print("\nStep 3 — Database info:")
    info = get_database_info()
    print(f"  Path      : {info['path']}")
    print(f"  Exists    : {info['exists']}")
    print(f"  Size      : {info['size_kb']} KB")
    print(f"  Demo Mode : {info['demo_mode']}")

    print("\nStep 4 — Health check:")
    health = check_database_health()
    print(f"  Status      : {health['status']}")
    print(f"  Tables OK   : {health['tables_ok']}")
    print(f"  Index count : {health.get('index_count', 0)}")
    if health["error"]:
        print(f"  Error       : {health['error']}")
    else:
        print("  All tables healthy ✓")
        for table, count in health["row_counts"].items():
            print(f"    {table:<35} : {count} rows")

    print("\nStep 5 — Backup test:")
    backed_up = backup_database()
    print(
        f"  Backup: "
        f"{'SUCCESS ✓' if backed_up else 'FAILED ✗'}"
    )

    print("\nStep 6 — Reset test (creates fresh empty DB)...")
    confirm = input(
        "  Type 'yes' to test reset (deletes all data): "
    ).strip().lower()

    if confirm == "yes":
        reset_database()
        stats_after = get_table_stats()
        print("  Tables after reset:")
        for table, count in stats_after.items():
            print(f"    {table:<35} : {count} rows")
    else:
        print("  Reset skipped.")

    print("\n" + "=" * 60)
    print("Database setup test complete.")
    print("=" * 60 + "\n")