# import os
# import logging
# from dotenv import load_dotenv

# from automation.runner import run_automation
# from knowledge_base.kb_search import search_knowledge_base
# from agent.escalation import escalate_ticket
# from agent.notifier import notify_user
# from database.db_logger import log_ticket_action
# from ingestion.freshdesk_client import (
#     close_ticket,
#     update_ticket_status,
#     add_internal_note,
#     add_public_reply,
#     add_tag_to_ticket,
#     set_ticket_priority,
# )

# load_dotenv()

# log = logging.getLogger(__name__)

# ESCALATION_AGENT_ID = int(os.getenv("ESCALATION_AGENT_ID", 0))


# def orchestrate(ticket: dict, classification: dict) -> bool:
#     """
#     Main orchestrator function called by main.py for every ticket.
#     Decides the full resolution path and executes it end to end.

#     Decision flow:
#         1. Validate ticket has minimum required data
#         2. Update Freshdesk priority based on AI classification
#         3. If can_auto_resolve → try automation
#            a. Automation success  → close ticket + notify user
#            b. Automation fail     → search KB → send guide or escalate
#         4. If cannot auto_resolve → search KB → send guide + escalate
#         5. Log everything to database

#     Args:
#         ticket         : Clean parsed ticket dict from ticket_parser.py
#         classification : Classification dict from ai_classifier.py

#     Returns:
#         True if ticket was fully resolved automatically
#         False if ticket was escalated or resolution failed
#     """
#     ticket_id    = ticket.get("id", 0)
#     subject      = ticket.get("subject", "No subject")
#     requester    = ticket.get("requester_email", "")
#     requester_name = ticket.get("requester_name", "User")
#     machine      = ticket.get("machine_name", "UNKNOWN")
#     category     = classification.get("category", "other")
#     priority     = classification.get("priority", "medium")
#     can_auto     = classification.get("can_auto_resolve", False)
#     action       = classification.get("suggested_action", "Manual review required.")
#     confidence   = classification.get("confidence", "low")

#     log.info(f"")
#     log.info(f"{'='*55}")
#     log.info(f"ORCHESTRATING TICKET #{ticket_id}")
#     log.info(f"  Subject    : {subject}")
#     log.info(f"  Category   : {category}")
#     log.info(f"  Priority   : {priority}")
#     log.info(f"  Auto       : {can_auto}")
#     log.info(f"  Machine    : {machine}")
#     log.info(f"  Confidence : {confidence}")
#     log.info(f"{'='*55}")

#     if not _validate_ticket(ticket):
#         log.error(f"Ticket #{ticket_id} failed validation. Escalating.")
#         _handle_escalation(
#             ticket=ticket,
#             classification=classification,
#             reason="Ticket data incomplete — needs manual review.",
#             tag="validation-failed"
#         )
#         return False

#     _sync_priority_to_freshdesk(ticket_id, priority)
#     _tag_ticket(ticket_id, category, confidence)

#     if can_auto:
#         return _handle_auto_resolve(ticket, classification)
#     else:
#         return _handle_manual_escalation(ticket, classification)


# def _handle_auto_resolve(ticket: dict, classification: dict) -> bool:
#     """
#     Attempt to auto-resolve the ticket using automation scripts.
#     If automation succeeds → close ticket and notify user.
#     If automation fails   → search KB and escalate.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict

#     Returns:
#         True if resolved, False if escalated
#     """
#     ticket_id      = ticket.get("id")
#     subject        = ticket.get("subject", "")
#     requester      = ticket.get("requester_email", "")
#     requester_name = ticket.get("requester_name", "User")
#     category       = classification.get("category", "other")
#     action         = classification.get("suggested_action", "")

#     log.info(f"Ticket #{ticket_id}: Attempting auto-resolution...")

#     add_internal_note(
#         ticket_id,
#         f"[AI Orchestrator] Auto-resolution started.\n"
#         f"Category : {category}\n"
#         f"Action   : {action}\n"
#         f"Machine  : {ticket.get('machine_name', 'UNKNOWN')}"
#     )

#     success = run_automation(ticket, classification)

#     if success:
#         log.info(f"Ticket #{ticket_id}: Auto-resolution SUCCEEDED.")

#         resolution_message = _build_resolution_message(
#             requester_name=requester_name,
#             subject=subject,
#             action=action,
#             category=category,
#         )

#         close_ticket(ticket_id, action)

#         notify_user(
#             email=requester,
#             ticket_id=ticket_id,
#             subject=subject,
#             message=resolution_message,
#         )

#         add_public_reply(ticket_id, resolution_message)

#         log_ticket_action(
#             ticket_id=ticket_id,
#             category=category,
#             priority=classification.get("priority", "medium"),
#             action_taken=action,
#             resolved_by="AI_AUTO",
#             status="RESOLVED",
#         )

#         log.info(f"Ticket #{ticket_id}: Closed and user notified.")
#         return True

#     else:
#         log.warning(
#             f"Ticket #{ticket_id}: Auto-resolution FAILED. "
#             "Searching knowledge base..."
#         )

#         add_internal_note(
#             ticket_id,
#             f"[AI Orchestrator] Auto-resolution failed.\n"
#             f"Searching knowledge base for: {subject}"
#         )

#         kb_guide = search_knowledge_base(ticket.get("description", ""))

#         if kb_guide:
#             log.info(f"Ticket #{ticket_id}: KB guide found. Sending to user.")

#             kb_message = _build_kb_message(
#                 requester_name=requester_name,
#                 subject=subject,
#                 guide=kb_guide,
#             )

#             add_public_reply(ticket_id, kb_message)

#             notify_user(
#                 email=requester,
#                 ticket_id=ticket_id,
#                 subject=subject,
#                 message=kb_message,
#             )

#             _handle_escalation(
#                 ticket=ticket,
#                 classification=classification,
#                 reason=(
#                     f"Auto-resolution failed. KB guide sent to user.\n"
#                     f"Engineer please verify fix was applied.\n"
#                     f"Suggested: {action}"
#                 ),
#                 tag="auto-failed-kb-sent"
#             )

#             log_ticket_action(
#                 ticket_id=ticket_id,
#                 category=category,
#                 priority=classification.get("priority", "medium"),
#                 action_taken="Auto-resolve failed. KB guide sent.",
#                 resolved_by="KB+ESCALATION",
#                 status="ESCALATED",
#             )

#         else:
#             log.warning(
#                 f"Ticket #{ticket_id}: No KB guide found. "
#                 "Escalating directly."
#             )

#             _handle_escalation(
#                 ticket=ticket,
#                 classification=classification,
#                 reason=(
#                     f"Auto-resolution failed. No KB guide found.\n"
#                     f"Suggested action: {action}"
#                 ),
#                 tag="auto-failed-no-kb"
#             )

#             log_ticket_action(
#                 ticket_id=ticket_id,
#                 category=category,
#                 priority=classification.get("priority", "medium"),
#                 action_taken="Auto-resolve failed. Escalated.",
#                 resolved_by="ESCALATION",
#                 status="ESCALATED",
#             )

#         return False


# def _handle_manual_escalation(ticket: dict, classification: dict) -> bool:
#     """
#     Handle tickets that cannot be auto-resolved.
#     Searches KB first to send self-help guide, then escalates to engineer.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict

#     Returns:
#         Always returns False (ticket not auto-resolved)
#     """
#     ticket_id      = ticket.get("id")
#     subject        = ticket.get("subject", "")
#     requester      = ticket.get("requester_email", "")
#     requester_name = ticket.get("requester_name", "User")
#     category       = classification.get("category", "other")
#     action         = classification.get("suggested_action", "")

#     log.info(
#         f"Ticket #{ticket_id}: Cannot auto-resolve. "
#         "Searching KB before escalating..."
#     )

#     kb_guide = search_knowledge_base(ticket.get("description", ""))

#     if kb_guide:
#         log.info(f"Ticket #{ticket_id}: KB guide found. Sending to user.")

#         kb_message = _build_kb_message(
#             requester_name=requester_name,
#             subject=subject,
#             guide=kb_guide,
#         )

#         add_public_reply(ticket_id, kb_message)

#         notify_user(
#             email=requester,
#             ticket_id=ticket_id,
#             subject=subject,
#             message=kb_message,
#         )

#         escalation_note = (
#             f"KB self-help guide sent to user.\n"
#             f"If guide does not resolve — engineer review needed.\n"
#             f"Category : {category}\n"
#             f"Suggested: {action}"
#         )

#     else:
#         log.info(f"Ticket #{ticket_id}: No KB guide. Escalating directly.")

#         escalation_note = (
#             f"No KB guide available for this issue.\n"
#             f"Category : {category}\n"
#             f"Suggested: {action}"
#         )

#     _handle_escalation(
#         ticket=ticket,
#         classification=classification,
#         reason=escalation_note,
#         tag="manual-escalation"
#     )

#     log_ticket_action(
#         ticket_id=ticket_id,
#         category=category,
#         priority=classification.get("priority", "medium"),
#         action_taken=f"KB guide sent + escalated. {action}",
#         resolved_by="ENGINEER_QUEUE",
#         status="ESCALATED",
#     )

#     return False


# def _handle_escalation(
#     ticket        : dict,
#     classification: dict,
#     reason        : str,
#     tag           : str = "escalated"
# ) -> None:
#     """
#     Escalate a ticket to the engineer queue.
#     Updates status to pending, adds internal note,
#     assigns to escalation agent, and tags the ticket.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict
#         reason         : Text explaining why escalation happened
#         tag            : Tag string to add to the ticket
#     """
#     ticket_id = ticket.get("id")
#     category  = classification.get("category", "other")
#     priority  = classification.get("priority", "medium")
#     action    = classification.get("suggested_action", "")

#     escalate_ticket(
#         ticket_id=ticket_id,
#         note=reason,
#         agent_id=ESCALATION_AGENT_ID if ESCALATION_AGENT_ID else None,
#     )

#     add_tag_to_ticket(ticket_id, [tag, f"cat-{category}", "ai-processed"])

#     log.info(f"Ticket #{ticket_id}: Escalated — {reason[:80]}")


# def _validate_ticket(ticket: dict) -> bool:
#     """
#     Check if a ticket has the minimum required fields
#     to attempt processing.

#     Args:
#         ticket : Parsed ticket dict

#     Returns:
#         True if valid, False if critical fields are missing
#     """
#     ticket_id = ticket.get("id", 0)

#     if not ticket_id or ticket_id == 0:
#         log.error("Ticket has no ID.")
#         return False

#     if not ticket.get("subject", "").strip():
#         log.warning(f"Ticket #{ticket_id} has no subject.")

#     if not ticket.get("description", "").strip():
#         log.warning(f"Ticket #{ticket_id} has no description.")

#     if not ticket.get("requester_email", "").strip():
#         log.error(f"Ticket #{ticket_id} has no requester email. Cannot notify user.")
#         return False

#     return True


# def _sync_priority_to_freshdesk(ticket_id: int, ai_priority: str) -> None:
#     """
#     Update the Freshdesk ticket priority to match what the AI classified.
#     This ensures engineers see the correct priority in Freshdesk dashboard.

#     Args:
#         ticket_id   : Freshdesk ticket ID
#         ai_priority : Priority string from classifier — low/medium/high/urgent
#     """
#     priority_map = {
#         "low"    : "low",
#         "medium" : "medium",
#         "high"   : "high",
#         "urgent" : "urgent",
#     }

#     fd_priority = priority_map.get(ai_priority, "medium")
#     set_ticket_priority(ticket_id, fd_priority)
#     log.info(f"Ticket #{ticket_id}: Priority set to '{fd_priority}' in Freshdesk.")


# def _tag_ticket(ticket_id: int, category: str, confidence: str) -> None:
#     """
#     Add AI-generated tags to the ticket in Freshdesk.
#     Tags help with filtering, reporting, and searching.

#     Args:
#         ticket_id  : Freshdesk ticket ID
#         category   : Classified category string
#         confidence : Classifier confidence — high/medium/low
#     """
#     tags = [
#         "ai-classified",
#         f"cat-{category}",
#         f"confidence-{confidence}",
#     ]
#     add_tag_to_ticket(ticket_id, tags)
#     log.debug(f"Ticket #{ticket_id}: Tagged with {tags}")


# def _build_resolution_message(
#     requester_name: str,
#     subject       : str,
#     action        : str,
#     category      : str,
# ) -> str:
#     """
#     Build the email/reply message sent to the user
#     when their ticket is auto-resolved.

#     Args:
#         requester_name : Name of the user
#         subject        : Ticket subject
#         action         : What action was taken
#         category       : Ticket category

#     Returns:
#         Formatted message string
#     """
#     category_labels = {
#         "app_install"       : "software installation",
#         "antivirus"         : "antivirus update",
#         "password_reset"    : "password reset",
#         "os_issue"          : "system repair",
#         "printer"           : "printer fix",
#         "email_issue"       : "email repair",
#         "network"           : "network fix",
#     }

#     label = category_labels.get(category, "issue resolution")

#     message = (
#         f"Dear {requester_name},\n\n"
#         f"Your ticket '{subject}' has been automatically resolved "
#         f"by our AI support system.\n\n"
#         f"Action taken: {action}\n\n"
#         f"Your {label} has been completed remotely on your machine. "
#         f"Please restart your computer if required and verify the issue is resolved.\n\n"
#         f"If you are still facing any issues, please raise a new ticket "
#         f"and our team will assist you promptly.\n\n"
#         f"Ticket ID    : #{subject}\n"
#         f"Resolved by  : AI Auto-Resolver\n\n"
#         f"Thank you,\n"
#         f"IT Support Team\n"
#         f"ICICI Bank"
#     )

#     return message


# def _build_kb_message(
#     requester_name: str,
#     subject       : str,
#     guide         : str,
# ) -> str:
#     """
#     Build the email/reply message sent to the user
#     when a knowledge base guide is found for their issue.

#     Args:
#         requester_name : Name of the user
#         subject        : Ticket subject
#         guide          : KB guide content text

#     Returns:
#         Formatted message string
#     """
#     message = (
#         f"Dear {requester_name},\n\n"
#         f"Thank you for raising a ticket regarding '{subject}'.\n\n"
#         f"We found a self-help guide that may resolve your issue:\n\n"
#         f"{'─'*50}\n"
#         f"{guide}\n"
#         f"{'─'*50}\n\n"
#         f"Please follow the steps above and let us know if this resolves the issue.\n\n"
#         f"If the problem persists, an engineer from our team will follow up "
#         f"with you shortly.\n\n"
#         f"Thank you,\n"
#         f"IT Support Team\n"
#         f"ICICI Bank"
#     )

#     return message


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(message)s"
#     )

#     print("\n" + "=" * 60)
#     print("ORCHESTRATOR TEST RUN")
#     print("=" * 60 + "\n")

#     test_cases = [
#         {
#             "label": "Auto-resolvable — App Install",
#             "ticket": {
#                 "id"              : 1001,
#                 "subject"         : "Install Zoom on my laptop",
#                 "description"     : "I need Zoom installed on PC-ICICI-0042 urgently.",
#                 "requester_email" : "rahul.sharma@icici.com",
#                 "requester_name"  : "Rahul Sharma",
#                 "machine_name"    : "PC-ICICI-0042",
#                 "mentioned_apps"  : ["zoom"],
#                 "urgency_level"   : "high",
#             },
#             "classification": {
#                 "category"        : "app_install",
#                 "priority"        : "high",
#                 "can_auto_resolve": True,
#                 "suggested_action": "Push Zoom installation via SCCM.",
#                 "confidence"      : "high",
#             },
#         },
#         {
#             "label": "Non-auto-resolvable — Hardware Issue",
#             "ticket": {
#                 "id"              : 1002,
#                 "subject"         : "Laptop screen is flickering",
#                 "description"     : "My laptop screen has been flickering since morning.",
#                 "requester_email" : "priya.mehta@icici.com",
#                 "requester_name"  : "Priya Mehta",
#                 "machine_name"    : "LAPTOP-ICICI-115",
#                 "mentioned_apps"  : [],
#                 "urgency_level"   : "medium",
#             },
#             "classification": {
#                 "category"        : "hardware",
#                 "priority"        : "medium",
#                 "can_auto_resolve": False,
#                 "suggested_action": "Schedule on-site hardware inspection.",
#                 "confidence"      : "high",
#             },
#         },
#         {
#             "label": "Missing email — Validation fail",
#             "ticket": {
#                 "id"              : 1003,
#                 "subject"         : "Cannot print documents",
#                 "description"     : "Printer is showing offline.",
#                 "requester_email" : "",
#                 "requester_name"  : "Unknown",
#                 "machine_name"    : "PC-ICICI-0099",
#                 "mentioned_apps"  : [],
#                 "urgency_level"   : "low",
#             },
#             "classification": {
#                 "category"        : "printer",
#                 "priority"        : "low",
#                 "can_auto_resolve": True,
#                 "suggested_action": "Restart print spooler remotely.",
#                 "confidence"      : "medium",
#             },
#         },
#     ]

#     for tc in test_cases:
#         print(f"\nTest: {tc['label']}")
#         print(f"  Ticket  : #{tc['ticket']['id']} — {tc['ticket']['subject']}")
#         print(f"  Category: {tc['classification']['category']}")
#         print(f"  Auto    : {tc['classification']['can_auto_resolve']}")

#         result = orchestrate(tc["ticket"], tc["classification"])

#         print(f"  Result  : {'RESOLVED' if result else 'ESCALATED/FAILED'}")
#         print("-" * 55)


import os
import logging
from datetime import datetime, timezone
from dotenv   import load_dotenv

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE           = os.getenv("DEMO_MODE",           "false").strip().lower() == "true"
DRY_RUN_MODE        = os.getenv("DRY_RUN_MODE",        "false").strip().lower() == "true"
ESCALATION_AGENT_ID = int(os.getenv("ESCALATION_AGENT_ID", 0))
COMPANY_NAME        = os.getenv("COMPANY_NAME",        "ICICI Bank")
FEATURE_KB_SEARCH   = os.getenv("FEATURE_KB_SEARCH",   "true").strip().lower() == "true"

from automation.runner      import run_automation
from knowledge_base.kb_search import (
    search_knowledge_base,
    is_kb_available,
)
from agent.escalation import escalate_ticket
from agent.notifier   import notify_user
from database.db_logger import log_ticket_action
from ingestion.freshdesk_client import (
    close_ticket,
    update_ticket_status,
    add_internal_note,
    add_public_reply,
    add_tag_to_ticket,
    set_ticket_priority,
)


def _now() -> str:
    """
    Return current UTC time as a formatted string.
    Uses timezone-aware datetime to avoid deprecation warning.

    Returns:
        Formatted datetime string e.g. '17 May 2026 10:30 UTC'
    """
    return datetime.now(timezone.utc).strftime(
        "%d %b %Y %H:%M UTC"
    )


def orchestrate(ticket: dict, classification: dict) -> bool:
    """
    Main orchestrator called by main.py for every ticket.
    Decides the full resolution path and executes it end to end.
    In demo mode uses real logic but with simulated API calls.

    Decision flow:
        1. Validate ticket has minimum required data
        2. Update Freshdesk priority to match AI classification
        3. Tag ticket with AI classification metadata
        4. If can_auto_resolve → try automation scripts
           a. Success  → close ticket + notify user
           b. Failure  → search KB → send guide or escalate
        5. If cannot auto_resolve → search KB → send guide + escalate
        6. Log all actions to database

    Args:
        ticket         : Clean parsed ticket dict from ticket_parser
        classification : Classification dict from ai_classifier

    Returns:
        True if ticket was fully auto-resolved
        False if ticket was escalated or resolution failed
    """
    ticket_id      = ticket.get("id",              0)
    subject        = ticket.get("subject",         "No subject")
    requester      = ticket.get("requester_email", "")
    requester_name = ticket.get("requester_name",  "User")
    machine        = ticket.get("machine_name",    "UNKNOWN")
    category       = classification.get("category",         "other")
    priority       = classification.get("priority",         "medium")
    can_auto       = classification.get("can_auto_resolve", False)
    action         = classification.get(
        "suggested_action", "Manual review required."
    )
    confidence     = classification.get("confidence", "low")

    mode = "[DEMO] " if DEMO_MODE else ""

    log.info("")
    log.info("=" * 55)
    log.info(
        f"{mode}ORCHESTRATING TICKET #{ticket_id}"
    )
    log.info(f"  Subject    : {subject[:55]}")
    log.info(f"  Category   : {category}")
    log.info(f"  Priority   : {priority}")
    log.info(f"  Auto       : {can_auto}")
    log.info(f"  Machine    : {machine}")
    log.info(f"  Confidence : {confidence}")
    log.info("=" * 55)

    if not _validate_ticket(ticket):
        log.error(
            f"Ticket #{ticket_id} failed validation. "
            "Escalating."
        )
        _handle_escalation(
            ticket         = ticket,
            classification = classification,
            reason         = (
                "Ticket data incomplete — needs manual review."
            ),
            tag            = "validation-failed",
        )
        return False

    _sync_priority_to_freshdesk(ticket_id, priority)
    _tag_ticket(ticket_id, category, confidence)

    if can_auto:
        return _handle_auto_resolve(ticket, classification)
    else:
        return _handle_manual_escalation(ticket, classification)


def _handle_auto_resolve(
    ticket        : dict,
    classification: dict,
) -> bool:
    """
    Attempt to auto-resolve via automation scripts.
    On success → close ticket and notify user.
    On failure → search KB and escalate.
    In demo mode uses simulated automation results.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        True if resolved, False if escalated
    """
    ticket_id      = ticket.get("id",              0)
    subject        = ticket.get("subject",         "")
    requester      = ticket.get("requester_email", "")
    requester_name = ticket.get("requester_name",  "User")
    category       = classification.get("category", "other")
    priority       = classification.get("priority", "medium")
    action         = classification.get(
        "suggested_action", ""
    )

    mode = "[DEMO] " if DEMO_MODE else ""
    log.info(
        f"{mode}Ticket #{ticket_id}: "
        "Attempting auto-resolution..."
    )

    add_internal_note(
        ticket_id,
        f"[AI Orchestrator — {_now()}]\n"
        f"Auto-resolution started.\n"
        f"Category : {category}\n"
        f"Action   : {action}\n"
        f"Machine  : {ticket.get('machine_name', 'UNKNOWN')}"
    )

    success = run_automation(ticket, classification)

    if success:
        log.info(
            f"{mode}Ticket #{ticket_id}: "
            "Auto-resolution SUCCEEDED ✓"
        )

        resolution_message = _build_resolution_message(
            requester_name = requester_name,
            subject        = subject,
            action         = action,
            category       = category,
        )

        if not DRY_RUN_MODE:
            close_ticket(ticket_id, action)

        notify_user(
            email      = requester,
            ticket_id  = ticket_id,
            subject    = subject,
            message    = resolution_message,
            notif_type = "resolved",
        )

        if not DRY_RUN_MODE:
            add_public_reply(ticket_id, resolution_message)

        add_tag_to_ticket(
            ticket_id,
            ["ai-resolved", f"cat-{category}", "auto-closed"]
        )

        try:
            log_ticket_action(
                ticket_id    = ticket_id,
                category     = category,
                priority     = priority,
                action_taken = action,
                resolved_by  = "AI_AUTO",
                status       = "RESOLVED",
            )
        except Exception as e:
            log.warning(
                f"DB log failed for ticket #{ticket_id}: {e}"
            )

        log.info(
            f"{mode}Ticket #{ticket_id}: "
            "Closed and user notified."
        )
        return True

    else:
        log.warning(
            f"{mode}Ticket #{ticket_id}: "
            "Auto-resolution FAILED — searching KB..."
        )

        add_internal_note(
            ticket_id,
            f"[AI Orchestrator — {_now()}]\n"
            f"Auto-resolution FAILED.\n"
            f"Searching KB for: {subject}"
        )

        kb_guide = None
        if FEATURE_KB_SEARCH and is_kb_available():
            try:
                kb_guide = search_knowledge_base(
                    ticket.get("description", "")
                )
            except Exception as e:
                log.warning(
                    f"KB search error for ticket #{ticket_id}: {e}"
                )

        if kb_guide:
            log.info(
                f"{mode}Ticket #{ticket_id}: "
                "KB guide found — sending to user."
            )

            kb_message = _build_kb_message(
                requester_name = requester_name,
                subject        = subject,
                guide          = kb_guide,
            )

            if not DRY_RUN_MODE:
                add_public_reply(ticket_id, kb_message)

            notify_user(
                email      = requester,
                ticket_id  = ticket_id,
                subject    = subject,
                message    = kb_message,
                notif_type = "kb_guide_sent",
            )

            _handle_escalation(
                ticket         = ticket,
                classification = classification,
                reason         = (
                    f"Auto-resolution failed. "
                    f"KB guide sent to user.\n"
                    f"Engineer — please verify fix applied.\n"
                    f"Suggested: {action}"
                ),
                tag            = "auto-failed-kb-sent",
            )

            try:
                log_ticket_action(
                    ticket_id    = ticket_id,
                    category     = category,
                    priority     = priority,
                    action_taken = "Auto-resolve failed. KB guide sent.",
                    resolved_by  = "KB+ESCALATION",
                    status       = "ESCALATED",
                )
            except Exception as e:
                log.warning(
                    f"DB log failed for ticket #{ticket_id}: {e}"
                )

        else:
            log.warning(
                f"{mode}Ticket #{ticket_id}: "
                "No KB guide found — escalating."
            )

            _handle_escalation(
                ticket         = ticket,
                classification = classification,
                reason         = (
                    f"Auto-resolution failed. "
                    f"No KB guide found.\n"
                    f"Suggested: {action}"
                ),
                tag            = "auto-failed-no-kb",
            )

            try:
                log_ticket_action(
                    ticket_id    = ticket_id,
                    category     = category,
                    priority     = priority,
                    action_taken = "Auto-resolve failed. Escalated.",
                    resolved_by  = "ESCALATION",
                    status       = "ESCALATED",
                )
            except Exception as e:
                log.warning(
                    f"DB log failed for ticket #{ticket_id}: {e}"
                )

        return False


def _handle_manual_escalation(
    ticket        : dict,
    classification: dict,
) -> bool:
    """
    Handle tickets that cannot be auto-resolved.
    Searches KB first to send self-help guide, then escalates.
    In demo mode uses real KB index if available.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        Always False — ticket is not auto-resolved
    """
    ticket_id      = ticket.get("id",              0)
    subject        = ticket.get("subject",         "")
    requester      = ticket.get("requester_email", "")
    requester_name = ticket.get("requester_name",  "User")
    category       = classification.get("category", "other")
    priority       = classification.get("priority", "medium")
    action         = classification.get(
        "suggested_action", ""
    )

    mode = "[DEMO] " if DEMO_MODE else ""
    log.info(
        f"{mode}Ticket #{ticket_id}: "
        "Cannot auto-resolve — searching KB..."
    )

    add_internal_note(
        ticket_id,
        f"[AI Orchestrator — {_now()}]\n"
        f"Cannot auto-resolve — routing to engineer.\n"
        f"Category : {category}\n"
        f"Action   : {action}"
    )

    kb_guide = None
    if FEATURE_KB_SEARCH and is_kb_available():
        try:
            kb_guide = search_knowledge_base(
                ticket.get("description", "")
            )
        except Exception as e:
            log.warning(
                f"KB search error for ticket #{ticket_id}: {e}"
            )

    if kb_guide:
        log.info(
            f"{mode}Ticket #{ticket_id}: "
            "KB guide found — sending to user."
        )

        kb_message = _build_kb_message(
            requester_name = requester_name,
            subject        = subject,
            guide          = kb_guide,
        )

        if not DRY_RUN_MODE:
            add_public_reply(ticket_id, kb_message)

        notify_user(
            email      = requester,
            ticket_id  = ticket_id,
            subject    = subject,
            message    = kb_message,
            notif_type = "kb_guide_sent",
        )

        escalation_note = (
            f"KB self-help guide sent to user.\n"
            f"Engineer — please verify issue resolved.\n"
            f"Category : {category}\n"
            f"Suggested: {action}"
        )
        resolved_by = "KB+ESCALATION"

    else:
        log.info(
            f"{mode}Ticket #{ticket_id}: "
            "No KB guide — escalating directly."
        )
        escalation_note = (
            f"No KB guide found for this issue.\n"
            f"Category : {category}\n"
            f"Suggested: {action}"
        )
        resolved_by = "ENGINEER_QUEUE"

    _handle_escalation(
        ticket         = ticket,
        classification = classification,
        reason         = escalation_note,
        tag            = "manual-escalation",
    )

    try:
        log_ticket_action(
            ticket_id    = ticket_id,
            category     = category,
            priority     = priority,
            action_taken = (
                f"KB guide sent + escalated. {action}"
                if kb_guide else
                f"Escalated — {action}"
            ),
            resolved_by  = resolved_by,
            status       = "ESCALATED",
        )
    except Exception as e:
        log.warning(
            f"DB log failed for ticket #{ticket_id}: {e}"
        )

    return False


def _handle_escalation(
    ticket        : dict,
    classification: dict,
    reason        : str,
    tag           : str = "escalated",
) -> None:
    """
    Escalate a ticket to the engineer queue.
    Updates status, adds internal note, assigns agent, tags ticket.
    In demo mode simulates all Freshdesk API calls.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict
        reason         : Why escalation is happening
        tag            : Freshdesk tag to apply
    """
    ticket_id = ticket.get("id", 0)
    category  = classification.get("category", "other")

    mode = "[DEMO] " if DEMO_MODE else ""

    try:
        escalate_ticket(
            ticket_id = ticket_id,
            note      = reason,
            agent_id  = (
                ESCALATION_AGENT_ID
                if ESCALATION_AGENT_ID and ESCALATION_AGENT_ID != 0
                else None
            ),
        )
    except Exception as e:
        log.warning(
            f"Escalation API call failed for "
            f"ticket #{ticket_id}: {e}"
        )

    try:
        add_tag_to_ticket(
            ticket_id,
            [tag, f"cat-{category}", "ai-processed"]
        )
    except Exception as e:
        log.warning(
            f"Tag failed for ticket #{ticket_id}: {e}"
        )

    log.info(
        f"{mode}Ticket #{ticket_id}: "
        f"Escalated — {reason[:80]}"
    )


def _validate_ticket(ticket: dict) -> bool:
    """
    Check if a ticket has the minimum required fields
    to attempt processing.

    Args:
        ticket : Parsed ticket dict

    Returns:
        True if valid, False if critical fields are missing
    """
    ticket_id = ticket.get("id", 0)

    if not ticket_id or ticket_id == 0:
        log.error("Ticket has no ID — cannot process.")
        return False

    if not ticket.get("subject", "").strip():
        log.warning(
            f"Ticket #{ticket_id} has no subject."
        )

    if not ticket.get("description", "").strip():
        log.warning(
            f"Ticket #{ticket_id} has no description."
        )

    if not ticket.get("requester_email", "").strip():
        log.error(
            f"Ticket #{ticket_id} has no requester email. "
            "Cannot notify user."
        )
        return False

    return True


def _sync_priority_to_freshdesk(
    ticket_id  : int,
    ai_priority: str,
) -> None:
    """
    Update Freshdesk ticket priority to match AI classification.
    In demo mode simulates the update without real API call.

    Args:
        ticket_id   : Freshdesk ticket ID
        ai_priority : Priority from classifier — low/medium/high/urgent
    """
    valid_priorities = {"low", "medium", "high", "urgent"}
    fd_priority      = (
        ai_priority if ai_priority in valid_priorities
        else "medium"
    )

    try:
        set_ticket_priority(ticket_id, fd_priority)
        log.info(
            f"Ticket #{ticket_id}: Priority set to "
            f"'{fd_priority}' in Freshdesk."
        )
    except Exception as e:
        log.warning(
            f"Priority sync failed for ticket #{ticket_id}: {e}"
        )


def _tag_ticket(
    ticket_id : int,
    category  : str,
    confidence: str,
) -> None:
    """
    Add AI-generated tags to the ticket in Freshdesk.
    Tags help with filtering and reporting.
    In demo mode stores tags in the demo tag store.

    Args:
        ticket_id  : Freshdesk ticket ID
        category   : Classified category string
        confidence : Classifier confidence — high/medium/low
    """
    tags = [
        "ai-classified",
        f"cat-{category}",
        f"confidence-{confidence}",
    ]

    try:
        add_tag_to_ticket(ticket_id, tags)
        log.debug(
            f"Ticket #{ticket_id}: Tagged with {tags}"
        )
    except Exception as e:
        log.warning(
            f"Tagging failed for ticket #{ticket_id}: {e}"
        )


def _build_resolution_message(
    requester_name: str,
    subject       : str,
    action        : str,
    category      : str,
) -> str:
    """
    Build the email/reply message sent to the user when
    their ticket is auto-resolved.

    Args:
        requester_name : Name of the user
        subject        : Ticket subject
        action         : What action was taken
        category       : Ticket category

    Returns:
        Formatted message string
    """
    category_labels = {
        "app_install"    : "software installation",
        "antivirus"      : "antivirus update",
        "password_reset" : "password reset",
        "os_issue"       : "system repair",
        "printer"        : "printer fix",
        "email_issue"    : "email repair",
        "network"        : "network fix",
        "other"          : "issue resolution",
    }

    label = category_labels.get(category, "issue resolution")

    message = (
        f"Dear {requester_name},\n\n"
        f"Your ticket '{subject}' has been automatically "
        f"resolved by our AI support system.\n\n"
        f"Action taken: {action}\n\n"
        f"Your {label} has been completed remotely on your "
        f"machine. Please restart your computer if required "
        f"and verify the issue is resolved.\n\n"
        f"If you are still facing any issues, please raise "
        f"a new ticket and our team will assist you promptly.\n\n"
        f"Resolved by  : AI Auto-Resolver\n"
        f"Resolved at  : {_now()}\n\n"
        f"Thank you,\n"
        f"IT Support Team\n"
        f"{COMPANY_NAME}"
    )

    return message


def _build_kb_message(
    requester_name: str,
    subject       : str,
    guide         : str,
) -> str:
    """
    Build the email/reply message sent to the user when
    a knowledge base guide is found for their issue.

    Args:
        requester_name : Name of the user
        subject        : Ticket subject
        guide          : KB guide content text

    Returns:
        Formatted message string
    """
    message = (
        f"Dear {requester_name},\n\n"
        f"Thank you for raising a ticket regarding "
        f"'{subject}'.\n\n"
        f"We found a self-help guide that may resolve "
        f"your issue:\n\n"
        f"{'─' * 50}\n"
        f"{guide}\n"
        f"{'─' * 50}\n\n"
        f"Please follow the steps above and let us know "
        f"if this resolves the issue.\n\n"
        f"If the problem persists, an engineer will follow "
        f"up with you shortly.\n\n"
        f"Thank you,\n"
        f"IT Support Team\n"
        f"{COMPANY_NAME}"
    )

    return message


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
    print("ORCHESTRATOR TEST RUN")
    print("=" * 60)
    print(
        f"  Mode         : "
        f"{'DEMO' if DEMO_MODE else 'LIVE'}"
    )
    print(
        f"  Dry run      : "
        f"{'YES' if DRY_RUN_MODE else 'NO'}"
    )
    print(f"  KB search    : {FEATURE_KB_SEARCH}")
    print(f"  Company      : {COMPANY_NAME}")
    print(f"  Agent ID     : {ESCALATION_AGENT_ID or 'not set'}")
    print()

    test_cases = [
        {
            "label"          : "Auto-resolvable — App Install",
            "ticket"         : {
                "id"              : 1001,
                "subject"         : "Install Zoom on my laptop",
                "description"     : (
                    "I need Zoom installed on PC-ICICI-0042 urgently. "
                    "Client call in 2 hours."
                ),
                "requester_email" : "rahul.sharma@icici.com",
                "requester_name"  : "Rahul Sharma",
                "machine_name"    : "PC-ICICI-0042",
                "mentioned_apps"  : ["zoom"],
                "urgency_level"   : "high",
            },
            "classification" : {
                "category"        : "app_install",
                "priority"        : "high",
                "can_auto_resolve": True,
                "suggested_action": "Push Zoom installation via SCCM.",
                "confidence"      : "high",
            },
        },
        {
            "label"          : "Non-auto — Hardware Issue",
            "ticket"         : {
                "id"              : 1002,
                "subject"         : "Laptop screen is flickering",
                "description"     : (
                    "My laptop screen has been flickering since morning. "
                    "I think it might be physical damage."
                ),
                "requester_email" : "priya.mehta@icici.com",
                "requester_name"  : "Priya Mehta",
                "machine_name"    : "LAPTOP-ICICI-115",
                "mentioned_apps"  : [],
                "urgency_level"   : "medium",
            },
            "classification" : {
                "category"        : "hardware",
                "priority"        : "medium",
                "can_auto_resolve": False,
                "suggested_action": "Schedule on-site hardware inspection.",
                "confidence"      : "high",
            },
        },
        {
            "label"          : "Non-auto — VPN (KB guide expected)",
            "ticket"         : {
                "id"              : 1003,
                "subject"         : "Cannot connect to VPN from home",
                "description"     : (
                    "I cannot connect to VPN. Cisco AnyConnect shows "
                    "connection timed out. Please help."
                ),
                "requester_email" : "amit.patel@icici.com",
                "requester_name"  : "Amit Patel",
                "machine_name"    : "LAPTOP-ICICI-088",
                "mentioned_apps"  : ["anyconnect"],
                "urgency_level"   : "high",
            },
            "classification" : {
                "category"        : "network",
                "priority"        : "high",
                "can_auto_resolve": False,
                "suggested_action": "Check VPN config and escalate.",
                "confidence"      : "high",
            },
        },
        {
            "label"          : "Validation fail — Missing email",
            "ticket"         : {
                "id"              : 1004,
                "subject"         : "Cannot print documents",
                "description"     : "Printer is showing offline.",
                "requester_email" : "",
                "requester_name"  : "Unknown",
                "machine_name"    : "PC-ICICI-0099",
                "mentioned_apps"  : [],
                "urgency_level"   : "low",
            },
            "classification" : {
                "category"        : "printer",
                "priority"        : "low",
                "can_auto_resolve": True,
                "suggested_action": "Restart print spooler remotely.",
                "confidence"      : "medium",
            },
        },
    ]

    resolved_count  = 0
    escalated_count = 0

    for tc in test_cases:
        print(f"\n--- Test: {tc['label']} ---")
        print(
            f"  Ticket  : "
            f"#{tc['ticket']['id']} — {tc['ticket']['subject']}"
        )
        print(
            f"  Category: "
            f"{tc['classification']['category']}"
        )
        print(
            f"  Auto    : "
            f"{tc['classification']['can_auto_resolve']}"
        )

        result = orchestrate(tc["ticket"], tc["classification"])

        outcome = "RESOLVED ✓" if result else "ESCALATED →"
        print(f"  Result  : {outcome}")
        print("-" * 55)

        if result:
            resolved_count += 1
        else:
            escalated_count += 1

    print(f"\n{'=' * 60}")
    print("ORCHESTRATOR TEST SUMMARY")
    print(f"{'=' * 60}")
    total = len(test_cases)
    print(f"  Total    : {total}")
    print(f"  Resolved : {resolved_count}")
    print(f"  Escalated: {escalated_count}")
    rate = round(resolved_count / total * 100, 1)
    print(f"  Rate     : {rate}%")
    print(f"{'=' * 60}\n")