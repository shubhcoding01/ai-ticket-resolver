# import schedule
# import time
# import logging
# from dotenv import load_dotenv
# import os

# from ingestion.freshdesk_client import fetch_new_tickets, update_ticket_status, close_ticket
# from ingestion.ticket_parser import parse_ticket
# from classifier.ai_classifier import classify_ticket
# from knowledge_base.kb_search import search_knowledge_base
# from automation.runner import run_automation
# from agent.orchestrator import orchestrate
# from agent.notifier import notify_user
# from agent.escalation import escalate_ticket
# from database.db_logger import log_ticket_action
# from database.db_setup import initialize_database

# load_dotenv()

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler("ticket_resolver.log"),
#         logging.StreamHandler()
#     ]
# )
# log = logging.getLogger(__name__)

# POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", 5))


# def process_tickets():
#     log.info("========== Polling for new tickets ==========")

#     try:
#         raw_tickets = fetch_new_tickets()
#     except Exception as e:
#         log.error(f"Failed to fetch tickets from Freshdesk: {e}")
#         return

#     if not raw_tickets:
#         log.info("No new tickets found.")
#         return

#     log.info(f"Found {len(raw_tickets)} new ticket(s). Processing...")

#     for raw in raw_tickets:
#         ticket = parse_ticket(raw)
#         ticket_id   = ticket["id"]
#         subject     = ticket["subject"]
#         description = ticket["description"]
#         requester   = ticket["requester_email"]
#         machine     = ticket.get("machine_name", "UNKNOWN")

#         log.info(f"--- Ticket #{ticket_id}: {subject} ---")

#         try:
#             classification = classify_ticket(subject, description)
#         except Exception as e:
#             log.error(f"Classifier failed for ticket #{ticket_id}: {e}")
#             escalate_ticket(ticket_id, "Classifier error — needs manual review.")
#             continue

#         category        = classification["category"]
#         priority        = classification["priority"]
#         can_auto        = classification["can_auto_resolve"]
#         suggested_action = classification["suggested_action"]

#         log.info(f"  Category : {category}")
#         log.info(f"  Priority : {priority}")
#         log.info(f"  Auto-resolve: {can_auto}")
#         log.info(f"  Suggested action: {suggested_action}")

#         if can_auto:
#             log.info(f"  Attempting auto-resolution for ticket #{ticket_id}...")
#             success = orchestrate(ticket, classification)

#             if success:
#                 close_ticket(ticket_id, f"Auto-resolved: {suggested_action}")
#                 notify_user(
#                     email=requester,
#                     ticket_id=ticket_id,
#                     subject=subject,
#                     message=f"Your ticket has been automatically resolved.\n\nAction taken: {suggested_action}\n\nIf the issue persists, please raise a new ticket."
#                 )
#                 log.info(f"  Ticket #{ticket_id} auto-resolved and closed.")
#                 log_ticket_action(
#                     ticket_id=ticket_id,
#                     category=category,
#                     priority=priority,
#                     action_taken=suggested_action,
#                     resolved_by="AI_AUTO",
#                     status="RESOLVED"
#                 )

#             else:
#                 log.warning(f"  Auto-resolution failed for ticket #{ticket_id}. Checking knowledge base...")
#                 kb_guide = search_knowledge_base(description)

#                 if kb_guide:
#                     notify_user(
#                         email=requester,
#                         ticket_id=ticket_id,
#                         subject=subject,
#                         message=f"We found a self-help guide for your issue:\n\n{kb_guide}\n\nIf this does not help, an engineer will follow up."
#                     )
#                     escalate_ticket(ticket_id, f"Auto-resolve failed. KB guide sent. Needs engineer review.\nSuggested: {suggested_action}")
#                     log.info(f"  KB guide sent. Ticket #{ticket_id} escalated.")
#                     log_ticket_action(
#                         ticket_id=ticket_id,
#                         category=category,
#                         priority=priority,
#                         action_taken="KB guide sent + escalated",
#                         resolved_by="KB+ESCALATION",
#                         status="ESCALATED"
#                     )
#                 else:
#                     escalate_ticket(ticket_id, f"Auto-resolve failed. No KB guide found.\nSuggested: {suggested_action}")
#                     log.info(f"  Ticket #{ticket_id} escalated to engineer.")
#                     log_ticket_action(
#                         ticket_id=ticket_id,
#                         category=category,
#                         priority=priority,
#                         action_taken="Escalated — no KB match",
#                         resolved_by="ESCALATION",
#                         status="ESCALATED"
#                     )

#         else:
#             log.info(f"  Ticket #{ticket_id} marked as complex. Searching knowledge base...")
#             kb_guide = search_knowledge_base(description)

#             if kb_guide:
#                 notify_user(
#                     email=requester,
#                     ticket_id=ticket_id,
#                     subject=subject,
#                     message=f"Here is a self-help guide that may resolve your issue:\n\n{kb_guide}\n\nAn engineer will also follow up shortly."
#                 )
#                 log.info(f"  KB guide sent to {requester}.")

#             escalate_ticket(ticket_id, f"Requires engineer. AI suggestion: {suggested_action}")
#             log.info(f"  Ticket #{ticket_id} escalated to engineer queue.")
#             log_ticket_action(
#                 ticket_id=ticket_id,
#                 category=category,
#                 priority=priority,
#                 action_taken=f"Escalated — {suggested_action}",
#                 resolved_by="ENGINEER_QUEUE",
#                 status="ESCALATED"
#             )

#     log.info("========== Polling cycle complete ==========\n")


# def main():
#     log.info("AI Ticket Resolver starting up...")
#     log.info(f"Poll interval: every {POLL_INTERVAL_MINUTES} minute(s)")

#     initialize_database()
#     log.info("Database initialized.")

#     process_tickets()

#     schedule.every(POLL_INTERVAL_MINUTES).minutes.do(process_tickets)

#     log.info("Scheduler running. Press Ctrl+C to stop.")
#     while True:
#         schedule.run_pending()
#         time.sleep(30)


# if __name__ == "__main__":
#     main()

import os
import sys
import time
import signal
import logging
import schedule
from datetime import datetime
from dotenv   import load_dotenv

load_dotenv()

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
    FEATURE_TICKET_QUALITY_CHECK,
    AUTO_RESOLVABLE_CATEGORIES,
    FORCE_ESCALATION_KEYWORDS,
    KB_AUTO_REBUILD,
)

setup_logging()
log = logging.getLogger(__name__)


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
from classifier.ai_classifier import (
    classify_ticket,
    batch_classify,
)
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
from agent.orchestrator  import orchestrate
from agent.notifier      import notify_user
from agent.escalation    import (
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


PROCESSED_TICKET_IDS: set = set()
START_TIME: datetime       = datetime.utcnow()
TICKETS_PROCESSED: int     = 0
TICKETS_RESOLVED: int      = 0
TICKETS_ESCALATED: int     = 0
POLL_COUNT: int            = 0


def process_tickets() -> None:
    """
    Main polling function — runs on every schedule tick.
    Fetches new open tickets from Freshdesk, classifies each
    one using the AI classifier, then routes to auto-resolution
    or escalation based on the classification result.

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
    log.info(f"POLL #{POLL_COUNT} — {datetime.utcnow().strftime('%d %b %Y %H:%M:%S UTC')}")
    log.info("=" * 60)

    if DRY_RUN_MODE:
        log.warning("DRY RUN MODE ACTIVE — no scripts will run, no tickets will be closed.")

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
        if t["id"] not in PROCESSED_TICKET_IDS and t["id"] != 0
    ]

    if not new_tickets:
        log.info("All fetched tickets already processed this session.")
        return

    log.info(f"Processing {len(new_tickets)} ticket(s)...")

    after_hours = _is_after_business_hours()
    if after_hours:
        log.info("Current time is outside business hours.")

    for ticket in new_tickets:
        _process_single_ticket(ticket, after_hours)
        PROCESSED_TICKET_IDS.add(ticket["id"])
        TICKETS_PROCESSED += 1

    poll_duration = round(time.time() - poll_start, 1)

    log.info("")
    log.info(f"Poll #{POLL_COUNT} complete in {poll_duration}s — "
             f"processed {len(new_tickets)} ticket(s).")
    log.info("=" * 60)


def _process_single_ticket(ticket: dict, after_hours: bool) -> None:
    """
    Process a single ticket end to end.
    Called by process_tickets() for each ticket in the batch.

    Args:
        ticket      : Parsed ticket dict from ticket_parser
        after_hours : True if current time is outside business hours
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
        log.error(f"│  Classifier error for ticket #{ticket_id}: {e}")
        log.warning(f"│  Falling back to rule-based classifier...")
        try:
            classification = classify_by_rules(subject, description)
        except Exception as e2:
            log.error(f"│  Rule classifier also failed: {e2}")
            _emergency_escalate(ticket, "Both AI and rule classifiers failed.")
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
        log.info(f"│  Priority boosted to 'high' based on urgency signals.")

    if machine == "UNKNOWN" and can_auto:
        can_auto = False
        log.warning(
            f"│  Machine name UNKNOWN — "
            "auto-resolve disabled (cannot run remote scripts)."
        )

    if DRY_RUN_MODE:
        can_auto = False
        log.warning("│  Dry run mode — auto-resolve forced OFF.")

    if not FEATURE_AUTO_RESOLVE:
        can_auto = False
        log.info("│  FEATURE_AUTO_RESOLVE disabled — routing to escalation.")

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
        log.warning(f"│  Classification logging failed: {e}")

    if force_escalate:
        log.warning(f"│  Force escalation triggered for ticket #{ticket_id}!")
        _handle_force_escalation(ticket, classification)
        TICKETS_ESCALATED += 1
        return

    if after_hours and priority not in ["high", "urgent"]:
        log.info(
            f"│  After hours + non-critical — "
            "sending acknowledgement and escalating."
        )
        escalate_after_business_hours(ticket, classification)
        TICKETS_ESCALATED += 1
        return

    if priority in ["high", "urgent"] and not can_auto:
        log.warning(
            f"│  High priority ticket #{ticket_id} — "
            "escalating with full details."
        )
        resolved = False
        escalate_high_priority(ticket, classification)
        TICKETS_ESCALATED += 1
        return

    if can_auto:
        resolved = _handle_auto_resolve(ticket, classification)
    else:
        resolved = _handle_manual_route(ticket, classification)

    if resolved:
        TICKETS_RESOLVED += 1
    else:
        TICKETS_ESCALATED += 1

    log.info(
        f"└─ Ticket #{ticket_id} — "
        f"{'RESOLVED' if resolved else 'ESCALATED'}"
    )


def _handle_auto_resolve(ticket: dict, classification: dict) -> bool:
    """
    Attempt to auto-resolve a ticket using automation scripts.
    If automation succeeds — close ticket and notify user.
    If automation fails — search KB and escalate.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        True if ticket was fully auto-resolved, False otherwise
    """
    ticket_id      = ticket["id"]
    subject        = ticket["subject"]
    description    = ticket["description"]
    requester      = ticket["requester_email"]
    requester_name = ticket["requester_name"]
    category       = classification["category"]
    priority       = classification["priority"]
    suggested_action = classification["suggested_action"]

    log.info(f"│  Attempting auto-resolution for ticket #{ticket_id}...")

    add_internal_note(
        ticket_id,
        f"[AI Ticket Resolver]\n"
        f"Auto-resolution started.\n"
        f"Category   : {category}\n"
        f"Priority   : {priority}\n"
        f"Machine    : {ticket.get('machine_name', 'UNKNOWN')}\n"
        f"Action     : {suggested_action}\n"
        f"Timestamp  : {datetime.utcnow().strftime('%d %b %Y %H:%M UTC')}"
    )

    success = orchestrate(ticket, classification)

    if success:
        log.info(f"│  Auto-resolution SUCCEEDED for ticket #{ticket_id}.")

        est_time = get_estimated_resolution_time(category, priority)
        cat_label = get_category_description(category)

        resolution_msg = (
            f"Dear {requester_name},\n\n"
            f"Your ticket '{subject}' has been automatically resolved "
            f"by our AI support system.\n\n"
            f"Issue type   : {cat_label}\n"
            f"Action taken : {suggested_action}\n\n"
            f"Your issue has been fixed remotely on your machine. "
            f"Please restart your computer if needed and verify the "
            f"issue is resolved.\n\n"
            f"If the problem persists, please raise a new support ticket "
            f"and our team will assist you promptly.\n\n"
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
            log.warning(f"│  Notification logging failed: {e}")

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
        log.warning(
            f"│  Auto-resolution FAILED for ticket #{ticket_id}. "
            "Checking knowledge base..."
        )

        add_internal_note(
            ticket_id,
            f"[AI Ticket Resolver]\n"
            f"Auto-resolution failed.\n"
            f"Searching KB for: {subject}"
        )

        return _search_kb_and_escalate(
            ticket         = ticket,
            classification = classification,
            reason         = (
                f"Auto-resolution failed.\n"
                f"Suggested action: {suggested_action}"
            ),
            tag            = "auto-failed",
        )


def _handle_manual_route(ticket: dict, classification: dict) -> bool:
    """
    Handle tickets that cannot be auto-resolved.
    Searches the KB first then escalates to the engineer queue.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        Always False — ticket is escalated not resolved
    """
    ticket_id      = ticket["id"]
    category       = classification["category"]
    suggested_action = classification["suggested_action"]

    log.info(
        f"│  Ticket #{ticket_id} cannot be auto-resolved. "
        "Searching KB..."
    )

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
            f"Requires engineer review.\n"
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
    Search the knowledge base for a self-help guide.
    If found — send it to the user.
    Then escalate the ticket to the engineer queue regardless.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict
        reason         : Why the ticket is being escalated
        tag            : Freshdesk tag to apply

    Returns:
        Always False — ticket is escalated not resolved
    """
    ticket_id      = ticket["id"]
    subject        = ticket["subject"]
    description    = ticket["description"]
    requester      = ticket["requester_email"]
    requester_name = ticket["requester_name"]
    category       = classification["category"]
    priority       = classification["priority"]
    suggested_action = classification["suggested_action"]

    kb_guide = None

    if FEATURE_KB_SEARCH and is_kb_available():
        log.info(f"│  Searching KB for ticket #{ticket_id}...")
        try:
            kb_guide = search_knowledge_base(description)
        except Exception as e:
            log.warning(f"│  KB search failed: {e}")

    if kb_guide:
        log.info(f"│  KB guide found — sending to {requester}.")

        kb_message = (
            f"Dear {requester_name},\n\n"
            f"Thank you for contacting IT Support regarding '{subject}'.\n\n"
            f"We found a self-help guide that may resolve your issue:\n\n"
            f"{'─' * 50}\n"
            f"{kb_guide}\n"
            f"{'─' * 50}\n\n"
            f"Please follow the steps above and let us know if this "
            f"resolves the issue.\n\n"
            f"An engineer from our team will also review your ticket "
            f"and follow up if needed.\n\n"
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
            log.warning(f"│  Notification logging failed: {e}")

        escalation_reason = (
            f"{reason}\n"
            f"KB self-help guide was sent to user.\n"
            f"Engineer — please verify issue is resolved."
        )
        resolved_by = "KB+ESCALATION"

    else:
        if FEATURE_KB_SEARCH:
            log.info(f"│  No KB guide found for ticket #{ticket_id}.")
        escalation_reason = reason
        resolved_by       = "ESCALATION"

    escalate_with_full_details(
        ticket         = ticket,
        classification = classification,
        reason         = escalation_reason,
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
            f"KB guide sent + escalated."
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
    Handle tickets that triggered a force-escalation keyword
    such as ransomware, data breach, or executive mention.
    Sets priority to urgent and notifies engineer immediately.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict
    """
    ticket_id = ticket["id"]
    category  = classification.get("category", "other")
    priority  = classification.get("priority", "high")

    log.warning(
        f"│  FORCE ESCALATION — ticket #{ticket_id} "
        f"contains critical trigger keyword."
    )

    classification["priority"]         = "urgent"
    classification["can_auto_resolve"] = False

    add_internal_note(
        ticket_id,
        f"[AI Ticket Resolver — FORCE ESCALATION]\n"
        f"This ticket triggered a critical escalation keyword.\n"
        f"Immediate engineer attention required.\n"
        f"Timestamp: {datetime.utcnow().strftime('%d %b %Y %H:%M UTC')}"
    )

    escalate_high_priority(ticket, classification)

    log_ticket_action(
        ticket_id    = ticket_id,
        category     = category,
        priority     = "urgent",
        action_taken = "Force-escalated due to critical keyword trigger.",
        resolved_by  = "FORCE_ESCALATION",
        status       = "ESCALATED",
    )


def _emergency_escalate(ticket: dict, reason: str) -> None:
    """
    Emergency fallback escalation when both the AI classifier
    and rule classifier fail completely. Ensures the ticket is
    never silently dropped even if all systems fail.

    Args:
        ticket : Parsed ticket dict
        reason : Why emergency escalation was triggered
    """
    ticket_id = ticket.get("id", 0)
    log.error(
        f"│  EMERGENCY ESCALATE for ticket #{ticket_id}: {reason}"
    )

    try:
        add_internal_note(
            ticket_id,
            f"[AI Ticket Resolver — EMERGENCY]\n"
            f"Reason: {reason}\n"
            f"This ticket could not be classified. "
            f"Please review manually.\n"
            f"Timestamp: {datetime.utcnow().strftime('%d %b %Y %H:%M UTC')}"
        )
        update_ticket_status(ticket_id, "pending")
        add_tag_to_ticket(ticket_id, ["emergency-escalation", "classifier-failed"])
    except Exception as e:
        log.error(f"│  Emergency escalation also failed: {e}")

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
    Validates settings, tests API connections, checks KB status,
    and prints a startup summary to the terminal.

    Returns:
        True if all required checks pass, False otherwise
    """
    log.info("")
    log.info("=" * 60)
    log.info(f"AI TICKET RESOLVER — STARTING UP")
    log.info(f"Company  : {COMPANY_NAME}")
    log.info(
        f"Started  : "
        f"{START_TIME.strftime('%d %b %Y %H:%M:%S UTC')}"
    )
    log.info(f"Dry Run  : {DRY_RUN_MODE}")
    log.info("=" * 60)

    log.info("Step 1/5 — Validating settings...")
    validation = validate_settings()
    if not validation["valid"]:
        for err in validation["errors"]:
            log.error(f"  CONFIG ERROR: {err}")
        log.error(
            "Fix the above errors in config/.env and restart."
        )
        return False

    for warn in validation["warnings"]:
        log.warning(f"  CONFIG WARNING: {warn}")

    log.info("Settings validation passed.")

    log.info("Step 2/5 — Initializing database...")
    try:
        initialize_database()
        log.info("Database initialized.")
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        return False

    log.info("Step 3/5 — Testing Freshdesk connection...")
    try:
        fd_ok = test_connection()
        if fd_ok:
            log.info("Freshdesk connection OK.")
        else:
            log.error(
                "Freshdesk connection FAILED. "
                "Check FRESHDESK_DOMAIN and FRESHDESK_API_KEY."
            )
            return False
    except Exception as e:
        log.error(f"Freshdesk connection test error: {e}")
        return False

    log.info("Step 4/5 — Checking knowledge base...")
    try:
        if KB_AUTO_REBUILD:
            log.info("KB_AUTO_REBUILD=true — rebuilding index...")
            build_index(force_rebuild=True)

        kb_ok    = is_kb_available()
        kb_stats = get_kb_stats()

        if kb_ok:
            log.info(
                f"KB ready — "
                f"{kb_stats.get('total_chunks', 0)} chunks indexed."
            )
        else:
            log.warning(
                "KB index not found or empty. "
                "Run: python knowledge_base/kb_indexer.py"
            )
            log.warning("KB search will be skipped until index is built.")

    except Exception as e:
        log.warning(f"KB check failed: {e}")

    log.info("Step 5/5 — Printing startup summary...")
    _print_startup_summary()

    log.info("All startup checks passed.")
    return True


def _print_startup_summary() -> None:
    """
    Print a clear configuration summary table at startup
    so the operator can verify everything is set correctly.
    """
    kb_stats  = get_kb_stats()
    db_stats  = get_resolution_stats()

    log.info("")
    log.info("┌─────────────────────────────────────────────────┐")
    log.info("│          SYSTEM CONFIGURATION SUMMARY          │")
    log.info("├─────────────────────────────────────────────────┤")
    log.info(f"│  Poll interval     : every {FRESHDESK_POLL_INTERVAL_MINUTES} minute(s)           │")
    log.info(f"│  Auto-resolve      : {'ON ' if FEATURE_AUTO_RESOLVE  else 'OFF'}                              │")
    log.info(f"│  KB search         : {'ON ' if FEATURE_KB_SEARCH     else 'OFF'}                              │")
    log.info(f"│  After-hours reply : {'ON ' if FEATURE_AFTER_HOURS_REPLY else 'OFF'}                          │")
    log.info(f"│  Sentiment check   : {'ON ' if FEATURE_SENTIMENT_ANALYSIS else 'OFF'}                         │")
    log.info(f"│  Dry run mode      : {'ON ' if DRY_RUN_MODE          else 'OFF'}                              │")
    log.info(f"│  KB chunks indexed : {kb_stats.get('total_chunks', 0):<10}                        │")
    log.info(f"│  Tickets processed : {db_stats.get('total', 0):<10} (all time)               │")
    log.info(f"│  Auto-resolve rate : {db_stats.get('auto_rate_pct', 0.0):<6.1f}% (all time)              │")
    log.info("└─────────────────────────────────────────────────┘")
    log.info("")


def _print_session_summary() -> None:
    """
    Print a session summary when the system shuts down.
    Shows how many tickets were processed, resolved,
    and escalated during this run.
    """
    uptime_mins = round(
        (datetime.utcnow() - START_TIME).total_seconds() / 60, 1
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
        rate = round(TICKETS_RESOLVED / TICKETS_PROCESSED * 100, 1)
        log.info(f"  Session auto-rate: {rate}%")

    log.info("=" * 60)


def _signal_handler(sig, frame) -> None:
    """
    Handle Ctrl+C and SIGTERM gracefully.
    Prints the session summary before exiting so you
    always know what was processed before shutdown.

    Args:
        sig   : Signal number
        frame : Current stack frame
    """
    log.info("")
    log.info("Shutdown signal received. Stopping scheduler...")
    _print_session_summary()
    log.info("AI Ticket Resolver stopped. Goodbye.")
    sys.exit(0)


def main() -> None:
    """
    Main entry point for the AI Ticket Resolver.

    Startup sequence:
        1. Setup logging
        2. Validate all settings and connections
        3. Initialize database
        4. Register shutdown signal handlers
        5. Run one immediate poll cycle
        6. Start the scheduler loop

    The system runs indefinitely until Ctrl+C or SIGTERM.
    """
    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    checks_passed = _startup_checks()

    if not checks_passed:
        log.error(
            "Startup checks failed. "
            "Fix the errors above and restart."
        )
        sys.exit(1)

    log.info(
        f"Running first poll immediately before "
        f"starting {FRESHDESK_POLL_INTERVAL_MINUTES}-minute scheduler..."
    )
    process_tickets()

    schedule.every(FRESHDESK_POLL_INTERVAL_MINUTES).minutes.do(
        process_tickets
    )

    log.info(
        f"Scheduler started — polling every "
        f"{FRESHDESK_POLL_INTERVAL_MINUTES} minute(s). "
        f"Press Ctrl+C to stop."
    )

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()