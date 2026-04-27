import os
import sys
import time
import signal
import logging
import schedule
from datetime import datetime, timezone
from pathlib  import Path
from dotenv   import load_dotenv

load_dotenv("config/.env")

from config.settings import (
    setup_logging,
    validate_settings,
    get_all_settings,
    FRESHDESK_POLL_INTERVAL_MINUTES,
    COMPANY_NAME,
    DRY_RUN_MODE,
    FEATURE_AUTO_RESOLVE,
    FEATURE_KB_SEARCH,
    FEATURE_AFTER_HOURS_REPLY,
    FEATURE_SENTIMENT_ANALYSIS,
    AUTO_RESOLVABLE_CATEGORIES,
    FORCE_ESCALATION_KEYWORDS,
    KB_AUTO_REBUILD,
)

setup_logging()
log = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() == "true"

if DEMO_MODE:
    log.info("DEMO MODE detected — importing demo runner...")
    from demo.demo_runner import run_demo
else:
    from ingestion.freshdesk_client import (
        fetch_new_tickets,
        close_ticket,
        update_ticket_status,
        add_internal_note,
        add_tag_to_ticket,
        test_connection,
    )
    from ingestion.ticket_parser import (
        parse_ticket,
        parse_tickets_bulk,
    )
    from classifier.ai_classifier import classify_ticket
    from classifier.category_rules import (
        classify_by_rules,
        _check_escalation_triggers,
        _is_after_business_hours,
    )
    from classifier.prompts import (
        get_estimated_resolution_time,
        get_category_description,
    )
    from knowledge_base.kb_indexer import (
        build_index,
        get_index_stats,
    )
    from knowledge_base.kb_search import (
        search_knowledge_base,
        is_kb_available,
        get_kb_stats,
    )
    from automation.runner import (
        run_automation,
        get_supported_categories,
    )
    from agent.orchestrator import orchestrate
    from agent.notifier     import notify_user
    from agent.escalation   import (
        escalate_ticket,
        escalate_with_full_details,
        escalate_high_priority,
        escalate_after_business_hours,
    )
    from database.db_setup  import initialize_database
    from database.db_logger import (
        log_ticket_action,
        log_classification,
        log_notification,
        get_resolution_stats,
    )


START_TIME         : datetime = datetime.now(timezone.utc)
PROCESSED_IDS      : set      = set()
TICKETS_PROCESSED  : int      = 0
TICKETS_RESOLVED   : int      = 0
TICKETS_ESCALATED  : int      = 0
POLL_COUNT         : int      = 0


def process_tickets() -> None:
    """
    Main polling function called by the scheduler every N minutes.
    Fetches new open tickets from Freshdesk, classifies each one,
    and routes to auto-resolution or escalation.

    Full flow per ticket:
        1.  Fetch raw tickets from Freshdesk
        2.  Parse into clean normalized dict
        3.  Skip if already processed this session
        4.  Classify with Claude AI (fallback to rules if API down)
        5.  Check for force-escalation triggers
        6.  Check if after business hours
        7.  If can auto-resolve → run automation via orchestrator
            a. Success  → close + notify user
            b. Failure  → search KB → send guide or escalate
        8.  If cannot auto-resolve → search KB + escalate
        9.  Log everything to database
    """
    global TICKETS_PROCESSED, TICKETS_RESOLVED, TICKETS_ESCALATED, POLL_COUNT

    POLL_COUNT += 1
    poll_start  = time.time()

    log.info("")
    log.info("=" * 60)
    log.info(
        f"POLL #{POLL_COUNT} — "
        f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M:%S UTC')}"
    )
    log.info("=" * 60)

    if DRY_RUN_MODE:
        log.warning(
            "DRY RUN MODE — no scripts will run, "
            "no tickets will be closed."
        )

    try:
        raw_tickets = fetch_new_tickets()
    except Exception as e:
        log.error(f"Failed to fetch tickets from Freshdesk: {e}")
        return

    if not raw_tickets:
        log.info("No new open tickets found.")
        return

    parsed_tickets = parse_tickets_bulk(raw_tickets)
    new_tickets    = [
        t for t in parsed_tickets
        if t["id"] not in PROCESSED_IDS and t["id"] != 0
    ]

    if not new_tickets:
        log.info("All fetched tickets already processed this session.")
        return

    log.info(f"Processing {len(new_tickets)} new ticket(s)...")

    after_hours = _is_after_business_hours()
    if after_hours:
        log.info("Current time is outside business hours.")

    for ticket in new_tickets:
        _process_single_ticket(ticket, after_hours)
        PROCESSED_IDS.add(ticket["id"])
        TICKETS_PROCESSED += 1

    poll_duration = round(time.time() - poll_start, 1)
    log.info("")
    log.info(
        f"Poll #{POLL_COUNT} complete in {poll_duration}s — "
        f"processed {len(new_tickets)} ticket(s)."
    )
    log.info("=" * 60)


def _process_single_ticket(ticket: dict, after_hours: bool) -> None:
    """
    Process one ticket end to end — classify, decide, act, log.

    Args:
        ticket      : Parsed ticket dict from ticket_parser
        after_hours : True if currently outside business hours
    """
    global TICKETS_RESOLVED, TICKETS_ESCALATED

    ticket_id      = ticket["id"]
    subject        = ticket["subject"]
    description    = ticket["description"]
    requester      = ticket["requester_email"]
    requester_name = ticket["requester_name"]
    machine        = ticket.get("machine_name", "UNKNOWN")
    urgency        = ticket.get("urgency_level", "medium")
    apps           = ticket.get("mentioned_apps", [])

    log.info("")
    log.info(f"┌─ Ticket #{ticket_id}: {subject[:55]}")
    log.info(f"│  Requester : {requester_name} ({requester})")
    log.info(f"│  Machine   : {machine}")
    log.info(f"│  Urgency   : {urgency}")
    log.info(f"│  Apps      : {apps or 'none detected'}")

    try:
        classification = classify_ticket(
            subject        = subject,
            description    = description,
            ticket_id      = ticket_id,
            machine_name   = machine,
            requester_name = requester_name,
        )
    except Exception as e:
        log.error(f"│  AI Classifier failed: {e}")
        log.warning("│  Falling back to rule-based classifier...")
        try:
            classification = classify_by_rules(subject, description)
        except Exception as e2:
            log.error(f"│  Rule classifier also failed: {e2}")
            _emergency_escalate(ticket, "Both classifiers failed.")
            TICKETS_ESCALATED += 1
            return

    category         = classification.get("category",         "other")
    priority         = classification.get("priority",         "medium")
    can_auto         = classification.get("can_auto_resolve", False)
    suggested_action = classification.get("suggested_action", "Manual review.")
    confidence       = classification.get("confidence",       "low")
    force_escalate   = classification.get("force_escalate",   False)

    force_escalate = (
        force_escalate
        or _check_escalation_triggers(f"{subject} {description}")
    )

    if urgency in ["critical", "high"] and priority == "medium":
        priority = "high"
        log.info("│  Priority boosted to 'high' based on urgency.")

    if machine == "UNKNOWN" and can_auto:
        can_auto = False
        log.warning(
            "│  Machine UNKNOWN — "
            "auto-resolve disabled."
        )

    if DRY_RUN_MODE:
        can_auto = False
        log.warning("│  Dry run — auto-resolve forced OFF.")

    if not FEATURE_AUTO_RESOLVE:
        can_auto = False
        log.info("│  FEATURE_AUTO_RESOLVE disabled.")

    log.info(f"│  Category  : {category}")
    log.info(f"│  Priority  : {priority}")
    log.info(f"│  Auto      : {can_auto}")
    log.info(f"│  Confidence: {confidence}")
    log.info(f"│  Escalate  : {force_escalate}")
    log.info(f"│  Action    : {suggested_action}")

    try:
        log_classification(
            ticket_id        = ticket_id,
            subject          = subject,
            category         = category,
            priority         = priority,
            can_auto_resolve = can_auto,
            suggested_action = suggested_action,
            confidence       = confidence,
        )
    except Exception as e:
        log.warning(f"│  Classification log failed: {e}")

    if force_escalate:
        log.warning(f"│  FORCE ESCALATION — critical keyword detected!")
        _handle_force_escalation(ticket, classification)
        TICKETS_ESCALATED += 1
        log.info(f"└─ Ticket #{ticket_id} → FORCE ESCALATED")
        return

    if after_hours and priority not in ["high", "urgent"]:
        log.info("│  After hours + non-critical → after-hours escalation.")
        escalate_after_business_hours(ticket, classification)
        TICKETS_ESCALATED += 1
        log.info(f"└─ Ticket #{ticket_id} → AFTER HOURS ESCALATED")
        return

    if priority in ["high", "urgent"] and not can_auto:
        log.warning("│  High priority + no auto-resolve → urgent escalation.")
        escalate_high_priority(ticket, classification)
        TICKETS_ESCALATED += 1
        log.info(f"└─ Ticket #{ticket_id} → HIGH PRIORITY ESCALATED")
        return

    if can_auto:
        resolved = _handle_auto_resolve(ticket, classification)
    else:
        resolved = _handle_manual_route(ticket, classification)

    if resolved:
        TICKETS_RESOLVED += 1
        log.info(f"└─ Ticket #{ticket_id} → RESOLVED ✓")
    else:
        TICKETS_ESCALATED += 1
        log.info(f"└─ Ticket #{ticket_id} → ESCALATED")


def _handle_auto_resolve(ticket: dict, classification: dict) -> bool:
    """
    Attempt auto-resolution via orchestrator.
    On success — close ticket and notify user.
    On failure — search KB and escalate.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        True if fully resolved, False if escalated
    """
    ticket_id        = ticket["id"]
    subject          = ticket["subject"]
    description      = ticket["description"]
    requester        = ticket["requester_email"]
    requester_name   = ticket["requester_name"]
    category         = classification["category"]
    priority         = classification["priority"]
    suggested_action = classification["suggested_action"]

    log.info(f"│  Attempting auto-resolution...")

    add_internal_note(
        ticket_id,
        f"[AI Ticket Resolver]\n"
        f"Auto-resolution started.\n"
        f"Category  : {category}\n"
        f"Priority  : {priority}\n"
        f"Machine   : {ticket.get('machine_name', 'UNKNOWN')}\n"
        f"Action    : {suggested_action}\n"
        f"Timestamp : "
        f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
    )

    success = orchestrate(ticket, classification)

    if success:
        log.info(f"│  Auto-resolution SUCCEEDED ✓")

        cat_label = get_category_description(category)

        resolution_msg = (
            f"Dear {requester_name},\n\n"
            f"Your ticket '{subject}' has been automatically resolved "
            f"by our AI support system.\n\n"
            f"Issue type   : {cat_label}\n"
            f"Action taken : {suggested_action}\n\n"
            f"Your issue has been fixed remotely. "
            f"Please restart your computer if needed and verify "
            f"the issue is resolved.\n\n"
            f"If the problem persists, please raise a new ticket.\n\n"
            f"Thank you,\n"
            f"IT Support Team\n"
            f"{COMPANY_NAME}"
        )

        if not DRY_RUN_MODE:
            close_ticket(ticket_id, suggested_action)

        notif_ok = notify_user(
            email      = requester,
            ticket_id  = ticket_id,
            subject    = subject,
            message    = resolution_msg,
            notif_type = "resolved",
        )

        try:
            log_notification(
                ticket_id  = ticket_id,
                recipient  = requester,
                notif_type = "resolved",
                subject    = subject,
                success    = notif_ok,
            )
        except Exception as e:
            log.warning(f"│  Notification log failed: {e}")

        add_tag_to_ticket(
            ticket_id,
            ["ai-resolved", f"cat-{category}", "auto-closed"]
        )

        log_ticket_action(
            ticket_id    = ticket_id,
            category     = category,
            priority     = priority,
            action_taken = suggested_action,
            resolved_by  = "AI_AUTO",
            status       = "RESOLVED",
        )

        return True

    else:
        log.warning(f"│  Auto-resolution FAILED — checking KB...")

        add_internal_note(
            ticket_id,
            f"[AI Ticket Resolver]\n"
            f"Auto-resolution FAILED.\n"
            f"Searching KB for: {subject}"
        )

        return _search_kb_and_escalate(
            ticket         = ticket,
            classification = classification,
            reason         = (
                f"Auto-resolution failed.\n"
                f"Suggested: {suggested_action}"
            ),
            tag            = "auto-failed",
        )


def _handle_manual_route(ticket: dict, classification: dict) -> bool:
    """
    Handle tickets that cannot be auto-resolved.
    Search KB first then escalate.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        Always False — ticket is escalated not resolved
    """
    ticket_id        = ticket["id"]
    category         = classification["category"]
    suggested_action = classification["suggested_action"]

    log.info(f"│  Cannot auto-resolve — searching KB...")

    add_internal_note(
        ticket_id,
        f"[AI Ticket Resolver]\n"
        f"Cannot auto-resolve — routing to engineer.\n"
        f"Category : {category}\n"
        f"Suggested: {suggested_action}"
    )

    return _search_kb_and_escalate(
        ticket         = ticket,
        classification = classification,
        reason         = (
            f"Requires engineer.\n"
            f"Category : {category}\n"
            f"Suggested: {suggested_action}"
        ),
        tag            = "manual-route",
    )


def _search_kb_and_escalate(
    ticket        : dict,
    classification: dict,
    reason        : str,
    tag           : str = "escalated",
) -> bool:
    """
    Search KB for self-help guide, send it to user if found,
    then escalate ticket to engineer queue.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict
        reason         : Why ticket is being escalated
        tag            : Freshdesk tag to apply

    Returns:
        Always False — ticket is escalated not resolved
    """
    ticket_id        = ticket["id"]
    subject          = ticket["subject"]
    description      = ticket["description"]
    requester        = ticket["requester_email"]
    requester_name   = ticket["requester_name"]
    category         = classification["category"]
    priority         = classification["priority"]
    suggested_action = classification["suggested_action"]

    kb_guide    = None
    resolved_by = "ESCALATION"

    if FEATURE_KB_SEARCH and is_kb_available():
        log.info(f"│  Searching KB...")
        try:
            kb_guide = search_knowledge_base(description)
        except Exception as e:
            log.warning(f"│  KB search error: {e}")

    if kb_guide:
        log.info(f"│  KB guide found — sending to {requester}.")

        kb_message = (
            f"Dear {requester_name},\n\n"
            f"Thank you for contacting IT Support "
            f"regarding '{subject}'.\n\n"
            f"We found a self-help guide that may help:\n\n"
            f"{'─' * 50}\n"
            f"{kb_guide}\n"
            f"{'─' * 50}\n\n"
            f"An engineer will also follow up shortly.\n\n"
            f"Thank you,\n"
            f"IT Support Team\n"
            f"{COMPANY_NAME}"
        )

        notif_ok = notify_user(
            email      = requester,
            ticket_id  = ticket_id,
            subject    = subject,
            message    = kb_message,
            notif_type = "kb_guide_sent",
        )

        try:
            log_notification(
                ticket_id  = ticket_id,
                recipient  = requester,
                notif_type = "kb_guide_sent",
                subject    = subject,
                success    = notif_ok,
            )
        except Exception as e:
            log.warning(f"│  Notification log failed: {e}")

        reason      += "\nKB guide sent to user."
        resolved_by  = "KB+ESCALATION"

    else:
        if FEATURE_KB_SEARCH:
            log.info(f"│  No KB guide found.")

    escalate_with_full_details(
        ticket         = ticket,
        classification = classification,
        reason         = reason,
    )

    add_tag_to_ticket(
        ticket_id,
        [tag, f"cat-{category}", "ai-processed"]
    )

    log_ticket_action(
        ticket_id    = ticket_id,
        category     = category,
        priority     = priority,
        action_taken = (
            "KB guide sent + escalated."
            if kb_guide else
            f"Escalated — {suggested_action}"
        ),
        resolved_by  = resolved_by,
        status       = "ESCALATED",
    )

    return False


def _handle_force_escalation(
    ticket        : dict,
    classification: dict,
) -> None:
    """
    Handle force-escalation for critical keyword tickets
    like ransomware, data breach, executive mentions.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict
    """
    ticket_id = ticket["id"]
    category  = classification.get("category", "other")

    classification["priority"]         = "urgent"
    classification["can_auto_resolve"] = False

    add_internal_note(
        ticket_id,
        f"[AI Ticket Resolver — FORCE ESCALATION]\n"
        f"Critical keyword detected in ticket.\n"
        f"Immediate engineer attention required.\n"
        f"Timestamp: "
        f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
    )

    escalate_high_priority(ticket, classification)

    log_ticket_action(
        ticket_id    = ticket_id,
        category     = category,
        priority     = "urgent",
        action_taken = "Force-escalated — critical keyword detected.",
        resolved_by  = "FORCE_ESCALATION",
        status       = "ESCALATED",
    )


def _emergency_escalate(ticket: dict, reason: str) -> None:
    """
    Last-resort escalation when all classifiers fail.
    Ensures no ticket is ever silently dropped.

    Args:
        ticket : Parsed ticket dict
        reason : Why emergency escalation was triggered
    """
    ticket_id = ticket.get("id", 0)
    log.error(f"│  EMERGENCY ESCALATE #{ticket_id}: {reason}")

    try:
        add_internal_note(
            ticket_id,
            f"[EMERGENCY ESCALATION]\n"
            f"Reason: {reason}\n"
            f"Cannot classify — manual review needed.\n"
            f"Timestamp: "
            f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
        )
        update_ticket_status(
            ticket_id, "pending"
        )
        add_tag_to_ticket(
            ticket_id,
            ["emergency-escalation", "classifier-failed"]
        )
    except Exception as e:
        log.error(f"│  Emergency note failed: {e}")

    try:
        log_ticket_action(
            ticket_id    = ticket_id,
            category     = "other",
            priority     = "high",
            action_taken = reason,
            resolved_by  = "EMERGENCY",
            status       = "ESCALATED",
        )
    except Exception as e:
        log.error(f"│  Emergency DB log failed: {e}")


def _startup_checks() -> bool:
    """
    Run all pre-flight checks before the scheduler starts.
    Tests settings, DB, Freshdesk connection, and KB status.

    Returns:
        True if all required checks pass, False otherwise
    """
    log.info("")
    log.info("=" * 60)
    log.info("AI TICKET RESOLVER — STARTING UP (LIVE MODE)")
    log.info(f"Company  : {COMPANY_NAME}")
    log.info(
        f"Started  : "
        f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M:%S UTC')}"
    )
    log.info(f"Dry Run  : {DRY_RUN_MODE}")
    log.info("=" * 60)

    log.info("Step 1/5 — Validating settings...")
    validation = validate_settings()
    if not validation["valid"]:
        for err in validation["errors"]:
            log.error(f"  CONFIG ERROR   : {err}")
        log.error("Fix the errors above in config/.env and restart.")
        return False
    for warn in validation["warnings"]:
        log.warning(f"  CONFIG WARNING : {warn}")
    log.info("Settings validation passed.")

    log.info("Step 2/5 — Initializing database...")
    try:
        initialize_database()
        log.info("Database initialized.")
    except Exception as e:
        log.error(f"Database init failed: {e}")
        return False

    log.info("Step 3/5 — Testing Freshdesk connection...")
    try:
        fd_ok = test_connection()
        if fd_ok:
            log.info("Freshdesk connection OK.")
        else:
            log.error(
                "Freshdesk connection FAILED. "
                "Check FRESHDESK_DOMAIN and FRESHDESK_API_KEY in .env"
            )
            return False
    except Exception as e:
        log.error(f"Freshdesk test error: {e}")
        return False

    log.info("Step 4/5 — Checking knowledge base...")
    try:
        if KB_AUTO_REBUILD:
            log.info("KB_AUTO_REBUILD=true — rebuilding...")
            build_index(force_rebuild=True)
        kb_ok    = is_kb_available()
        kb_stats = get_kb_stats()
        if kb_ok:
            log.info(
                f"KB ready — "
                f"{kb_stats.get('total_chunks', 0)} chunks."
            )
        else:
            log.warning(
                "KB not indexed. "
                "Run: python knowledge_base/kb_indexer.py"
            )
    except Exception as e:
        log.warning(f"KB check failed: {e}")

    log.info("Step 5/5 — Startup summary...")
    _print_startup_summary()
    log.info("All startup checks passed.")
    return True


def _print_startup_summary() -> None:
    """Print configuration summary at startup."""
    try:
        kb_stats = get_kb_stats()
        db_stats = get_resolution_stats()
    except Exception:
        kb_stats = {}
        db_stats = {}

    log.info("")
    log.info("┌─────────────────────────────────────────────────┐")
    log.info("│        SYSTEM CONFIGURATION SUMMARY            │")
    log.info("├─────────────────────────────────────────────────┤")
    log.info(
        f"│  Poll interval     : "
        f"every {FRESHDESK_POLL_INTERVAL_MINUTES} minute(s)"
    )
    log.info(
        f"│  Auto-resolve      : "
        f"{'ON' if FEATURE_AUTO_RESOLVE else 'OFF'}"
    )
    log.info(
        f"│  KB search         : "
        f"{'ON' if FEATURE_KB_SEARCH else 'OFF'}"
    )
    log.info(
        f"│  After-hours reply : "
        f"{'ON' if FEATURE_AFTER_HOURS_REPLY else 'OFF'}"
    )
    log.info(
        f"│  Dry run mode      : "
        f"{'ON' if DRY_RUN_MODE else 'OFF'}"
    )
    log.info(
        f"│  KB chunks         : "
        f"{kb_stats.get('total_chunks', 0)}"
    )
    log.info(
        f"│  Tickets (all time): "
        f"{db_stats.get('total', 0)}"
    )
    log.info(
        f"│  Auto-rate (all)   : "
        f"{db_stats.get('auto_rate_pct', 0.0):.1f}%"
    )
    log.info("└─────────────────────────────────────────────────┘")
    log.info("")


def _print_session_summary() -> None:
    """Print session stats on shutdown."""
    uptime_mins = round(
        (datetime.now(timezone.utc) - START_TIME)
        .total_seconds() / 60,
        1
    )

    log.info("")
    log.info("=" * 60)
    log.info("SESSION SUMMARY")
    log.info("=" * 60)
    log.info(f"  Uptime           : {uptime_mins} minutes")
    log.info(f"  Poll cycles      : {POLL_COUNT}")
    log.info(f"  Tickets processed: {TICKETS_PROCESSED}")
    log.info(f"  Tickets resolved : {TICKETS_RESOLVED}")
    log.info(f"  Tickets escalated: {TICKETS_ESCALATED}")
    if TICKETS_PROCESSED > 0:
        rate = round(
            TICKETS_RESOLVED / TICKETS_PROCESSED * 100, 1
        )
        log.info(f"  Session rate     : {rate}%")
    log.info("=" * 60)


def _signal_handler(sig, frame) -> None:
    """Handle Ctrl+C and SIGTERM gracefully."""
    log.info("")
    log.info("Shutdown signal received. Stopping...")
    if not DEMO_MODE:
        _print_session_summary()
    log.info("AI Ticket Resolver stopped. Goodbye.")
    sys.exit(0)


def main() -> None:
    """
    Main entry point.

    If DEMO_MODE=true in .env:
        → Runs the full demo with 10 sample tickets
        → No real API keys needed
        → Everything is simulated

    If DEMO_MODE=false in .env:
        → Runs in live mode
        → Requires real Freshdesk + Anthropic API keys
        → Polls Freshdesk every N minutes
    """
    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    if DEMO_MODE:
        log.info("")
        log.info("=" * 60)
        log.info("DEMO MODE — starting demo runner...")
        log.info("=" * 60)
        run_demo()
        log.info("")
        log.info("Demo complete.")
        log.info(
            "To run the dashboard: "
            "streamlit run dashboard/app.py"
        )
        log.info(
            "To switch to live mode: "
            "set DEMO_MODE=false in config/.env"
        )
        return

    checks_passed = _startup_checks()

    if not checks_passed:
        log.error(
            "Startup checks failed. "
            "Fix errors in config/.env and restart.\n"
            "Tip: Set DEMO_MODE=true to run without real API keys."
        )
        sys.exit(1)

    log.info("Running first poll immediately...")
    process_tickets()

    schedule.every(
        FRESHDESK_POLL_INTERVAL_MINUTES
    ).minutes.do(process_tickets)

    log.info(
        f"Scheduler running — polling every "
        f"{FRESHDESK_POLL_INTERVAL_MINUTES} minute(s). "
        f"Press Ctrl+C to stop."
    )

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()