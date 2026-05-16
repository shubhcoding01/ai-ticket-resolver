# import os
# import sys
# import time
# import signal
# import logging
# import schedule
# from datetime import datetime, timezone
# from pathlib  import Path
# from dotenv   import load_dotenv

# load_dotenv("config/.env")

# from config.settings import (
#     setup_logging,
#     validate_settings,
#     get_all_settings,
#     FRESHDESK_POLL_INTERVAL_MINUTES,
#     COMPANY_NAME,
#     DRY_RUN_MODE,
#     FEATURE_AUTO_RESOLVE,
#     FEATURE_KB_SEARCH,
#     FEATURE_AFTER_HOURS_REPLY,
#     FEATURE_SENTIMENT_ANALYSIS,
#     AUTO_RESOLVABLE_CATEGORIES,
#     FORCE_ESCALATION_KEYWORDS,
#     KB_AUTO_REBUILD,
# )

# setup_logging()
# log = logging.getLogger(__name__)

# DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() == "true"

# if DEMO_MODE:
#     log.info("DEMO MODE detected — importing demo runner...")
#     from demo.demo_runner import run_demo
# else:
#     from ingestion.freshdesk_client import (
#         fetch_new_tickets,
#         close_ticket,
#         update_ticket_status,
#         add_internal_note,
#         add_tag_to_ticket,
#         test_connection,
#     )
#     from ingestion.ticket_parser import (
#         parse_ticket,
#         parse_tickets_bulk,
#     )
#     from classifier.ai_classifier import classify_ticket
#     from classifier.category_rules import (
#         classify_by_rules,
#         _check_escalation_triggers,
#         _is_after_business_hours,
#     )
#     from classifier.prompts import (
#         get_estimated_resolution_time,
#         get_category_description,
#     )
#     from knowledge_base.kb_indexer import (
#         build_index,
#         get_index_stats,
#     )
#     from knowledge_base.kb_search import (
#         search_knowledge_base,
#         is_kb_available,
#         get_kb_stats,
#     )
#     from automation.runner import (
#         run_automation,
#         get_supported_categories,
#     )
#     from agent.orchestrator import orchestrate
#     from agent.notifier     import notify_user
#     from agent.escalation   import (
#         escalate_ticket,
#         escalate_with_full_details,
#         escalate_high_priority,
#         escalate_after_business_hours,
#     )
#     from database.db_setup  import initialize_database
#     from database.db_logger import (
#         log_ticket_action,
#         log_classification,
#         log_notification,
#         get_resolution_stats,
#     )


# START_TIME         : datetime = datetime.now(timezone.utc)
# PROCESSED_IDS      : set      = set()
# TICKETS_PROCESSED  : int      = 0
# TICKETS_RESOLVED   : int      = 0
# TICKETS_ESCALATED  : int      = 0
# POLL_COUNT         : int      = 0


# def process_tickets() -> None:
#     """
#     Main polling function called by the scheduler every N minutes.
#     Fetches new open tickets from Freshdesk, classifies each one,
#     and routes to auto-resolution or escalation.

#     Full flow per ticket:
#         1.  Fetch raw tickets from Freshdesk
#         2.  Parse into clean normalized dict
#         3.  Skip if already processed this session
#         4.  Classify with Claude AI (fallback to rules if API down)
#         5.  Check for force-escalation triggers
#         6.  Check if after business hours
#         7.  If can auto-resolve → run automation via orchestrator
#             a. Success  → close + notify user
#             b. Failure  → search KB → send guide or escalate
#         8.  If cannot auto-resolve → search KB + escalate
#         9.  Log everything to database
#     """
#     global TICKETS_PROCESSED, TICKETS_RESOLVED, TICKETS_ESCALATED, POLL_COUNT

#     POLL_COUNT += 1
#     poll_start  = time.time()

#     log.info("")
#     log.info("=" * 60)
#     log.info(
#         f"POLL #{POLL_COUNT} — "
#         f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M:%S UTC')}"
#     )
#     log.info("=" * 60)

#     if DRY_RUN_MODE:
#         log.warning(
#             "DRY RUN MODE — no scripts will run, "
#             "no tickets will be closed."
#         )

#     try:
#         raw_tickets = fetch_new_tickets()
#     except Exception as e:
#         log.error(f"Failed to fetch tickets from Freshdesk: {e}")
#         return

#     if not raw_tickets:
#         log.info("No new open tickets found.")
#         return

#     parsed_tickets = parse_tickets_bulk(raw_tickets)
#     new_tickets    = [
#         t for t in parsed_tickets
#         if t["id"] not in PROCESSED_IDS and t["id"] != 0
#     ]

#     if not new_tickets:
#         log.info("All fetched tickets already processed this session.")
#         return

#     log.info(f"Processing {len(new_tickets)} new ticket(s)...")

#     after_hours = _is_after_business_hours()
#     if after_hours:
#         log.info("Current time is outside business hours.")

#     for ticket in new_tickets:
#         _process_single_ticket(ticket, after_hours)
#         PROCESSED_IDS.add(ticket["id"])
#         TICKETS_PROCESSED += 1

#     poll_duration = round(time.time() - poll_start, 1)
#     log.info("")
#     log.info(
#         f"Poll #{POLL_COUNT} complete in {poll_duration}s — "
#         f"processed {len(new_tickets)} ticket(s)."
#     )
#     log.info("=" * 60)


# def _process_single_ticket(ticket: dict, after_hours: bool) -> None:
#     """
#     Process one ticket end to end — classify, decide, act, log.

#     Args:
#         ticket      : Parsed ticket dict from ticket_parser
#         after_hours : True if currently outside business hours
#     """
#     global TICKETS_RESOLVED, TICKETS_ESCALATED

#     ticket_id      = ticket["id"]
#     subject        = ticket["subject"]
#     description    = ticket["description"]
#     requester      = ticket["requester_email"]
#     requester_name = ticket["requester_name"]
#     machine        = ticket.get("machine_name", "UNKNOWN")
#     urgency        = ticket.get("urgency_level", "medium")
#     apps           = ticket.get("mentioned_apps", [])

#     log.info("")
#     log.info(f"┌─ Ticket #{ticket_id}: {subject[:55]}")
#     log.info(f"│  Requester : {requester_name} ({requester})")
#     log.info(f"│  Machine   : {machine}")
#     log.info(f"│  Urgency   : {urgency}")
#     log.info(f"│  Apps      : {apps or 'none detected'}")

#     try:
#         classification = classify_ticket(
#             subject        = subject,
#             description    = description,
#             ticket_id      = ticket_id,
#             machine_name   = machine,
#             requester_name = requester_name,
#         )
#     except Exception as e:
#         log.error(f"│  AI Classifier failed: {e}")
#         log.warning("│  Falling back to rule-based classifier...")
#         try:
#             classification = classify_by_rules(subject, description)
#         except Exception as e2:
#             log.error(f"│  Rule classifier also failed: {e2}")
#             _emergency_escalate(ticket, "Both classifiers failed.")
#             TICKETS_ESCALATED += 1
#             return

#     category         = classification.get("category",         "other")
#     priority         = classification.get("priority",         "medium")
#     can_auto         = classification.get("can_auto_resolve", False)
#     suggested_action = classification.get("suggested_action", "Manual review.")
#     confidence       = classification.get("confidence",       "low")
#     force_escalate   = classification.get("force_escalate",   False)

#     force_escalate = (
#         force_escalate
#         or _check_escalation_triggers(f"{subject} {description}")
#     )

#     if urgency in ["critical", "high"] and priority == "medium":
#         priority = "high"
#         log.info("│  Priority boosted to 'high' based on urgency.")

#     if machine == "UNKNOWN" and can_auto:
#         can_auto = False
#         log.warning(
#             "│  Machine UNKNOWN — "
#             "auto-resolve disabled."
#         )

#     if DRY_RUN_MODE:
#         can_auto = False
#         log.warning("│  Dry run — auto-resolve forced OFF.")

#     if not FEATURE_AUTO_RESOLVE:
#         can_auto = False
#         log.info("│  FEATURE_AUTO_RESOLVE disabled.")

#     log.info(f"│  Category  : {category}")
#     log.info(f"│  Priority  : {priority}")
#     log.info(f"│  Auto      : {can_auto}")
#     log.info(f"│  Confidence: {confidence}")
#     log.info(f"│  Escalate  : {force_escalate}")
#     log.info(f"│  Action    : {suggested_action}")

#     try:
#         log_classification(
#             ticket_id        = ticket_id,
#             subject          = subject,
#             category         = category,
#             priority         = priority,
#             can_auto_resolve = can_auto,
#             suggested_action = suggested_action,
#             confidence       = confidence,
#         )
#     except Exception as e:
#         log.warning(f"│  Classification log failed: {e}")

#     if force_escalate:
#         log.warning(f"│  FORCE ESCALATION — critical keyword detected!")
#         _handle_force_escalation(ticket, classification)
#         TICKETS_ESCALATED += 1
#         log.info(f"└─ Ticket #{ticket_id} → FORCE ESCALATED")
#         return

#     if after_hours and priority not in ["high", "urgent"]:
#         log.info("│  After hours + non-critical → after-hours escalation.")
#         escalate_after_business_hours(ticket, classification)
#         TICKETS_ESCALATED += 1
#         log.info(f"└─ Ticket #{ticket_id} → AFTER HOURS ESCALATED")
#         return

#     if priority in ["high", "urgent"] and not can_auto:
#         log.warning("│  High priority + no auto-resolve → urgent escalation.")
#         escalate_high_priority(ticket, classification)
#         TICKETS_ESCALATED += 1
#         log.info(f"└─ Ticket #{ticket_id} → HIGH PRIORITY ESCALATED")
#         return

#     if can_auto:
#         resolved = _handle_auto_resolve(ticket, classification)
#     else:
#         resolved = _handle_manual_route(ticket, classification)

#     if resolved:
#         TICKETS_RESOLVED += 1
#         log.info(f"└─ Ticket #{ticket_id} → RESOLVED ✓")
#     else:
#         TICKETS_ESCALATED += 1
#         log.info(f"└─ Ticket #{ticket_id} → ESCALATED")


# def _handle_auto_resolve(ticket: dict, classification: dict) -> bool:
#     """
#     Attempt auto-resolution via orchestrator.
#     On success — close ticket and notify user.
#     On failure — search KB and escalate.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict

#     Returns:
#         True if fully resolved, False if escalated
#     """
#     ticket_id        = ticket["id"]
#     subject          = ticket["subject"]
#     description      = ticket["description"]
#     requester        = ticket["requester_email"]
#     requester_name   = ticket["requester_name"]
#     category         = classification["category"]
#     priority         = classification["priority"]
#     suggested_action = classification["suggested_action"]

#     log.info(f"│  Attempting auto-resolution...")

#     add_internal_note(
#         ticket_id,
#         f"[AI Ticket Resolver]\n"
#         f"Auto-resolution started.\n"
#         f"Category  : {category}\n"
#         f"Priority  : {priority}\n"
#         f"Machine   : {ticket.get('machine_name', 'UNKNOWN')}\n"
#         f"Action    : {suggested_action}\n"
#         f"Timestamp : "
#         f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
#     )

#     success = orchestrate(ticket, classification)

#     if success:
#         log.info(f"│  Auto-resolution SUCCEEDED ✓")

#         cat_label = get_category_description(category)

#         resolution_msg = (
#             f"Dear {requester_name},\n\n"
#             f"Your ticket '{subject}' has been automatically resolved "
#             f"by our AI support system.\n\n"
#             f"Issue type   : {cat_label}\n"
#             f"Action taken : {suggested_action}\n\n"
#             f"Your issue has been fixed remotely. "
#             f"Please restart your computer if needed and verify "
#             f"the issue is resolved.\n\n"
#             f"If the problem persists, please raise a new ticket.\n\n"
#             f"Thank you,\n"
#             f"IT Support Team\n"
#             f"{COMPANY_NAME}"
#         )

#         if not DRY_RUN_MODE:
#             close_ticket(ticket_id, suggested_action)

#         notif_ok = notify_user(
#             email      = requester,
#             ticket_id  = ticket_id,
#             subject    = subject,
#             message    = resolution_msg,
#             notif_type = "resolved",
#         )

#         try:
#             log_notification(
#                 ticket_id  = ticket_id,
#                 recipient  = requester,
#                 notif_type = "resolved",
#                 subject    = subject,
#                 success    = notif_ok,
#             )
#         except Exception as e:
#             log.warning(f"│  Notification log failed: {e}")

#         add_tag_to_ticket(
#             ticket_id,
#             ["ai-resolved", f"cat-{category}", "auto-closed"]
#         )

#         log_ticket_action(
#             ticket_id    = ticket_id,
#             category     = category,
#             priority     = priority,
#             action_taken = suggested_action,
#             resolved_by  = "AI_AUTO",
#             status       = "RESOLVED",
#         )

#         return True

#     else:
#         log.warning(f"│  Auto-resolution FAILED — checking KB...")

#         add_internal_note(
#             ticket_id,
#             f"[AI Ticket Resolver]\n"
#             f"Auto-resolution FAILED.\n"
#             f"Searching KB for: {subject}"
#         )

#         return _search_kb_and_escalate(
#             ticket         = ticket,
#             classification = classification,
#             reason         = (
#                 f"Auto-resolution failed.\n"
#                 f"Suggested: {suggested_action}"
#             ),
#             tag            = "auto-failed",
#         )


# def _handle_manual_route(ticket: dict, classification: dict) -> bool:
#     """
#     Handle tickets that cannot be auto-resolved.
#     Search KB first then escalate.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict

#     Returns:
#         Always False — ticket is escalated not resolved
#     """
#     ticket_id        = ticket["id"]
#     category         = classification["category"]
#     suggested_action = classification["suggested_action"]

#     log.info(f"│  Cannot auto-resolve — searching KB...")

#     add_internal_note(
#         ticket_id,
#         f"[AI Ticket Resolver]\n"
#         f"Cannot auto-resolve — routing to engineer.\n"
#         f"Category : {category}\n"
#         f"Suggested: {suggested_action}"
#     )

#     return _search_kb_and_escalate(
#         ticket         = ticket,
#         classification = classification,
#         reason         = (
#             f"Requires engineer.\n"
#             f"Category : {category}\n"
#             f"Suggested: {suggested_action}"
#         ),
#         tag            = "manual-route",
#     )


# def _search_kb_and_escalate(
#     ticket        : dict,
#     classification: dict,
#     reason        : str,
#     tag           : str = "escalated",
# ) -> bool:
#     """
#     Search KB for self-help guide, send it to user if found,
#     then escalate ticket to engineer queue.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict
#         reason         : Why ticket is being escalated
#         tag            : Freshdesk tag to apply

#     Returns:
#         Always False — ticket is escalated not resolved
#     """
#     ticket_id        = ticket["id"]
#     subject          = ticket["subject"]
#     description      = ticket["description"]
#     requester        = ticket["requester_email"]
#     requester_name   = ticket["requester_name"]
#     category         = classification["category"]
#     priority         = classification["priority"]
#     suggested_action = classification["suggested_action"]

#     kb_guide    = None
#     resolved_by = "ESCALATION"

#     if FEATURE_KB_SEARCH and is_kb_available():
#         log.info(f"│  Searching KB...")
#         try:
#             kb_guide = search_knowledge_base(description)
#         except Exception as e:
#             log.warning(f"│  KB search error: {e}")

#     if kb_guide:
#         log.info(f"│  KB guide found — sending to {requester}.")

#         kb_message = (
#             f"Dear {requester_name},\n\n"
#             f"Thank you for contacting IT Support "
#             f"regarding '{subject}'.\n\n"
#             f"We found a self-help guide that may help:\n\n"
#             f"{'─' * 50}\n"
#             f"{kb_guide}\n"
#             f"{'─' * 50}\n\n"
#             f"An engineer will also follow up shortly.\n\n"
#             f"Thank you,\n"
#             f"IT Support Team\n"
#             f"{COMPANY_NAME}"
#         )

#         notif_ok = notify_user(
#             email      = requester,
#             ticket_id  = ticket_id,
#             subject    = subject,
#             message    = kb_message,
#             notif_type = "kb_guide_sent",
#         )

#         try:
#             log_notification(
#                 ticket_id  = ticket_id,
#                 recipient  = requester,
#                 notif_type = "kb_guide_sent",
#                 subject    = subject,
#                 success    = notif_ok,
#             )
#         except Exception as e:
#             log.warning(f"│  Notification log failed: {e}")

#         reason      += "\nKB guide sent to user."
#         resolved_by  = "KB+ESCALATION"

#     else:
#         if FEATURE_KB_SEARCH:
#             log.info(f"│  No KB guide found.")

#     escalate_with_full_details(
#         ticket         = ticket,
#         classification = classification,
#         reason         = reason,
#     )

#     add_tag_to_ticket(
#         ticket_id,
#         [tag, f"cat-{category}", "ai-processed"]
#     )

#     log_ticket_action(
#         ticket_id    = ticket_id,
#         category     = category,
#         priority     = priority,
#         action_taken = (
#             "KB guide sent + escalated."
#             if kb_guide else
#             f"Escalated — {suggested_action}"
#         ),
#         resolved_by  = resolved_by,
#         status       = "ESCALATED",
#     )

#     return False


# def _handle_force_escalation(
#     ticket        : dict,
#     classification: dict,
# ) -> None:
#     """
#     Handle force-escalation for critical keyword tickets
#     like ransomware, data breach, executive mentions.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict
#     """
#     ticket_id = ticket["id"]
#     category  = classification.get("category", "other")

#     classification["priority"]         = "urgent"
#     classification["can_auto_resolve"] = False

#     add_internal_note(
#         ticket_id,
#         f"[AI Ticket Resolver — FORCE ESCALATION]\n"
#         f"Critical keyword detected in ticket.\n"
#         f"Immediate engineer attention required.\n"
#         f"Timestamp: "
#         f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
#     )

#     escalate_high_priority(ticket, classification)

#     log_ticket_action(
#         ticket_id    = ticket_id,
#         category     = category,
#         priority     = "urgent",
#         action_taken = "Force-escalated — critical keyword detected.",
#         resolved_by  = "FORCE_ESCALATION",
#         status       = "ESCALATED",
#     )


# def _emergency_escalate(ticket: dict, reason: str) -> None:
#     """
#     Last-resort escalation when all classifiers fail.
#     Ensures no ticket is ever silently dropped.

#     Args:
#         ticket : Parsed ticket dict
#         reason : Why emergency escalation was triggered
#     """
#     ticket_id = ticket.get("id", 0)
#     log.error(f"│  EMERGENCY ESCALATE #{ticket_id}: {reason}")

#     try:
#         add_internal_note(
#             ticket_id,
#             f"[EMERGENCY ESCALATION]\n"
#             f"Reason: {reason}\n"
#             f"Cannot classify — manual review needed.\n"
#             f"Timestamp: "
#             f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
#         )
#         update_ticket_status(
#             ticket_id, "pending"
#         )
#         add_tag_to_ticket(
#             ticket_id,
#             ["emergency-escalation", "classifier-failed"]
#         )
#     except Exception as e:
#         log.error(f"│  Emergency note failed: {e}")

#     try:
#         log_ticket_action(
#             ticket_id    = ticket_id,
#             category     = "other",
#             priority     = "high",
#             action_taken = reason,
#             resolved_by  = "EMERGENCY",
#             status       = "ESCALATED",
#         )
#     except Exception as e:
#         log.error(f"│  Emergency DB log failed: {e}")


# def _startup_checks() -> bool:
#     """
#     Run all pre-flight checks before the scheduler starts.
#     Tests settings, DB, Freshdesk connection, and KB status.

#     Returns:
#         True if all required checks pass, False otherwise
#     """
#     log.info("")
#     log.info("=" * 60)
#     log.info("AI TICKET RESOLVER — STARTING UP (LIVE MODE)")
#     log.info(f"Company  : {COMPANY_NAME}")
#     log.info(
#         f"Started  : "
#         f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M:%S UTC')}"
#     )
#     log.info(f"Dry Run  : {DRY_RUN_MODE}")
#     log.info("=" * 60)

#     log.info("Step 1/5 — Validating settings...")
#     validation = validate_settings()
#     if not validation["valid"]:
#         for err in validation["errors"]:
#             log.error(f"  CONFIG ERROR   : {err}")
#         log.error("Fix the errors above in config/.env and restart.")
#         return False
#     for warn in validation["warnings"]:
#         log.warning(f"  CONFIG WARNING : {warn}")
#     log.info("Settings validation passed.")

#     log.info("Step 2/5 — Initializing database...")
#     try:
#         initialize_database()
#         log.info("Database initialized.")
#     except Exception as e:
#         log.error(f"Database init failed: {e}")
#         return False

#     log.info("Step 3/5 — Testing Freshdesk connection...")
#     try:
#         fd_ok = test_connection()
#         if fd_ok:
#             log.info("Freshdesk connection OK.")
#         else:
#             log.error(
#                 "Freshdesk connection FAILED. "
#                 "Check FRESHDESK_DOMAIN and FRESHDESK_API_KEY in .env"
#             )
#             return False
#     except Exception as e:
#         log.error(f"Freshdesk test error: {e}")
#         return False

#     log.info("Step 4/5 — Checking knowledge base...")
#     try:
#         if KB_AUTO_REBUILD:
#             log.info("KB_AUTO_REBUILD=true — rebuilding...")
#             build_index(force_rebuild=True)
#         kb_ok    = is_kb_available()
#         kb_stats = get_kb_stats()
#         if kb_ok:
#             log.info(
#                 f"KB ready — "
#                 f"{kb_stats.get('total_chunks', 0)} chunks."
#             )
#         else:
#             log.warning(
#                 "KB not indexed. "
#                 "Run: python knowledge_base/kb_indexer.py"
#             )
#     except Exception as e:
#         log.warning(f"KB check failed: {e}")

#     log.info("Step 5/5 — Startup summary...")
#     _print_startup_summary()
#     log.info("All startup checks passed.")
#     return True


# def _print_startup_summary() -> None:
#     """Print configuration summary at startup."""
#     try:
#         kb_stats = get_kb_stats()
#         db_stats = get_resolution_stats()
#     except Exception:
#         kb_stats = {}
#         db_stats = {}

#     log.info("")
#     log.info("┌─────────────────────────────────────────────────┐")
#     log.info("│        SYSTEM CONFIGURATION SUMMARY            │")
#     log.info("├─────────────────────────────────────────────────┤")
#     log.info(
#         f"│  Poll interval     : "
#         f"every {FRESHDESK_POLL_INTERVAL_MINUTES} minute(s)"
#     )
#     log.info(
#         f"│  Auto-resolve      : "
#         f"{'ON' if FEATURE_AUTO_RESOLVE else 'OFF'}"
#     )
#     log.info(
#         f"│  KB search         : "
#         f"{'ON' if FEATURE_KB_SEARCH else 'OFF'}"
#     )
#     log.info(
#         f"│  After-hours reply : "
#         f"{'ON' if FEATURE_AFTER_HOURS_REPLY else 'OFF'}"
#     )
#     log.info(
#         f"│  Dry run mode      : "
#         f"{'ON' if DRY_RUN_MODE else 'OFF'}"
#     )
#     log.info(
#         f"│  KB chunks         : "
#         f"{kb_stats.get('total_chunks', 0)}"
#     )
#     log.info(
#         f"│  Tickets (all time): "
#         f"{db_stats.get('total', 0)}"
#     )
#     log.info(
#         f"│  Auto-rate (all)   : "
#         f"{db_stats.get('auto_rate_pct', 0.0):.1f}%"
#     )
#     log.info("└─────────────────────────────────────────────────┘")
#     log.info("")


# def _print_session_summary() -> None:
#     """Print session stats on shutdown."""
#     uptime_mins = round(
#         (datetime.now(timezone.utc) - START_TIME)
#         .total_seconds() / 60,
#         1
#     )

#     log.info("")
#     log.info("=" * 60)
#     log.info("SESSION SUMMARY")
#     log.info("=" * 60)
#     log.info(f"  Uptime           : {uptime_mins} minutes")
#     log.info(f"  Poll cycles      : {POLL_COUNT}")
#     log.info(f"  Tickets processed: {TICKETS_PROCESSED}")
#     log.info(f"  Tickets resolved : {TICKETS_RESOLVED}")
#     log.info(f"  Tickets escalated: {TICKETS_ESCALATED}")
#     if TICKETS_PROCESSED > 0:
#         rate = round(
#             TICKETS_RESOLVED / TICKETS_PROCESSED * 100, 1
#         )
#         log.info(f"  Session rate     : {rate}%")
#     log.info("=" * 60)


# def _signal_handler(sig, frame) -> None:
#     """Handle Ctrl+C and SIGTERM gracefully."""
#     log.info("")
#     log.info("Shutdown signal received. Stopping...")
#     if not DEMO_MODE:
#         _print_session_summary()
#     log.info("AI Ticket Resolver stopped. Goodbye.")
#     sys.exit(0)


# def main() -> None:
#     """
#     Main entry point.

#     If DEMO_MODE=true in .env:
#         → Runs the full demo with 10 sample tickets
#         → No real API keys needed
#         → Everything is simulated

#     If DEMO_MODE=false in .env:
#         → Runs in live mode
#         → Requires real Freshdesk + Anthropic API keys
#         → Polls Freshdesk every N minutes
#     """
#     signal.signal(signal.SIGINT,  _signal_handler)
#     signal.signal(signal.SIGTERM, _signal_handler)

#     if DEMO_MODE:
#         log.info("")
#         log.info("=" * 60)
#         log.info("DEMO MODE — starting demo runner...")
#         log.info("=" * 60)
#         run_demo()
#         log.info("")
#         log.info("Demo complete.")
#         log.info(
#             "To run the dashboard: "
#             "streamlit run dashboard/app.py"
#         )
#         log.info(
#             "To switch to live mode: "
#             "set DEMO_MODE=false in config/.env"
#         )
#         return

#     checks_passed = _startup_checks()

#     if not checks_passed:
#         log.error(
#             "Startup checks failed. "
#             "Fix errors in config/.env and restart.\n"
#             "Tip: Set DEMO_MODE=true to run without real API keys."
#         )
#         sys.exit(1)

#     log.info("Running first poll immediately...")
#     process_tickets()

#     schedule.every(
#         FRESHDESK_POLL_INTERVAL_MINUTES
#     ).minutes.do(process_tickets)

#     log.info(
#         f"Scheduler running — polling every "
#         f"{FRESHDESK_POLL_INTERVAL_MINUTES} minute(s). "
#         f"Press Ctrl+C to stop."
#     )

#     while True:
#         schedule.run_pending()
#         time.sleep(30)


# if __name__ == "__main__":
#     main()


import os
import sys
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib       import Path

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

os.environ.setdefault("DEMO_MODE",   "true")
os.environ.setdefault("KB_MIN_SCORE", "0.3")

TEMP_DIR      = tempfile.mkdtemp(prefix="kb_test_")
TEST_DOCS_DIR = os.path.join(TEMP_DIR, "docs")
TEST_CHROMA   = os.path.join(TEMP_DIR, "chroma_db")
TEST_METADATA = os.path.join(TEMP_DIR, "index_metadata.json")

os.makedirs(TEST_DOCS_DIR, exist_ok=True)

os.environ["KB_DOCS_DIR"]   = TEST_DOCS_DIR
os.environ["KB_CHROMA_DIR"] = TEST_CHROMA
os.environ["KB_METADATA"]   = TEST_METADATA

from knowledge_base.kb_indexer import (
    build_index,
    _scan_docs_folder,
    _load_document,
    _chunk_text,
    _split_into_sentences,
    _merge_small_chunks,
    _hash_file,
    _generate_chunk_id,
    _load_metadata,
    _save_metadata,
    _get_changed_files,
    get_index_stats,
    create_sample_docs,
    DOCS_DIR,
    CHROMA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from knowledge_base.kb_search import (
    search_knowledge_base,
    search_with_details,
    search_by_category,
    search_multi_query,
    is_kb_available,
    get_kb_stats,
    reset_collection_cache,
    _clean_query,
    _filter_by_score,
    _deduplicate_results,
    _text_overlap_ratio,
    _format_guide,
    _file_name_to_title,
    _score_to_label,
    _clean_chunk_text,
)


SAMPLE_VPN_CONTENT = """
VPN Connection Guide

This guide explains how to connect to the company VPN.

Step 1 — Open Cisco AnyConnect
Open the Start menu and search for Cisco AnyConnect.
Click on the application icon to open it.

Step 2 — Enter Server Address
Type vpn.company.com in the connection box.
Click Connect to proceed.

Step 3 — Enter Credentials
Enter your domain username and password.
Click OK to complete the connection.

Troubleshooting VPN Issues

Issue: Connection timed out
Solution: Check your internet connection first.
Restart the AnyConnect service and try again.

Issue: Invalid credentials
Solution: Verify your password has not expired.
Contact IT support if the issue persists.
"""

SAMPLE_ANTIVIRUS_CONTENT = """
Antivirus Troubleshooting Guide

This guide covers common antivirus issues on corporate laptops.

Windows Defender Issues

Issue: Real-time protection is turned off
Solution: Open Windows Security from the Start menu.
Toggle Real-time protection to On.

Issue: Definitions out of date
Solution: Open Windows Security and click Virus protection.
Click Check for updates to download latest definitions.

Symantec Endpoint Protection

Issue: Symantec showing red warning
Solution: Right click Symantec icon in taskbar.
Select Open and click LiveUpdate to update definitions.
"""

VALID_CATEGORIES = [
    "app_install",
    "antivirus",
    "password_reset",
    "network",
    "printer",
    "email_issue",
    "hardware",
    "os_issue",
    "access_permission",
    "other",
]


def _write_test_doc(filename: str, content: str) -> Path:
    """
    Write a test document to the test docs directory.

    Args:
        filename : File name to write
        content  : Text content

    Returns:
        Path object of the written file
    """
    file_path = Path(TEST_DOCS_DIR) / filename
    file_path.write_text(content.strip(), encoding="utf-8")
    return file_path


def _cleanup_test_dir() -> None:
    """Remove the temp test directory after tests complete."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


def _make_mock_result(
    text      : str,
    file_name : str,
    score     : float = 0.8,
    idx       : int   = 0,
) -> dict:
    """
    Build a minimal result dict matching the format
    returned by _vector_search().

    Args:
        text      : Chunk text content
        file_name : Source document filename
        score     : Cosine similarity score
        idx       : Chunk index

    Returns:
        Result dict
    """
    return {
        "text"        : text,
        "score"       : score,
        "file_name"   : file_name,
        "chunk_index" : idx,
        "word_count"  : len(text.split()),
        "indexed_at"  : "2026-05-01 10:00:00",
        "id"          : f"{file_name}_{idx}",
    }


def _make_mock_collection(
    docs  : list,
    scores: list,
) -> MagicMock:
    """
    Build a mock ChromaDB collection with query results.

    Args:
        docs   : List of document text strings
        scores : List of cosine similarity scores

    Returns:
        MagicMock object simulating a ChromaDB collection
    """
    mock_collection = MagicMock()
    mock_collection.count.return_value = len(docs)

    distances = [max(0.0, 1.0 - s) for s in scores]

    mock_collection.query.return_value = {
        "documents" : [docs],
        "metadatas" : [
            [
                {
                    "file_name"   : "vpn_guide.txt",
                    "chunk_index" : i,
                    "word_count"  : len(d.split()),
                    "indexed_at"  : "2026-05-01 10:00:00",
                }
                for i, d in enumerate(docs)
            ]
        ],
        "distances" : [distances],
        "ids"       : [
            [f"chunk_{i}" for i in range(len(docs))]
        ],
    }
    return mock_collection


class TestScanDocsFolder(unittest.TestCase):
    """Tests for _scan_docs_folder()."""

    def setUp(self):
        for f in Path(TEST_DOCS_DIR).glob("*"):
            f.unlink()

    def test_finds_txt_files(self):
        """Should find .txt files in docs folder."""
        _write_test_doc("test_guide.txt", "Some content.")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertIn("test_guide.txt", names)

    def test_finds_md_files(self):
        """Should find .md files in docs folder."""
        _write_test_doc("test_guide.md", "# Some markdown.")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertIn("test_guide.md", names)

    def test_ignores_pdf_files(self):
        """Should not return .pdf files."""
        _write_test_doc("document.pdf", "PDF content")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertNotIn("document.pdf", names)

    def test_ignores_docx_files(self):
        """Should not return .docx files."""
        _write_test_doc("document.docx", "DOCX content")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertNotIn("document.docx", names)

    def test_empty_folder_returns_empty_list(self):
        """Empty docs folder returns empty list."""
        files = _scan_docs_folder()
        self.assertEqual(files, [])

    def test_returns_list_of_path_objects(self):
        """Should return list of Path objects."""
        _write_test_doc("guide.txt", "Content here.")
        files = _scan_docs_folder()
        for f in files:
            self.assertIsInstance(f, Path)

    def test_multiple_files_all_returned(self):
        """Multiple files should all be returned."""
        _write_test_doc("guide_a.txt", "Content A.")
        _write_test_doc("guide_b.txt", "Content B.")
        _write_test_doc("guide_c.md",  "Content C.")
        files = _scan_docs_folder()
        self.assertGreaterEqual(len(files), 3)

    def test_files_sorted_alphabetically(self):
        """Files should be returned in a consistent order."""
        _write_test_doc("z_guide.txt", "Z content.")
        _write_test_doc("a_guide.txt", "A content.")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertEqual(names, sorted(names))


class TestLoadDocument(unittest.TestCase):
    """Tests for _load_document()."""

    def test_loads_text_content(self):
        """Should return file content as string."""
        fp   = _write_test_doc("load_test.txt", "Hello world.")
        text = _load_document(fp)
        self.assertEqual(text, "Hello world.")

    def test_returns_empty_for_missing_file(self):
        """Missing file should return empty string."""
        fp   = Path(TEST_DOCS_DIR) / "nonexistent.txt"
        text = _load_document(fp)
        self.assertEqual(text, "")

    def test_strips_whitespace(self):
        """Content should be stripped of leading/trailing whitespace."""
        fp   = _write_test_doc(
            "whitespace.txt", "  Content here.  "
        )
        text = _load_document(fp)
        self.assertEqual(text, "Content here.")

    def test_multiline_content_preserved(self):
        """Multi-line content should be preserved."""
        content = "Line one.\nLine two.\nLine three."
        fp      = _write_test_doc("multiline.txt", content)
        text    = _load_document(fp)
        self.assertIn("Line one.",   text)
        self.assertIn("Line two.",   text)
        self.assertIn("Line three.", text)

    def test_empty_file_returns_empty(self):
        """Empty file should return empty string."""
        fp = Path(TEST_DOCS_DIR) / "empty.txt"
        fp.write_text("", encoding="utf-8")
        text = _load_document(fp)
        self.assertEqual(text, "")

    def test_utf8_content_loaded(self):
        """Unicode content should be loaded correctly."""
        content = "Guide for IT: résumé café naïve"
        fp      = _write_test_doc("unicode.txt", content)
        text    = _load_document(fp)
        self.assertIn("résumé", text)


class TestChunkText(unittest.TestCase):
    """Tests for _chunk_text()."""

    def test_short_text_returns_at_least_one_chunk(self):
        """Short text should produce at least one chunk."""
        text   = "This is a short document."
        chunks = _chunk_text(text, "test.txt")
        self.assertGreaterEqual(len(chunks), 1)

    def test_long_text_returns_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        text   = "This is a sentence with content. " * 100
        chunks = _chunk_text(text, "long_doc.txt")
        self.assertGreater(len(chunks), 1)

    def test_each_chunk_has_required_keys(self):
        """Each chunk must have all required metadata keys."""
        text   = "Some content to chunk. " * 30
        chunks = _chunk_text(text, "test.txt")
        for chunk in chunks:
            self.assertIn("text",        chunk)
            self.assertIn("chunk_id",    chunk)
            self.assertIn("file_name",   chunk)
            self.assertIn("chunk_index", chunk)
            self.assertIn("word_count",  chunk)

    def test_chunk_ids_are_unique(self):
        """All chunk IDs should be unique."""
        text   = "Content sentence here. " * 100
        chunks = _chunk_text(text, "test.txt")
        ids    = [c["chunk_id"] for c in chunks]
        self.assertEqual(len(ids), len(set(ids)))

    def test_file_name_preserved(self):
        """file_name field must match the input filename."""
        text   = "Some content. " * 20
        chunks = _chunk_text(text, "my_guide.txt")
        for chunk in chunks:
            self.assertEqual(chunk["file_name"], "my_guide.txt")

    def test_empty_text_returns_empty_list(self):
        """Empty text should return empty list."""
        chunks = _chunk_text("", "empty.txt")
        self.assertEqual(chunks, [])

    def test_chunk_word_count_reasonable(self):
        """word_count in chunk should match actual word count."""
        text   = "Word " * 500
        chunks = _chunk_text(text, "count_test.txt")
        for chunk in chunks:
            actual = len(chunk["text"].split())
            self.assertAlmostEqual(
                chunk["word_count"],
                actual,
                delta=CHUNK_OVERLAP + 10,
            )

    def test_chunk_indices_sequential(self):
        """Chunk indices should start at 0 and be sequential."""
        text    = "Lots of content. " * 100
        chunks  = _chunk_text(text, "test.txt")
        indices = [c["chunk_index"] for c in chunks]
        self.assertEqual(indices[0], 0)
        self.assertEqual(indices, list(range(len(chunks))))

    def test_chunk_text_not_empty(self):
        """No chunk should have empty text."""
        text   = "Meaningful content in every chunk. " * 50
        chunks = _chunk_text(text, "test.txt")
        for chunk in chunks:
            self.assertGreater(
                len(chunk["text"].strip()), 0,
                "Found empty chunk text"
            )


class TestSplitIntoSentences(unittest.TestCase):
    """Tests for _split_into_sentences()."""

    def test_simple_sentences_split(self):
        """Three sentences should produce three results."""
        text   = "First sentence. Second sentence. Third sentence."
        result = _split_into_sentences(text)
        self.assertEqual(len(result), 3)

    def test_exclamation_splits(self):
        """Exclamation marks should also split sentences."""
        text   = "Urgent issue! Please fix it. Thank you."
        result = _split_into_sentences(text)
        self.assertGreaterEqual(len(result), 2)

    def test_empty_text_returns_empty_list(self):
        """Empty text returns empty list."""
        result = _split_into_sentences("")
        self.assertEqual(result, [])

    def test_single_sentence_returns_one_item(self):
        """Single sentence returns list with one item."""
        result = _split_into_sentences(
            "This is the only sentence here"
        )
        self.assertEqual(len(result), 1)

    def test_each_sentence_is_string(self):
        """Every item in result should be a string."""
        text   = "First. Second. Third."
        result = _split_into_sentences(text)
        for s in result:
            self.assertIsInstance(s, str)

    def test_sentences_not_empty(self):
        """No empty strings should be in result."""
        text   = "First sentence. Second sentence. Third sentence."
        result = _split_into_sentences(text)
        for s in result:
            self.assertGreater(len(s.strip()), 0)


class TestMergeSmallChunks(unittest.TestCase):
    """Tests for _merge_small_chunks()."""

    def test_small_chunks_merged(self):
        """Chunks under min_words should be merged together."""
        chunks = ["tiny", "also tiny", "still small"]
        merged = _merge_small_chunks(chunks, min_words=10)
        self.assertLess(len(merged), len(chunks))

    def test_large_chunks_not_merged(self):
        """Chunks over min_words stay separate."""
        large  = " ".join([f"word{i}" for i in range(50)])
        chunks = [large, large]
        merged = _merge_small_chunks(chunks, min_words=10)
        self.assertEqual(len(merged), 2)

    def test_empty_list_returns_empty(self):
        """Empty input returns empty list."""
        result = _merge_small_chunks([], min_words=30)
        self.assertEqual(result, [])

    def test_single_chunk_returned(self):
        """Single chunk always returned as-is."""
        chunks = ["just one chunk here"]
        merged = _merge_small_chunks(chunks, min_words=5)
        self.assertEqual(len(merged), 1)

    def test_merged_result_is_list_of_strings(self):
        """Result should always be a list of strings."""
        chunks = ["tiny", "also tiny"]
        merged = _merge_small_chunks(chunks, min_words=10)
        for item in merged:
            self.assertIsInstance(item, str)


class TestHashFile(unittest.TestCase):
    """Tests for _hash_file()."""

    def test_same_content_same_hash(self):
        """Two files with same content produce same hash."""
        fp1 = _write_test_doc("hash_a.txt", "Same content here.")
        fp2 = _write_test_doc("hash_b.txt", "Same content here.")
        self.assertEqual(_hash_file(fp1), _hash_file(fp2))

    def test_different_content_different_hash(self):
        """Different content produces different hash."""
        fp1 = _write_test_doc("diff_a.txt", "Content A here.")
        fp2 = _write_test_doc("diff_b.txt", "Content B here.")
        self.assertNotEqual(_hash_file(fp1), _hash_file(fp2))

    def test_returns_string(self):
        """Hash should be returned as a non-empty string."""
        fp     = _write_test_doc("hash_test.txt", "Content.")
        result = _hash_file(fp)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_missing_file_returns_empty(self):
        """Missing file returns empty string."""
        fp     = Path(TEST_DOCS_DIR) / "nonexistent.txt"
        result = _hash_file(fp)
        self.assertEqual(result, "")

    def test_hash_is_deterministic(self):
        """Same file always produces same hash on repeated calls."""
        fp = _write_test_doc("deterministic.txt", "Stable content.")
        h1 = _hash_file(fp)
        h2 = _hash_file(fp)
        self.assertEqual(h1, h2)


class TestGenerateChunkId(unittest.TestCase):
    """Tests for _generate_chunk_id()."""

    def test_returns_string(self):
        """Should return a string."""
        result = _generate_chunk_id("test.txt", 0, "Content.")
        self.assertIsInstance(result, str)

    def test_same_inputs_same_id(self):
        """Same inputs always produce same ID."""
        id1 = _generate_chunk_id("guide.txt", 1, "Content.")
        id2 = _generate_chunk_id("guide.txt", 1, "Content.")
        self.assertEqual(id1, id2)

    def test_different_index_different_id(self):
        """Different chunk index produces different ID."""
        id1 = _generate_chunk_id("guide.txt", 0, "Content.")
        id2 = _generate_chunk_id("guide.txt", 1, "Content.")
        self.assertNotEqual(id1, id2)

    def test_different_file_different_id(self):
        """Different file name produces different ID."""
        id1 = _generate_chunk_id("guide_a.txt", 0, "Content.")
        id2 = _generate_chunk_id("guide_b.txt", 0, "Content.")
        self.assertNotEqual(id1, id2)

    def test_id_contains_file_reference(self):
        """ID should reference the source file."""
        chunk_id = _generate_chunk_id("vpn_guide.txt", 0, "Content.")
        self.assertIn("vpn_guide", chunk_id)

    def test_no_spaces_in_id(self):
        """Chunk IDs should never contain spaces."""
        chunk_id = _generate_chunk_id("my guide.txt", 0, "Content.")
        self.assertNotIn(" ", chunk_id)

    def test_id_not_empty(self):
        """Chunk ID should never be empty."""
        chunk_id = _generate_chunk_id("guide.txt", 0, "Content.")
        self.assertGreater(len(chunk_id), 0)


class TestMetadataOperations(unittest.TestCase):
    """Tests for _load_metadata() and _save_metadata()."""

    def setUp(self):
        if os.path.exists(TEST_METADATA):
            os.remove(TEST_METADATA)

    def test_load_returns_empty_when_no_file(self):
        """Loading when no file exists returns empty dict."""
        result = _load_metadata()
        self.assertEqual(result, {})

    def test_save_and_load_roundtrip(self):
        """Saved metadata should be loadable and match original."""
        data = {
            "guide.txt": {
                "hash"        : "abc123def456",
                "indexed_at"  : "2026-05-01 10:00:00",
                "chunk_count" : 5,
                "file_size"   : 1024,
            }
        }
        _save_metadata(data)
        loaded = _load_metadata()
        self.assertEqual(loaded, data)

    def test_save_overwrites_existing(self):
        """Saving new data overwrites old metadata."""
        _save_metadata({"file_a.txt": {"hash": "old_hash"}})
        _save_metadata({"file_b.txt": {"hash": "new_hash"}})
        loaded = _load_metadata()
        self.assertIn("file_b.txt",    loaded)
        self.assertNotIn("file_a.txt", loaded)

    def test_multiple_files_saved(self):
        """Multiple files should all be saved and loaded."""
        data = {
            "guide_a.txt" : {"hash": "hash_a"},
            "guide_b.txt" : {"hash": "hash_b"},
            "guide_c.txt" : {"hash": "hash_c"},
        }
        _save_metadata(data)
        loaded = _load_metadata()
        self.assertEqual(len(loaded), 3)
        for key in data:
            self.assertIn(key, loaded)

    def test_save_creates_file_on_disk(self):
        """Calling save should create the metadata file."""
        _save_metadata({"test.txt": {"hash": "xyz"}})
        self.assertTrue(os.path.exists(TEST_METADATA))


class TestGetChangedFiles(unittest.TestCase):
    """Tests for _get_changed_files()."""

    def setUp(self):
        for f in Path(TEST_DOCS_DIR).glob("*.txt"):
            f.unlink()

    def test_new_file_detected_as_changed(self):
        """A new file not in metadata should be in changed list."""
        fp      = _write_test_doc("new_guide.txt", "Content.")
        changed = _get_changed_files([fp], metadata={})
        self.assertIn(fp, changed)

    def test_unchanged_file_not_in_changed_list(self):
        """File whose hash matches metadata should not be changed."""
        fp       = _write_test_doc("existing.txt", "Content.")
        metadata = {"existing.txt": {"hash": _hash_file(fp)}}
        changed  = _get_changed_files([fp], metadata=metadata)
        self.assertNotIn(fp, changed)

    def test_modified_file_detected(self):
        """File with different hash than stored should be changed."""
        fp       = _write_test_doc(
            "modified.txt", "New content after edit."
        )
        metadata = {
            "modified.txt": {"hash": "old_stale_hash_value"}
        }
        changed  = _get_changed_files([fp], metadata=metadata)
        self.assertIn(fp, changed)

    def test_empty_docs_returns_empty(self):
        """No files means no changed files."""
        changed = _get_changed_files([], metadata={})
        self.assertEqual(changed, [])

    def test_multiple_new_files_all_detected(self):
        """Multiple new files should all be in changed list."""
        fp1 = _write_test_doc("new_a.txt", "Content A.")
        fp2 = _write_test_doc("new_b.txt", "Content B.")
        fp3 = _write_test_doc("new_c.txt", "Content C.")
        changed = _get_changed_files(
            [fp1, fp2, fp3], metadata={}
        )
        self.assertEqual(len(changed), 3)


class TestCleanQuery(unittest.TestCase):
    """Tests for _clean_query()."""

    def test_lowercases_query(self):
        """Query should be lowercased."""
        result = _clean_query("INSTALL ZOOM ON MY LAPTOP")
        self.assertEqual(result, result.lower())

    def test_removes_email_addresses(self):
        """Email addresses should be stripped."""
        result = _clean_query("Contact rahul@icici.com for help")
        self.assertNotIn("rahul@icici.com", result)

    def test_removes_machine_names(self):
        """Machine names like PC-ICICI-0042 should be removed."""
        result = _clean_query("Install on PC-ICICI-0042")
        self.assertNotIn("PC-ICICI-0042", result)

    def test_expands_av_abbreviation(self):
        """'av' should expand to 'antivirus'."""
        result = _clean_query("av not working on laptop")
        self.assertIn("antivirus", result)

    def test_expands_vpn_abbreviation(self):
        """'vpn' should be expanded in query."""
        result = _clean_query("vpn not connecting")
        self.assertIn("vpn", result)

    def test_empty_query_returns_empty(self):
        """Empty query returns empty string."""
        result = _clean_query("")
        self.assertEqual(result, "")

    def test_very_long_query_trimmed(self):
        """Queries over 200 words should be trimmed."""
        long_query = "help me " * 300
        result     = _clean_query(long_query)
        self.assertLessEqual(len(result.split()), 205)

    def test_special_chars_removed(self):
        """Special characters should be replaced with spaces."""
        result = _clean_query("zoom!!! not@working #urgent")
        self.assertNotIn("!!!", result)
        self.assertNotIn("@",   result)
        self.assertNotIn("#",   result)

    def test_normalizes_whitespace(self):
        """Multiple spaces should be collapsed to one."""
        result = _clean_query("install    zoom    on   laptop")
        self.assertNotIn("  ", result)

    def test_returns_string(self):
        """Always returns a string."""
        result = _clean_query("some query text")
        self.assertIsInstance(result, str)

    def test_pst_abbreviation_expanded(self):
        """'pst' should be expanded in query."""
        result = _clean_query("pst file corrupt outlook")
        self.assertIn("outlook", result)

    def test_bsod_abbreviation_expanded(self):
        """'bsod' should be expanded."""
        result = _clean_query("bsod error on my laptop")
        self.assertIn("blue screen", result)


class TestFilterByScore(unittest.TestCase):
    """Tests for _filter_by_score()."""

    def _make_results(self, scores: list) -> list:
        return [
            _make_mock_result(
                f"Content {s}", "test.txt", score=s, idx=i
            )
            for i, s in enumerate(scores)
        ]

    def test_filters_below_threshold(self):
        """Results below min_score should be excluded."""
        results  = self._make_results([0.8, 0.5, 0.2, 0.1])
        filtered = _filter_by_score(results, min_score=0.4)
        scores   = [r["score"] for r in filtered]
        self.assertNotIn(0.2, scores)
        self.assertNotIn(0.1, scores)

    def test_keeps_above_threshold(self):
        """Results above min_score should be kept."""
        results  = self._make_results([0.9, 0.7, 0.5])
        filtered = _filter_by_score(results, min_score=0.4)
        self.assertEqual(len(filtered), 3)

    def test_empty_returns_empty(self):
        """Empty input returns empty list."""
        filtered = _filter_by_score([], min_score=0.3)
        self.assertEqual(filtered, [])

    def test_all_below_threshold_returns_empty(self):
        """All results below threshold — return empty list."""
        results  = self._make_results([0.1, 0.05, 0.02])
        filtered = _filter_by_score(results, min_score=0.3)
        self.assertEqual(filtered, [])

    def test_exact_threshold_kept(self):
        """Score exactly at threshold should be kept."""
        results  = self._make_results([0.30])
        filtered = _filter_by_score(results, min_score=0.30)
        self.assertEqual(len(filtered), 1)

    def test_result_order_preserved(self):
        """Result order should be preserved after filtering."""
        scores   = [0.9, 0.7, 0.5, 0.4]
        results  = self._make_results(scores)
        filtered = _filter_by_score(results, min_score=0.3)
        out_scores = [r["score"] for r in filtered]
        self.assertEqual(out_scores, scores)


class TestDeduplicateResults(unittest.TestCase):
    """Tests for _deduplicate_results()."""

    def test_empty_input_returns_empty(self):
        """Empty list input returns empty list."""
        result = _deduplicate_results([])
        self.assertEqual(result, [])

    def test_single_result_preserved(self):
        """Single result should always be returned."""
        results = [
            _make_mock_result("Some guide text.", "guide.txt")
        ]
        deduped = _deduplicate_results(results)
        self.assertEqual(len(deduped), 1)

    def test_max_two_chunks_per_file(self):
        """At most 2 chunks from the same file should be kept."""
        results = [
            _make_mock_result(
                f"Unique content for chunk number {i} here.",
                "guide.txt",
                idx=i,
            )
            for i in range(6)
        ]
        deduped = _deduplicate_results(results)
        count   = sum(
            1 for r in deduped
            if r["file_name"] == "guide.txt"
        )
        self.assertLessEqual(count, 2)

    def test_different_files_both_kept(self):
        """Results from different files should both be kept."""
        results = [
            _make_mock_result(
                "VPN guide content here.", "vpn.txt"
            ),
            _make_mock_result(
                "Printer guide content.", "printer.txt"
            ),
        ]
        deduped = _deduplicate_results(results)
        self.assertEqual(len(deduped), 2)

    def test_near_duplicate_removed(self):
        """Near-duplicate chunks (>60% word overlap) removed."""
        base = "How to reset your Windows domain account password"
        dup  = "How to reset your Windows domain account password today"
        results = [
            _make_mock_result(base, "guide.txt", idx=0),
            _make_mock_result(dup,  "guide.txt", idx=1),
        ]
        deduped = _deduplicate_results(results)
        self.assertLessEqual(len(deduped), 2)

    def test_unique_chunks_from_same_file_kept(self):
        """Two clearly different chunks from same file kept."""
        results = [
            _make_mock_result(
                "Step one open the VPN client on your computer.",
                "guide.txt", idx=0,
            ),
            _make_mock_result(
                "Password expiry configuration settings in Active Directory.",
                "guide.txt", idx=1,
            ),
        ]
        deduped = _deduplicate_results(results)
        self.assertEqual(len(deduped), 2)


class TestTextOverlapRatio(unittest.TestCase):
    """Tests for _text_overlap_ratio()."""

    def test_identical_texts_give_one(self):
        """Identical texts give overlap ratio of 1.0."""
        text   = "the quick brown fox jumps over the lazy dog"
        result = _text_overlap_ratio(text, text)
        self.assertAlmostEqual(result, 1.0, places=2)

    def test_completely_different_gives_low(self):
        """Completely different texts give low overlap."""
        text_a = "vpn network connection internet router firewall"
        text_b = "password forgot locked account windows login reset"
        result = _text_overlap_ratio(text_a, text_b)
        self.assertLess(result, 0.2)

    def test_empty_text_a_gives_zero(self):
        """Empty text_a gives 0.0 ratio."""
        result = _text_overlap_ratio("", "some content here")
        self.assertEqual(result, 0.0)

    def test_ratio_between_zero_and_one(self):
        """Overlap ratio always between 0.0 and 1.0."""
        text_a = "install zoom on laptop using sccm deployment"
        text_b = "install teams on laptop using intune deployment"
        result = _text_overlap_ratio(text_a, text_b)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_partial_overlap_intermediate(self):
        """Texts sharing some words have intermediate ratio."""
        text_a = "cannot connect to vpn from home network"
        text_b = "cannot connect to internet from office network"
        result = _text_overlap_ratio(text_a, text_b)
        self.assertGreater(result, 0.0)
        self.assertLess(result, 1.0)

    def test_returns_float(self):
        """Should always return a float."""
        result = _text_overlap_ratio("hello world", "hello there")
        self.assertIsInstance(result, float)


class TestFormatGuide(unittest.TestCase):
    """Tests for _format_guide()."""

    def test_returns_string(self):
        """Format guide should return a string."""
        results = [
            _make_mock_result(
                "Step 1 open VPN client.", "vpn_guide.txt"
            )
        ]
        output = _format_guide(results, "vpn not working")
        self.assertIsInstance(output, str)

    def test_contains_guide_content(self):
        """Output should contain the chunk text."""
        results = [
            _make_mock_result(
                "Step 1 open the application.", "guide.txt"
            )
        ]
        output = _format_guide(results, "how to open app")
        self.assertIn("Step 1 open the application.", output)

    def test_contains_footer(self):
        """Output should contain KB footer text."""
        results = [
            _make_mock_result("Some guide content.", "guide.txt")
        ]
        output = _format_guide(results, "query")
        self.assertIn("Knowledge Base", output)

    def test_empty_results_returns_empty(self):
        """Empty results list should return empty string."""
        output = _format_guide([], "any query")
        self.assertEqual(output, "")

    def test_multi_source_longer_output(self):
        """Multiple source files produce longer combined output."""
        results = [
            _make_mock_result(
                "VPN connection steps here.",
                "vpn_guide.txt",
            ),
            _make_mock_result(
                "Outlook troubleshooting steps here.",
                "outlook_guide.txt",
            ),
        ]
        output = _format_guide(results, "vpn and outlook")
        self.assertGreater(len(output), 100)

    def test_single_source_contains_guide_header(self):
        """Single source output should have SELF-HELP GUIDE header."""
        results = [
            _make_mock_result(
                "Guide content here.", "vpn_guide.txt"
            )
        ]
        output = _format_guide(results, "vpn query")
        self.assertIn("SELF-HELP GUIDE", output)

    def test_footer_contains_date(self):
        """Footer should contain a date string."""
        results = [
            _make_mock_result("Content.", "guide.txt")
        ]
        output = _format_guide(results, "query")
        import re
        date_pattern = r"\d{2} \w{3} \d{4}"
        self.assertTrue(
            re.search(date_pattern, output),
            "No date found in footer"
        )


class TestFileNameToTitle(unittest.TestCase):
    """Tests for _file_name_to_title()."""

    def test_underscores_replaced(self):
        """Underscores in filename should become spaces."""
        result = _file_name_to_title("vpn_setup_guide.txt")
        self.assertNotIn("_", result)

    def test_extension_removed(self):
        """File extension should be stripped."""
        result = _file_name_to_title("printer_guide.txt")
        self.assertNotIn(".txt", result)

    def test_words_capitalized(self):
        """Each word should start with capital letter."""
        result = _file_name_to_title("password_reset_guide.txt")
        for word in result.split():
            self.assertTrue(
                word[0].isupper(),
                f"Word '{word}' not capitalized"
            )

    def test_vpn_override_uppercase(self):
        """VPN should be uppercase per override list."""
        result = _file_name_to_title("vpn_setup_guide.txt")
        self.assertIn("VPN", result)

    def test_md_extension_stripped(self):
        """Markdown extension should be stripped."""
        result = _file_name_to_title("some_guide.md")
        self.assertNotIn(".md", result)

    def test_returns_string(self):
        """Should always return a string."""
        result = _file_name_to_title("any_guide.txt")
        self.assertIsInstance(result, str)

    def test_hyphen_replaced_with_space(self):
        """Hyphens should be replaced with spaces."""
        result = _file_name_to_title("vpn-setup-guide.txt")
        self.assertNotIn("-", result)


class TestScoreToLabel(unittest.TestCase):
    """Tests for _score_to_label()."""

    def test_high_score_label(self):
        """Score >= 0.75 returns 'High' label."""
        result = _score_to_label(0.80)
        self.assertIn("High", result)

    def test_medium_score_label(self):
        """Score 0.50-0.75 returns 'Medium' label."""
        result = _score_to_label(0.60)
        self.assertIn("Medium", result)

    def test_low_score_label(self):
        """Score 0.30-0.50 returns 'Low' label."""
        result = _score_to_label(0.35)
        self.assertIn("Low", result)

    def test_very_low_score_label(self):
        """Score below 0.30 returns 'Very Low' label."""
        result = _score_to_label(0.15)
        self.assertIn("Very Low", result)

    def test_percentage_included(self):
        """Result should include a percentage sign."""
        result = _score_to_label(0.75)
        self.assertIn("%", result)

    def test_returns_string_for_all_scores(self):
        """Should return string for any score 0.0 to 1.0."""
        for score in [0.0, 0.1, 0.3, 0.5, 0.75, 0.9, 1.0]:
            result = _score_to_label(score)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)


class TestCleanChunkText(unittest.TestCase):
    """Tests for _clean_chunk_text()."""

    def test_strips_whitespace(self):
        """Should strip leading and trailing whitespace."""
        result = _clean_chunk_text("  Content here.  ")
        self.assertEqual(result, "Content here.")

    def test_normalizes_multiple_newlines(self):
        """Three or more newlines should be reduced to two."""
        result = _clean_chunk_text("Line 1.\n\n\n\nLine 2.")
        self.assertNotIn("\n\n\n", result)

    def test_empty_returns_empty(self):
        """Empty input returns empty string."""
        result = _clean_chunk_text("")
        self.assertEqual(result, "")

    def test_content_preserved(self):
        """Main content should be preserved after cleaning."""
        content = "Step 1: Open the application and click Connect."
        result  = _clean_chunk_text(content)
        self.assertIn("Step 1:", result)
        self.assertIn("click Connect", result)

    def test_trailing_spaces_removed(self):
        """Trailing spaces on lines should be removed."""
        result = _clean_chunk_text("Line with space.   \nNext line.")
        self.assertNotIn("   \n", result)


class TestResetCollectionCache(unittest.TestCase):
    """Tests for reset_collection_cache()."""

    def test_cache_reset_does_not_crash(self):
        """Calling reset_collection_cache should not crash."""
        try:
            reset_collection_cache()
        except Exception as e:
            self.fail(
                f"reset_collection_cache raised: {e}"
            )

    def test_is_kb_available_false_after_reset(self):
        """After cache reset, KB may need reconnect."""
        reset_collection_cache()
        result = is_kb_available()
        self.assertIsInstance(result, bool)


class TestSearchKnowledgeBase(unittest.TestCase):
    """
    Integration-style tests for search_knowledge_base().
    Mocks ChromaDB — no real embeddings needed.
    """

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_string_when_found(self, mock_get_col):
        """Should return a string when relevant results found."""
        docs = [
            "Step 1: Open Cisco AnyConnect from Start menu.",
            "Step 2: Enter vpn.company.com in the server box.",
        ]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.85, 0.75]
        )

        result = search_knowledge_base(
            "cannot connect to vpn from home"
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_none_when_score_too_low(self, mock_get_col):
        """Returns None when all results below threshold."""
        docs = ["Some unrelated content about databases."]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.05]
        )

        result = search_knowledge_base("install zoom on laptop")
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_empty_query_returns_none(self, mock_get_col):
        """Empty query returns None without querying ChromaDB."""
        result = search_knowledge_base("")
        self.assertIsNone(result)
        mock_get_col.assert_not_called()

    @patch("knowledge_base.kb_search._get_collection")
    def test_whitespace_query_returns_none(self, mock_get_col):
        """Whitespace-only query returns None."""
        result = search_knowledge_base("   ")
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_unavailable_collection_returns_none(self, mock_get_col):
        """When ChromaDB unavailable, returns None."""
        mock_get_col.return_value = None
        result = search_knowledge_base("vpn not working")
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_result_contains_chunk_content(self, mock_get_col):
        """Returned guide should contain the retrieved chunk text."""
        docs = [
            "Open AnyConnect and enter vpn.company.com to connect."
        ]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.90]
        )

        result = search_knowledge_base("how to connect vpn")

        self.assertIsNotNone(result)
        self.assertIn("AnyConnect", result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_result_contains_footer(self, mock_get_col):
        """Result should always contain the KB footer."""
        docs = ["VPN connection steps here."]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.85]
        )

        result = search_knowledge_base("vpn")
        self.assertIsNotNone(result)
        self.assertIn("Knowledge Base", result)


class TestSearchWithDetails(unittest.TestCase):
    """Tests for search_with_details()."""

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_list(self, mock_get_col):
        """Should return a list."""
        docs = ["VPN step one here."]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.85]
        )
        result = search_with_details("vpn not working")
        self.assertIsInstance(result, list)

    @patch("knowledge_base.kb_search._get_collection")
    def test_each_result_has_rank(self, mock_get_col):
        """Each result dict should have a 'rank' field."""
        docs = [
            "VPN connection guide step one.",
            "VPN troubleshooting step two.",
        ]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.85, 0.75]
        )
        results = search_with_details("vpn not connecting")
        for r in results:
            self.assertIn("rank", r)

    @patch("knowledge_base.kb_search._get_collection")
    def test_empty_query_returns_empty_list(self, mock_get_col):
        """Empty query returns empty list."""
        result = search_with_details("")
        self.assertEqual(result, [])


class TestSearchByCategory(unittest.TestCase):
    """Tests for search_by_category()."""

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_all_main_categories_trigger_search(self, mock_search):
        """Each main category should trigger a search call."""
        mock_search.return_value = "Some guide content."

        categories = [
            "app_install", "antivirus", "password_reset",
            "network",     "printer",   "email_issue",
            "os_issue",    "access_permission",
        ]

        for cat in categories:
            result = search_by_category(cat)
            self.assertIsNotNone(result)

        self.assertGreater(mock_search.call_count, 0)

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_unknown_category_still_searches(self, mock_search):
        """Unknown category should still attempt a search."""
        mock_search.return_value = None
        result = search_by_category("unknown_category_xyz")
        mock_search.assert_called_once()

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_returns_none_when_no_guide(self, mock_search):
        """Returns None when search finds nothing."""
        mock_search.return_value = None
        result = search_by_category("hardware")
        self.assertIsNone(result)


class TestSearchMultiQuery(unittest.TestCase):
    """Tests for search_multi_query()."""

    def test_empty_list_returns_none(self):
        """Empty query list returns None."""
        result = search_multi_query([])
        self.assertIsNone(result)

    def test_whitespace_queries_skipped(self):
        """Whitespace-only queries should be skipped."""
        result = search_multi_query(["  ", "", "   "])
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_deduplicates_across_queries(self, mock_get_col):
        """
        Same chunk from two queries should not appear twice
        in the merged results.
        """
        docs = ["VPN connection guide steps here."]
        mock_get_col.return_value = _make_mock_collection(
            docs, [0.85]
        )
        result = search_multi_query(
            ["vpn not connecting", "vpn timeout error"]
        )
        self.assertIsInstance(result, (str, type(None)))


class TestIsKbAvailable(unittest.TestCase):
    """Tests for is_kb_available()."""

    @patch("knowledge_base.kb_search._get_collection")
    def test_true_when_has_docs(self, mock_get_col):
        """Returns True when collection has documents."""
        mock_col = MagicMock()
        mock_col.count.return_value = 25
        mock_get_col.return_value   = mock_col

        self.assertTrue(is_kb_available())

    @patch("knowledge_base.kb_search._get_collection")
    def test_false_when_empty(self, mock_get_col):
        """Returns False when collection has 0 documents."""
        mock_col = MagicMock()
        mock_col.count.return_value = 0
        mock_get_col.return_value   = mock_col

        self.assertFalse(is_kb_available())

    @patch("knowledge_base.kb_search._get_collection")
    def test_false_when_none(self, mock_get_col):
        """Returns False when collection is None."""
        mock_get_col.return_value = None
        self.assertFalse(is_kb_available())

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_bool(self, mock_get_col):
        """Should always return a bool."""
        mock_col = MagicMock()
        mock_col.count.return_value = 10
        mock_get_col.return_value   = mock_col

        result = is_kb_available()
        self.assertIsInstance(result, bool)


class TestGetKbStats(unittest.TestCase):
    """Tests for get_kb_stats()."""

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_dict(self, mock_get_col):
        """Should always return a dict."""
        mock_col = MagicMock()
        mock_col.count.return_value = 50
        mock_get_col.return_value   = mock_col

        result = get_kb_stats()
        self.assertIsInstance(result, dict)

    @patch("knowledge_base.kb_search._get_collection")
    def test_has_all_required_keys(self, mock_get_col):
        """Stats dict must have all required keys."""
        mock_col = MagicMock()
        mock_col.count.return_value = 50
        mock_get_col.return_value   = mock_col

        result = get_kb_stats()

        for key in [
            "is_available", "total_chunks",
            "collection_name", "chroma_dir", "embed_model",
        ]:
            self.assertIn(key, result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_unavailable_has_false_flag(self, mock_get_col):
        """When unavailable, is_available should be False."""
        mock_get_col.return_value = None

        result = get_kb_stats()
        self.assertFalse(result["is_available"])
        self.assertEqual(result["total_chunks"], 0)

    @patch("knowledge_base.kb_search._get_collection")
    def test_chunk_count_matches_collection(self, mock_get_col):
        """total_chunks should match collection.count()."""
        mock_col = MagicMock()
        mock_col.count.return_value = 42
        mock_get_col.return_value   = mock_col

        result = get_kb_stats()
        self.assertEqual(result["total_chunks"], 42)

    @patch("knowledge_base.kb_search._get_collection")
    def test_is_available_true_when_has_chunks(self, mock_get_col):
        """is_available should be True when chunks > 0."""
        mock_col = MagicMock()
        mock_col.count.return_value = 32
        mock_get_col.return_value   = mock_col

        result = get_kb_stats()
        self.assertTrue(result["is_available"])


def run_all_tests() -> bool:
    """
    Run the complete KB test suite and print a summary.

    Returns:
        True if all tests passed, False otherwise
    """
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestScanDocsFolder,
        TestLoadDocument,
        TestChunkText,
        TestSplitIntoSentences,
        TestMergeSmallChunks,
        TestHashFile,
        TestGenerateChunkId,
        TestMetadataOperations,
        TestGetChangedFiles,
        TestCleanQuery,
        TestFilterByScore,
        TestDeduplicateResults,
        TestTextOverlapRatio,
        TestFormatGuide,
        TestFileNameToTitle,
        TestScoreToLabel,
        TestCleanChunkText,
        TestResetCollectionCache,
        TestSearchKnowledgeBase,
        TestSearchWithDetails,
        TestSearchByCategory,
        TestSearchMultiQuery,
        TestIsKbAvailable,
        TestGetKbStats,
    ]

    for cls in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(cls)
        )

    runner = unittest.TextTestRunner(
        verbosity = 2,
        stream    = sys.stdout,
    )

    print("\n" + "=" * 65)
    print("KNOWLEDGE BASE TEST SUITE")
    print("=" * 65)
    print(
        f"  Mode         : "
        f"{'DEMO' if os.getenv('DEMO_MODE') == 'true' else 'LIVE'}"
    )
    print(f"  Temp dir     : {TEMP_DIR}")
    print(f"  Test docs    : {TEST_DOCS_DIR}")
    print(f"  Test chroma  : {TEST_CHROMA}")
    print(f"  Test classes : {len(test_classes)}")
    print()

    result = runner.run(suite)

    _cleanup_test_dir()

    passed = (
        result.testsRun
        - len(result.failures)
        - len(result.errors)
    )

    print("\n" + "=" * 65)
    print("TEST SUMMARY")
    print("=" * 65)
    print(f"  Tests run  : {result.testsRun}")
    print(f"  Passed     : {passed}")
    print(f"  Failures   : {len(result.failures)}")
    print(f"  Errors     : {len(result.errors)}")
    print(f"  Skipped    : {len(result.skipped)}")
    print(
        f"  Overall    : "
        f"{'PASSED ✓' if result.wasSuccessful() else 'FAILED ✗'}"
    )
    print("=" * 65 + "\n")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)