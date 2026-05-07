# import sqlite3
# import logging
# from datetime import datetime
# from database.db_setup import get_connection

# log = logging.getLogger(__name__)


# def log_ticket_action(
#     ticket_id   : int,
#     category    : str,
#     priority    : str,
#     action_taken: str,
#     resolved_by : str,
#     status      : str,
# ) -> bool:
#     """
#     Log every ticket resolution action to the database.
#     Called by orchestrator after every ticket is processed.

#     Args:
#         ticket_id    : Freshdesk ticket ID
#         category     : AI classified category
#         priority     : Ticket priority level
#         action_taken : Description of what was done
#         resolved_by  : Who/what resolved — AI_AUTO, KB, ESCALATION, ENGINEER
#         status       : Final status — RESOLVED or ESCALATED

#     Returns:
#         True if logged successfully, False otherwise
#     """
#     now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             SELECT id FROM ticket_logs WHERE ticket_id = ?
#         """, (ticket_id,))

#         existing = cursor.fetchone()

#         if existing:
#             cursor.execute("""
#                 UPDATE ticket_logs
#                 SET category     = ?,
#                     priority     = ?,
#                     action_taken = ?,
#                     resolved_by  = ?,
#                     status       = ?,
#                     updated_at   = ?
#                 WHERE ticket_id  = ?
#             """, (
#                 category, priority, action_taken,
#                 resolved_by, status, now, ticket_id
#             ))
#             log.debug(f"Updated existing log for ticket #{ticket_id}")

#         else:
#             cursor.execute("""
#                 INSERT INTO ticket_logs (
#                     ticket_id, category, priority,
#                     action_taken, resolved_by, status,
#                     created_at, updated_at
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 ticket_id, category, priority,
#                 action_taken, resolved_by, status,
#                 now, now
#             ))
#             log.debug(f"Inserted new log for ticket #{ticket_id}")

#         conn.commit()
#         log.info(
#             f"Logged ticket #{ticket_id} — "
#             f"status: {status}, resolved_by: {resolved_by}"
#         )
#         return True

#     except sqlite3.Error as e:
#         log.error(f"DB error logging ticket #{ticket_id}: {e}")
#         return False

#     finally:
#         conn.close()


# def log_automation(
#     ticket_id    : int,
#     script_name  : str,
#     machine_name : str,
#     success      : bool,
#     output       : str = "",
#     error        : str = "",
#     duration_secs: float = 0.0,
# ) -> bool:
#     """
#     Log every automation script execution to the database.
#     Tracks which scripts ran, on which machines, and whether they succeeded.

#     Args:
#         ticket_id     : Freshdesk ticket ID
#         script_name   : Name of the PowerShell script that ran
#         machine_name  : Target machine the script ran on
#         success       : True if script exited with code 0
#         output        : Script stdout output
#         error         : Script stderr output
#         duration_secs : How long the script took in seconds

#     Returns:
#         True if logged successfully, False otherwise
#     """
#     now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             INSERT INTO automation_logs (
#                 ticket_id, script_name, machine_name,
#                 success, output, error,
#                 duration_secs, ran_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             ticket_id, script_name, machine_name,
#             1 if success else 0,
#             output[:2000] if output else "",
#             error[:2000]  if error  else "",
#             round(duration_secs, 2),
#             now
#         ))

#         conn.commit()
#         log.debug(
#             f"Automation logged: ticket #{ticket_id}, "
#             f"script: {script_name}, "
#             f"success: {success}"
#         )
#         return True

#     except sqlite3.Error as e:
#         log.error(f"DB error logging automation for ticket #{ticket_id}: {e}")
#         return False

#     finally:
#         conn.close()


# def log_classification(
#     ticket_id       : int,
#     subject         : str,
#     category        : str,
#     priority        : str,
#     can_auto_resolve: bool,
#     suggested_action: str,
#     confidence      : str,
# ) -> bool:
#     """
#     Log every AI classification result to the database.
#     Useful for auditing AI accuracy over time.

#     Args:
#         ticket_id        : Freshdesk ticket ID
#         subject          : Ticket subject line
#         category         : Classified category
#         priority         : Classified priority
#         can_auto_resolve : Whether AI said it can be auto-resolved
#         suggested_action : AI suggested action text
#         confidence       : Classifier confidence level

#     Returns:
#         True if logged successfully, False otherwise
#     """
#     now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             INSERT INTO classification_logs (
#                 ticket_id, subject, category, priority,
#                 can_auto_resolve, suggested_action,
#                 confidence, classified_at
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             ticket_id, subject, category, priority,
#             1 if can_auto_resolve else 0,
#             suggested_action, confidence, now
#         ))

#         conn.commit()
#         log.debug(f"Classification logged for ticket #{ticket_id}")
#         return True

#     except sqlite3.Error as e:
#         log.error(f"DB error logging classification for ticket #{ticket_id}: {e}")
#         return False

#     finally:
#         conn.close()


# def log_notification(
#     ticket_id : int,
#     recipient : str,
#     notif_type: str,
#     subject   : str,
#     success   : bool,
# ) -> bool:
#     """
#     Log every email notification attempt to the database.

#     Args:
#         ticket_id  : Freshdesk ticket ID
#         recipient  : Email address notification was sent to
#         notif_type : Type of notification sent
#         subject    : Email subject line
#         success    : True if email was sent successfully

#     Returns:
#         True if logged successfully, False otherwise
#     """
#     now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             INSERT INTO notification_logs (
#                 ticket_id, recipient, notif_type,
#                 subject, success, sent_at
#             ) VALUES (?, ?, ?, ?, ?, ?)
#         """, (
#             ticket_id, recipient, notif_type,
#             subject, 1 if success else 0, now
#         ))

#         conn.commit()
#         log.debug(
#             f"Notification logged: ticket #{ticket_id}, "
#             f"to: {recipient}, success: {success}"
#         )
#         return True

#     except sqlite3.Error as e:
#         log.error(f"DB error logging notification for ticket #{ticket_id}: {e}")
#         return False

#     finally:
#         conn.close()


# def get_all_ticket_logs(limit: int = 100) -> list:
#     """
#     Fetch recent ticket logs for the dashboard.

#     Args:
#         limit : Maximum number of records to return

#     Returns:
#         List of ticket log dicts ordered by most recent first
#     """
#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             SELECT * FROM ticket_logs
#             ORDER BY created_at DESC
#             LIMIT ?
#         """, (limit,))

#         rows = [dict(row) for row in cursor.fetchall()]
#         return rows

#     except sqlite3.Error as e:
#         log.error(f"DB error fetching ticket logs: {e}")
#         return []

#     finally:
#         conn.close()


# def get_resolution_stats() -> dict:
#     """
#     Get overall resolution statistics for the dashboard.

#     Returns:
#         Dict with total, resolved, escalated counts and auto-resolve rate
#     """
#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("SELECT COUNT(*) FROM ticket_logs")
#         total = cursor.fetchone()[0]

#         cursor.execute("""
#             SELECT COUNT(*) FROM ticket_logs
#             WHERE status = 'RESOLVED'
#         """)
#         resolved = cursor.fetchone()[0]

#         cursor.execute("""
#             SELECT COUNT(*) FROM ticket_logs
#             WHERE status = 'ESCALATED'
#         """)
#         escalated = cursor.fetchone()[0]

#         cursor.execute("""
#             SELECT COUNT(*) FROM ticket_logs
#             WHERE resolved_by = 'AI_AUTO'
#         """)
#         ai_resolved = cursor.fetchone()[0]

#         auto_rate = round((ai_resolved / total * 100), 1) if total > 0 else 0.0

#         cursor.execute("""
#             SELECT category, COUNT(*) as count
#             FROM ticket_logs
#             GROUP BY category
#             ORDER BY count DESC
#             LIMIT 1
#         """)
#         top_row      = cursor.fetchone()
#         top_category = top_row["category"] if top_row else "N/A"

#         cursor.execute("""
#             SELECT category, COUNT(*) as count
#             FROM ticket_logs
#             GROUP BY category
#             ORDER BY count DESC
#         """)
#         category_rows  = cursor.fetchall()
#         category_counts = {
#             row["category"]: row["count"]
#             for row in category_rows
#         }

#         return {
#             "total"          : total,
#             "resolved"       : resolved,
#             "escalated"      : escalated,
#             "ai_resolved"    : ai_resolved,
#             "auto_rate_pct"  : auto_rate,
#             "top_category"   : top_category,
#             "category_counts": category_counts,
#         }

#     except sqlite3.Error as e:
#         log.error(f"DB error fetching resolution stats: {e}")
#         return {
#             "total"          : 0,
#             "resolved"       : 0,
#             "escalated"      : 0,
#             "ai_resolved"    : 0,
#             "auto_rate_pct"  : 0.0,
#             "top_category"   : "N/A",
#             "category_counts": {},
#         }

#     finally:
#         conn.close()


# def get_daily_stats(days: int = 7) -> list:
#     """
#     Get per-day ticket counts for the last N days.
#     Used to draw the daily trend chart in the dashboard.

#     Args:
#         days : Number of past days to include

#     Returns:
#         List of dicts with date and counts
#     """
#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(f"""
#             SELECT
#                 DATE(created_at)          AS date,
#                 COUNT(*)                  AS total,
#                 SUM(CASE WHEN status = 'RESOLVED'  THEN 1 ELSE 0 END) AS resolved,
#                 SUM(CASE WHEN status = 'ESCALATED' THEN 1 ELSE 0 END) AS escalated
#             FROM ticket_logs
#             WHERE created_at >= DATE('now', '-{days} days')
#             GROUP BY DATE(created_at)
#             ORDER BY date ASC
#         """)

#         rows = [dict(row) for row in cursor.fetchall()]
#         return rows

#     except sqlite3.Error as e:
#         log.error(f"DB error fetching daily stats: {e}")
#         return []

#     finally:
#         conn.close()


# def get_recent_automation_logs(limit: int = 50) -> list:
#     """
#     Fetch recent automation script execution logs.

#     Args:
#         limit : Max number of records

#     Returns:
#         List of automation log dicts
#     """
#     try:
#         conn   = get_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             SELECT * FROM automation_logs
#             ORDER BY ran_at DESC
#             LIMIT ?
#         """, (limit,))

#         return [dict(row) for row in cursor.fetchall()]

#     except sqlite3.Error as e:
#         log.error(f"DB error fetching automation logs: {e}")
#         return []

#     finally:
#         conn.close()


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(message)s"
#     )

#     from database.db_setup import initialize_database
#     initialize_database()

#     print("\n" + "=" * 60)
#     print("DB LOGGER TEST RUN")
#     print("=" * 60 + "\n")

#     print("Inserting test ticket logs...")

#     test_data = [
#         {
#             "ticket_id"   : 1001,
#             "category"    : "app_install",
#             "priority"    : "high",
#             "action_taken": "Zoom installed via winget on PC-ICICI-0042",
#             "resolved_by" : "AI_AUTO",
#             "status"      : "RESOLVED",
#         },
#         {
#             "ticket_id"   : 1002,
#             "category"    : "antivirus",
#             "priority"    : "medium",
#             "action_taken": "AV definitions updated and full scan triggered",
#             "resolved_by" : "AI_AUTO",
#             "status"      : "RESOLVED",
#         },
#         {
#             "ticket_id"   : 1003,
#             "category"    : "hardware",
#             "priority"    : "high",
#             "action_taken": "Escalated to engineer — hardware inspection needed",
#             "resolved_by" : "ESCALATION",
#             "status"      : "ESCALATED",
#         },
#         {
#             "ticket_id"   : 1004,
#             "category"    : "network",
#             "priority"    : "high",
#             "action_taken": "KB VPN guide sent. Escalated to engineer.",
#             "resolved_by" : "KB+ESCALATION",
#             "status"      : "ESCALATED",
#         },
#         {
#             "ticket_id"   : 1005,
#             "category"    : "password_reset",
#             "priority"    : "high",
#             "action_taken": "AD password reset for amit.patel",
#             "resolved_by" : "AI_AUTO",
#             "status"      : "RESOLVED",
#         },
#     ]

#     for td in test_data:
#         ok = log_ticket_action(**td)
#         print(f"  Ticket #{td['ticket_id']} logged: {'OK' if ok else 'FAILED'}")

#     log_automation(
#         ticket_id     = 1001,
#         script_name   = "install_app.ps1",
#         machine_name  = "PC-ICICI-0042",
#         success       = True,
#         output        = "Zoom installed successfully.",
#         duration_secs = 45.3,
#     )

#     log_classification(
#         ticket_id        = 1001,
#         subject          = "Install Zoom on my laptop",
#         category         = "app_install",
#         priority         = "high",
#         can_auto_resolve = True,
#         suggested_action = "Push Zoom via SCCM",
#         confidence       = "high",
#     )

#     log_notification(
#         ticket_id  = 1001,
#         recipient  = "rahul.sharma@icici.com",
#         notif_type = "resolved",
#         subject    = "Install Zoom on my laptop",
#         success    = True,
#     )

#     print("\n--- Resolution Stats ---")
#     stats = get_resolution_stats()
#     print(f"  Total tickets    : {stats['total']}")
#     print(f"  Resolved         : {stats['resolved']}")
#     print(f"  Escalated        : {stats['escalated']}")
#     print(f"  AI auto-resolved : {stats['ai_resolved']}")
#     print(f"  Auto-resolve rate: {stats['auto_rate_pct']}%")
#     print(f"  Top category     : {stats['top_category']}")

#     print("\n--- Recent Ticket Logs ---")
#     logs = get_all_ticket_logs(limit=5)
#     for row in logs:
#         print(
#             f"  #{row['ticket_id']} | {row['category']:<18} | "
#             f"{row['status']:<10} | {row['resolved_by']}"
#         )

#     print("\nAll DB logger tests complete.")


import os
import sqlite3
import logging
from datetime import datetime, timezone
from database.db_setup import get_connection

log = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() == "true"


def _now() -> str:
    """
    Return current UTC time as formatted string.
    Uses timezone-aware datetime to avoid deprecation warning.

    Returns:
        Formatted datetime string e.g. '2026-05-07 10:30:00'
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def log_ticket_action(
    ticket_id   : int,
    category    : str,
    priority    : str,
    action_taken: str,
    resolved_by : str,
    status      : str,
) -> bool:
    """
    Log every ticket resolution action to the database.
    Called by orchestrator and demo_runner after every
    ticket is processed.

    If a log already exists for this ticket_id it is
    updated rather than inserting a duplicate row.

    Args:
        ticket_id    : Freshdesk ticket ID
        category     : AI classified category
        priority     : Ticket priority level
        action_taken : Description of what was done
        resolved_by  : Who/what resolved —
                       AI_AUTO | KB+ESCALATION |
                       ESCALATION | ENGINEER_QUEUE |
                       FORCE_ESCALATION | EMERGENCY
        status       : Final status — RESOLVED or ESCALATED

    Returns:
        True if logged successfully, False otherwise
    """
    now = _now()

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM ticket_logs
            WHERE ticket_id = ?
        """, (ticket_id,))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE ticket_logs
                SET category     = ?,
                    priority     = ?,
                    action_taken = ?,
                    resolved_by  = ?,
                    status       = ?,
                    updated_at   = ?
                WHERE ticket_id  = ?
            """, (
                category, priority, action_taken,
                resolved_by, status, now, ticket_id,
            ))
            log.debug(
                f"Updated existing log for ticket #{ticket_id}"
            )

        else:
            cursor.execute("""
                INSERT INTO ticket_logs (
                    ticket_id,    category,     priority,
                    action_taken, resolved_by,  status,
                    created_at,   updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id,    category,     priority,
                action_taken, resolved_by,  status,
                now,          now,
            ))
            log.debug(
                f"Inserted new log for ticket #{ticket_id}"
            )

        conn.commit()
        log.info(
            f"Logged ticket #{ticket_id} — "
            f"status: {status}, "
            f"resolved_by: {resolved_by}"
        )
        return True

    except sqlite3.Error as e:
        log.error(
            f"DB error logging ticket #{ticket_id}: {e}"
        )
        return False

    finally:
        conn.close()


def log_automation(
    ticket_id    : int,
    script_name  : str,
    machine_name : str,
    success      : bool,
    output       : str   = "",
    error        : str   = "",
    duration_secs: float = 0.0,
) -> bool:
    """
    Log every automation script execution to the database.
    Tracks which scripts ran, on which machines, and whether
    they succeeded. Used by runner.py and demo_runner.py.

    Args:
        ticket_id     : Freshdesk ticket ID
        script_name   : Name of the PowerShell script
        machine_name  : Target machine the script ran on
        success       : True if script exited with code 0
        output        : Script stdout output
        error         : Script stderr output
        duration_secs : How long the script took in seconds

    Returns:
        True if logged successfully, False otherwise
    """
    now = _now()

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO automation_logs (
                ticket_id,    script_name,  machine_name,
                success,      output,       error,
                duration_secs, ran_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            script_name,
            machine_name,
            1 if success else 0,
            (output[:2000] if output else ""),
            (error[:2000]  if error  else ""),
            round(duration_secs, 2),
            now,
        ))

        conn.commit()
        log.debug(
            f"Automation logged: ticket #{ticket_id}, "
            f"script: {script_name}, "
            f"success: {success}"
        )
        return True

    except sqlite3.Error as e:
        log.error(
            f"DB error logging automation "
            f"for ticket #{ticket_id}: {e}"
        )
        return False

    finally:
        conn.close()


def log_classification(
    ticket_id       : int,
    subject         : str,
    category        : str,
    priority        : str,
    can_auto_resolve: bool,
    suggested_action: str,
    confidence      : str,
) -> bool:
    """
    Log every AI/rule classification result to the database.
    Useful for auditing classifier accuracy over time and
    reviewing how tickets were routed.

    Args:
        ticket_id        : Freshdesk ticket ID
        subject          : Ticket subject line
        category         : Classified category
        priority         : Classified priority
        can_auto_resolve : Whether classifier said auto-resolvable
        suggested_action : Suggested action text
        confidence       : Classifier confidence — high/medium/low

    Returns:
        True if logged successfully, False otherwise
    """
    now = _now()

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO classification_logs (
                ticket_id,       subject,          category,
                priority,        can_auto_resolve,  suggested_action,
                confidence,      classified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            subject,
            category,
            priority,
            1 if can_auto_resolve else 0,
            suggested_action,
            confidence,
            now,
        ))

        conn.commit()
        log.debug(
            f"Classification logged for ticket #{ticket_id}"
        )
        return True

    except sqlite3.Error as e:
        log.error(
            f"DB error logging classification "
            f"for ticket #{ticket_id}: {e}"
        )
        return False

    finally:
        conn.close()


def log_notification(
    ticket_id : int,
    recipient : str,
    notif_type: str,
    subject   : str,
    success   : bool,
) -> bool:
    """
    Log every email notification attempt to the database.
    In demo mode logs simulated notifications.

    Args:
        ticket_id  : Freshdesk ticket ID
        recipient  : Email address notification was sent to
        notif_type : Type — resolved | escalated |
                     kb_guide_sent | in_progress |
                     password_reset | general
        subject    : Email subject line
        success    : True if email was sent successfully

    Returns:
        True if logged successfully, False otherwise
    """
    now = _now()

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO notification_logs (
                ticket_id, recipient, notif_type,
                subject,   success,   sent_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            recipient,
            notif_type,
            subject,
            1 if success else 0,
            now,
        ))

        conn.commit()
        log.debug(
            f"Notification logged: ticket #{ticket_id}, "
            f"to: {recipient}, "
            f"type: {notif_type}, "
            f"success: {success}"
        )
        return True

    except sqlite3.Error as e:
        log.error(
            f"DB error logging notification "
            f"for ticket #{ticket_id}: {e}"
        )
        return False

    finally:
        conn.close()


def get_all_ticket_logs(limit: int = 100) -> list:
    """
    Fetch recent ticket logs ordered by most recent first.
    Used by the Streamlit dashboard ticket log table.

    Args:
        limit : Maximum number of records to return

    Returns:
        List of ticket log dicts
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM   ticket_logs
            ORDER  BY created_at DESC
            LIMIT  ?
        """, (limit,))

        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    except sqlite3.Error as e:
        log.error(f"DB error fetching ticket logs: {e}")
        return []

    finally:
        conn.close()


def get_resolution_stats() -> dict:
    """
    Get overall resolution statistics for the dashboard.
    Returns counts, rates, and category breakdown.

    Returns:
        Dict with keys:
            total, resolved, escalated, ai_resolved,
            auto_rate_pct, top_category, category_counts
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM ticket_logs"
        )
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM ticket_logs
            WHERE  status = 'RESOLVED'
        """)
        resolved = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM ticket_logs
            WHERE  status = 'ESCALATED'
        """)
        escalated = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM ticket_logs
            WHERE  resolved_by = 'AI_AUTO'
        """)
        ai_resolved = cursor.fetchone()[0]

        auto_rate = (
            round(ai_resolved / total * 100, 1)
            if total > 0 else 0.0
        )

        cursor.execute("""
            SELECT   category, COUNT(*) AS count
            FROM     ticket_logs
            GROUP BY category
            ORDER BY count DESC
            LIMIT    1
        """)
        top_row      = cursor.fetchone()
        top_category = top_row["category"] if top_row else "N/A"

        cursor.execute("""
            SELECT   category, COUNT(*) AS count
            FROM     ticket_logs
            GROUP BY category
            ORDER BY count DESC
        """)
        category_counts = {
            row["category"]: row["count"]
            for row in cursor.fetchall()
        }

        cursor.execute("""
            SELECT COUNT(*) FROM ticket_logs
            WHERE  resolved_by IN ('KB+ESCALATION')
        """)
        kb_sent = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM ticket_logs
            WHERE  resolved_by IN (
                'FORCE_ESCALATION', 'EMERGENCY'
            )
        """)
        force_escalated = cursor.fetchone()[0]

        return {
            "total"           : total,
            "resolved"        : resolved,
            "escalated"       : escalated,
            "ai_resolved"     : ai_resolved,
            "auto_rate_pct"   : auto_rate,
            "top_category"    : top_category,
            "category_counts" : category_counts,
            "kb_sent"         : kb_sent,
            "force_escalated" : force_escalated,
        }

    except sqlite3.Error as e:
        log.error(f"DB error fetching resolution stats: {e}")
        return {
            "total"           : 0,
            "resolved"        : 0,
            "escalated"       : 0,
            "ai_resolved"     : 0,
            "auto_rate_pct"   : 0.0,
            "top_category"    : "N/A",
            "category_counts" : {},
            "kb_sent"         : 0,
            "force_escalated" : 0,
        }

    finally:
        conn.close()


def get_daily_stats(days: int = 7) -> list:
    """
    Get per-day ticket counts for the last N days.
    Used to draw the daily trend chart in the dashboard.

    Args:
        days : Number of past days to include

    Returns:
        List of dicts with keys: date, total, resolved, escalated
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT
                DATE(created_at) AS date,
                COUNT(*)         AS total,
                SUM(CASE WHEN status = 'RESOLVED'
                    THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN status = 'ESCALATED'
                    THEN 1 ELSE 0 END) AS escalated
            FROM   ticket_logs
            WHERE  created_at >= DATE('now', '-{days} days')
            GROUP  BY DATE(created_at)
            ORDER  BY date ASC
        """)

        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    except sqlite3.Error as e:
        log.error(f"DB error fetching daily stats: {e}")
        return []

    finally:
        conn.close()


def get_recent_automation_logs(limit: int = 50) -> list:
    """
    Fetch recent automation script execution logs.
    Used by the Streamlit dashboard automation table.

    Args:
        limit : Max number of records to return

    Returns:
        List of automation log dicts ordered by most recent
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM   automation_logs
            ORDER  BY ran_at DESC
            LIMIT  ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    except sqlite3.Error as e:
        log.error(f"DB error fetching automation logs: {e}")
        return []

    finally:
        conn.close()


def get_category_stats() -> list:
    """
    Get detailed stats broken down by category including
    resolution rate per category.
    Used for the dashboard category analysis section.

    Returns:
        List of dicts with category, total, resolved,
        escalated, auto_rate per category
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                category,
                COUNT(*)   AS total,
                SUM(CASE WHEN status = 'RESOLVED'
                    THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN status = 'ESCALATED'
                    THEN 1 ELSE 0 END) AS escalated,
                SUM(CASE WHEN resolved_by = 'AI_AUTO'
                    THEN 1 ELSE 0 END) AS ai_auto
            FROM   ticket_logs
            GROUP  BY category
            ORDER  BY total DESC
        """)

        rows = []
        for row in cursor.fetchall():
            d         = dict(row)
            total     = d["total"] or 1
            d["auto_rate_pct"] = round(
                d["ai_auto"] / total * 100, 1
            )
            rows.append(d)

        return rows

    except sqlite3.Error as e:
        log.error(f"DB error fetching category stats: {e}")
        return []

    finally:
        conn.close()


def get_recent_notifications(limit: int = 20) -> list:
    """
    Fetch recent email notification logs.

    Args:
        limit : Max number of records to return

    Returns:
        List of notification log dicts
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM   notification_logs
            ORDER  BY sent_at DESC
            LIMIT  ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    except sqlite3.Error as e:
        log.error(f"DB error fetching notification logs: {e}")
        return []

    finally:
        conn.close()


def get_ticket_by_id(ticket_id: int) -> dict | None:
    """
    Fetch a single ticket log entry by ticket ID.

    Args:
        ticket_id : Freshdesk ticket ID

    Returns:
        Ticket log dict or None if not found
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ticket_logs
            WHERE  ticket_id = ?
        """, (ticket_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    except sqlite3.Error as e:
        log.error(
            f"DB error fetching ticket #{ticket_id}: {e}"
        )
        return None

    finally:
        conn.close()


def delete_all_logs() -> bool:
    """
    Delete all logs from all tables.
    WARNING — this clears all data.
    Use only during development or to reset demo data.

    Returns:
        True if deleted successfully
    """
    tables = [
        "ticket_logs",
        "automation_logs",
        "classification_logs",
        "notification_logs",
    ]

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            log.warning(f"Cleared all rows from {table}")

        conn.commit()
        log.warning("All log tables cleared.")
        return True

    except sqlite3.Error as e:
        log.error(f"DB error clearing logs: {e}")
        return False

    finally:
        conn.close()


def get_db_summary() -> dict:
    """
    Return row counts for all tables.
    Useful for verifying data is being logged correctly.

    Returns:
        Dict of table_name -> row_count
    """
    tables = [
        "ticket_logs",
        "automation_logs",
        "classification_logs",
        "notification_logs",
    ]

    summary = {}

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        for table in tables:
            try:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table}"
                )
                summary[table] = cursor.fetchone()[0]
            except sqlite3.Error:
                summary[table] = "ERROR"

        return summary

    except sqlite3.Error as e:
        log.error(f"DB error fetching summary: {e}")
        return {t: "ERROR" for t in tables}

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
    )

    from database.db_setup import initialize_database
    initialize_database()

    print("\n" + "=" * 60)
    print("DB LOGGER TEST RUN")
    print("=" * 60 + "\n")

    print("Inserting test ticket logs...")

    test_data = [
        {
            "ticket_id"   : 2001,
            "category"    : "app_install",
            "priority"    : "high",
            "action_taken": "Zoom installed via winget on PC-ICICI-0042",
            "resolved_by" : "AI_AUTO",
            "status"      : "RESOLVED",
        },
        {
            "ticket_id"   : 2002,
            "category"    : "antivirus",
            "priority"    : "medium",
            "action_taken": "AV definitions updated. Full scan triggered.",
            "resolved_by" : "AI_AUTO",
            "status"      : "RESOLVED",
        },
        {
            "ticket_id"   : 2003,
            "category"    : "hardware",
            "priority"    : "high",
            "action_taken": "Escalated — hardware inspection needed.",
            "resolved_by" : "ESCALATION",
            "status"      : "ESCALATED",
        },
        {
            "ticket_id"   : 2004,
            "category"    : "network",
            "priority"    : "high",
            "action_taken": "KB VPN guide sent. Escalated to engineer.",
            "resolved_by" : "KB+ESCALATION",
            "status"      : "ESCALATED",
        },
        {
            "ticket_id"   : 2005,
            "category"    : "password_reset",
            "priority"    : "high",
            "action_taken": "AD password reset for user.",
            "resolved_by" : "AI_AUTO",
            "status"      : "RESOLVED",
        },
    ]

    for td in test_data:
        ok = log_ticket_action(**td)
        print(
            f"  Ticket #{td['ticket_id']} "
            f"[{td['category']:<18}] : "
            f"{'OK ✓' if ok else 'FAILED ✗'}"
        )

    print("\nLogging automation run...")
    log_automation(
        ticket_id     = 2001,
        script_name   = "install_app.ps1",
        machine_name  = "PC-ICICI-0042",
        success       = True,
        output        = "[DEMO] Zoom installed via winget.",
        duration_secs = 45.3,
    )
    print("  Automation log: OK ✓")

    print("\nLogging classification...")
    log_classification(
        ticket_id        = 2001,
        subject          = "Install Zoom on my laptop",
        category         = "app_install",
        priority         = "high",
        can_auto_resolve = True,
        suggested_action = "Push Zoom via SCCM or Intune.",
        confidence       = "high",
    )
    print("  Classification log: OK ✓")

    print("\nLogging notification...")
    log_notification(
        ticket_id  = 2001,
        recipient  = "rahul.sharma@icici.com",
        notif_type = "resolved",
        subject    = "Install Zoom on my laptop",
        success    = True,
    )
    print("  Notification log: OK ✓")

    print("\n--- Resolution Stats ---")
    stats = get_resolution_stats()
    print(f"  Total            : {stats['total']}")
    print(f"  Resolved         : {stats['resolved']}")
    print(f"  Escalated        : {stats['escalated']}")
    print(f"  AI auto-resolved : {stats['ai_resolved']}")
    print(f"  Auto-resolve rate: {stats['auto_rate_pct']}%")
    print(f"  Top category     : {stats['top_category']}")
    print(f"  KB guides sent   : {stats['kb_sent']}")
    print(f"  Force escalated  : {stats['force_escalated']}")

    print("\n--- Category Breakdown ---")
    cat_stats = get_category_stats()
    print(
        f"  {'CATEGORY':<20} "
        f"{'TOTAL':<8} "
        f"{'RESOLVED':<10} "
        f"{'ESCALATED':<11} "
        f"{'AUTO RATE'}"
    )
    print(f"  {'-'*20} {'-'*8} {'-'*10} {'-'*11} {'-'*9}")
    for cs in cat_stats:
        print(
            f"  {cs['category']:<20} "
            f"{cs['total']:<8} "
            f"{cs['resolved']:<10} "
            f"{cs['escalated']:<11} "
            f"{cs['auto_rate_pct']}%"
        )

    print("\n--- Recent Ticket Logs ---")
    logs = get_all_ticket_logs(limit=5)
    for row in logs:
        print(
            f"  #{row['ticket_id']:<6} "
            f"{row['category']:<20} "
            f"{row['status']:<10} "
            f"{row['resolved_by']}"
        )

    print("\n--- DB Table Summary ---")
    summary = get_db_summary()
    for table, count in summary.items():
        print(f"  {table:<30} : {count} rows")

    print("\n" + "=" * 60)
    print("All DB logger tests complete.")
    print("=" * 60 + "\n")