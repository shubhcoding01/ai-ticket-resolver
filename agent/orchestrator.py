import os
import logging
from dotenv import load_dotenv

from automation.runner import run_automation
from knowledge_base.kb_search import search_knowledge_base
from agent.escalation import escalate_ticket
from agent.notifier import notify_user
from database.db_logger import log_ticket_action
from ingestion.freshdesk_client import (
    close_ticket,
    update_ticket_status,
    add_internal_note,
    add_public_reply,
    add_tag_to_ticket,
    set_ticket_priority,
)

load_dotenv()

log = logging.getLogger(__name__)

ESCALATION_AGENT_ID = int(os.getenv("ESCALATION_AGENT_ID", 0))


def orchestrate(ticket: dict, classification: dict) -> bool:
    """
    Main orchestrator function called by main.py for every ticket.
    Decides the full resolution path and executes it end to end.

    Decision flow:
        1. Validate ticket has minimum required data
        2. Update Freshdesk priority based on AI classification
        3. If can_auto_resolve → try automation
           a. Automation success  → close ticket + notify user
           b. Automation fail     → search KB → send guide or escalate
        4. If cannot auto_resolve → search KB → send guide + escalate
        5. Log everything to database

    Args:
        ticket         : Clean parsed ticket dict from ticket_parser.py
        classification : Classification dict from ai_classifier.py

    Returns:
        True if ticket was fully resolved automatically
        False if ticket was escalated or resolution failed
    """
    ticket_id    = ticket.get("id", 0)
    subject      = ticket.get("subject", "No subject")
    requester    = ticket.get("requester_email", "")
    requester_name = ticket.get("requester_name", "User")
    machine      = ticket.get("machine_name", "UNKNOWN")
    category     = classification.get("category", "other")
    priority     = classification.get("priority", "medium")
    can_auto     = classification.get("can_auto_resolve", False)
    action       = classification.get("suggested_action", "Manual review required.")
    confidence   = classification.get("confidence", "low")

    log.info(f"")
    log.info(f"{'='*55}")
    log.info(f"ORCHESTRATING TICKET #{ticket_id}")
    log.info(f"  Subject    : {subject}")
    log.info(f"  Category   : {category}")
    log.info(f"  Priority   : {priority}")
    log.info(f"  Auto       : {can_auto}")
    log.info(f"  Machine    : {machine}")
    log.info(f"  Confidence : {confidence}")
    log.info(f"{'='*55}")

    if not _validate_ticket(ticket):
        log.error(f"Ticket #{ticket_id} failed validation. Escalating.")
        _handle_escalation(
            ticket=ticket,
            classification=classification,
            reason="Ticket data incomplete — needs manual review.",
            tag="validation-failed"
        )
        return False

    _sync_priority_to_freshdesk(ticket_id, priority)
    _tag_ticket(ticket_id, category, confidence)

    if can_auto:
        return _handle_auto_resolve(ticket, classification)
    else:
        return _handle_manual_escalation(ticket, classification)


def _handle_auto_resolve(ticket: dict, classification: dict) -> bool:
    """
    Attempt to auto-resolve the ticket using automation scripts.
    If automation succeeds → close ticket and notify user.
    If automation fails   → search KB and escalate.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        True if resolved, False if escalated
    """
    ticket_id      = ticket.get("id")
    subject        = ticket.get("subject", "")
    requester      = ticket.get("requester_email", "")
    requester_name = ticket.get("requester_name", "User")
    category       = classification.get("category", "other")
    action         = classification.get("suggested_action", "")

    log.info(f"Ticket #{ticket_id}: Attempting auto-resolution...")

    add_internal_note(
        ticket_id,
        f"[AI Orchestrator] Auto-resolution started.\n"
        f"Category : {category}\n"
        f"Action   : {action}\n"
        f"Machine  : {ticket.get('machine_name', 'UNKNOWN')}"
    )

    success = run_automation(ticket, classification)

    if success:
        log.info(f"Ticket #{ticket_id}: Auto-resolution SUCCEEDED.")

        resolution_message = _build_resolution_message(
            requester_name=requester_name,
            subject=subject,
            action=action,
            category=category,
        )

        close_ticket(ticket_id, action)

        notify_user(
            email=requester,
            ticket_id=ticket_id,
            subject=subject,
            message=resolution_message,
        )

        add_public_reply(ticket_id, resolution_message)

        log_ticket_action(
            ticket_id=ticket_id,
            category=category,
            priority=classification.get("priority", "medium"),
            action_taken=action,
            resolved_by="AI_AUTO",
            status="RESOLVED",
        )

        log.info(f"Ticket #{ticket_id}: Closed and user notified.")
        return True

    else:
        log.warning(
            f"Ticket #{ticket_id}: Auto-resolution FAILED. "
            "Searching knowledge base..."
        )

        add_internal_note(
            ticket_id,
            f"[AI Orchestrator] Auto-resolution failed.\n"
            f"Searching knowledge base for: {subject}"
        )

        kb_guide = search_knowledge_base(ticket.get("description", ""))

        if kb_guide:
            log.info(f"Ticket #{ticket_id}: KB guide found. Sending to user.")

            kb_message = _build_kb_message(
                requester_name=requester_name,
                subject=subject,
                guide=kb_guide,
            )

            add_public_reply(ticket_id, kb_message)

            notify_user(
                email=requester,
                ticket_id=ticket_id,
                subject=subject,
                message=kb_message,
            )

            _handle_escalation(
                ticket=ticket,
                classification=classification,
                reason=(
                    f"Auto-resolution failed. KB guide sent to user.\n"
                    f"Engineer please verify fix was applied.\n"
                    f"Suggested: {action}"
                ),
                tag="auto-failed-kb-sent"
            )

            log_ticket_action(
                ticket_id=ticket_id,
                category=category,
                priority=classification.get("priority", "medium"),
                action_taken="Auto-resolve failed. KB guide sent.",
                resolved_by="KB+ESCALATION",
                status="ESCALATED",
            )

        else:
            log.warning(
                f"Ticket #{ticket_id}: No KB guide found. "
                "Escalating directly."
            )

            _handle_escalation(
                ticket=ticket,
                classification=classification,
                reason=(
                    f"Auto-resolution failed. No KB guide found.\n"
                    f"Suggested action: {action}"
                ),
                tag="auto-failed-no-kb"
            )

            log_ticket_action(
                ticket_id=ticket_id,
                category=category,
                priority=classification.get("priority", "medium"),
                action_taken="Auto-resolve failed. Escalated.",
                resolved_by="ESCALATION",
                status="ESCALATED",
            )

        return False


def _handle_manual_escalation(ticket: dict, classification: dict) -> bool:
    """
    Handle tickets that cannot be auto-resolved.
    Searches KB first to send self-help guide, then escalates to engineer.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict

    Returns:
        Always returns False (ticket not auto-resolved)
    """
    ticket_id      = ticket.get("id")
    subject        = ticket.get("subject", "")
    requester      = ticket.get("requester_email", "")
    requester_name = ticket.get("requester_name", "User")
    category       = classification.get("category", "other")
    action         = classification.get("suggested_action", "")

    log.info(
        f"Ticket #{ticket_id}: Cannot auto-resolve. "
        "Searching KB before escalating..."
    )

    kb_guide = search_knowledge_base(ticket.get("description", ""))

    if kb_guide:
        log.info(f"Ticket #{ticket_id}: KB guide found. Sending to user.")

        kb_message = _build_kb_message(
            requester_name=requester_name,
            subject=subject,
            guide=kb_guide,
        )

        add_public_reply(ticket_id, kb_message)

        notify_user(
            email=requester,
            ticket_id=ticket_id,
            subject=subject,
            message=kb_message,
        )

        escalation_note = (
            f"KB self-help guide sent to user.\n"
            f"If guide does not resolve — engineer review needed.\n"
            f"Category : {category}\n"
            f"Suggested: {action}"
        )

    else:
        log.info(f"Ticket #{ticket_id}: No KB guide. Escalating directly.")

        escalation_note = (
            f"No KB guide available for this issue.\n"
            f"Category : {category}\n"
            f"Suggested: {action}"
        )

    _handle_escalation(
        ticket=ticket,
        classification=classification,
        reason=escalation_note,
        tag="manual-escalation"
    )

    log_ticket_action(
        ticket_id=ticket_id,
        category=category,
        priority=classification.get("priority", "medium"),
        action_taken=f"KB guide sent + escalated. {action}",
        resolved_by="ENGINEER_QUEUE",
        status="ESCALATED",
    )

    return False


def _handle_escalation(
    ticket        : dict,
    classification: dict,
    reason        : str,
    tag           : str = "escalated"
) -> None:
    """
    Escalate a ticket to the engineer queue.
    Updates status to pending, adds internal note,
    assigns to escalation agent, and tags the ticket.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification result dict
        reason         : Text explaining why escalation happened
        tag            : Tag string to add to the ticket
    """
    ticket_id = ticket.get("id")
    category  = classification.get("category", "other")
    priority  = classification.get("priority", "medium")
    action    = classification.get("suggested_action", "")

    escalate_ticket(
        ticket_id=ticket_id,
        note=reason,
        agent_id=ESCALATION_AGENT_ID if ESCALATION_AGENT_ID else None,
    )

    add_tag_to_ticket(ticket_id, [tag, f"cat-{category}", "ai-processed"])

    log.info(f"Ticket #{ticket_id}: Escalated — {reason[:80]}")


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
        log.error("Ticket has no ID.")
        return False

    if not ticket.get("subject", "").strip():
        log.warning(f"Ticket #{ticket_id} has no subject.")

    if not ticket.get("description", "").strip():
        log.warning(f"Ticket #{ticket_id} has no description.")

    if not ticket.get("requester_email", "").strip():
        log.error(f"Ticket #{ticket_id} has no requester email. Cannot notify user.")
        return False

    return True


def _sync_priority_to_freshdesk(ticket_id: int, ai_priority: str) -> None:
    """
    Update the Freshdesk ticket priority to match what the AI classified.
    This ensures engineers see the correct priority in Freshdesk dashboard.

    Args:
        ticket_id   : Freshdesk ticket ID
        ai_priority : Priority string from classifier — low/medium/high/urgent
    """
    priority_map = {
        "low"    : "low",
        "medium" : "medium",
        "high"   : "high",
        "urgent" : "urgent",
    }

    fd_priority = priority_map.get(ai_priority, "medium")
    set_ticket_priority(ticket_id, fd_priority)
    log.info(f"Ticket #{ticket_id}: Priority set to '{fd_priority}' in Freshdesk.")


def _tag_ticket(ticket_id: int, category: str, confidence: str) -> None:
    """
    Add AI-generated tags to the ticket in Freshdesk.
    Tags help with filtering, reporting, and searching.

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
    add_tag_to_ticket(ticket_id, tags)
    log.debug(f"Ticket #{ticket_id}: Tagged with {tags}")


def _build_resolution_message(
    requester_name: str,
    subject       : str,
    action        : str,
    category      : str,
) -> str:
    """
    Build the email/reply message sent to the user
    when their ticket is auto-resolved.

    Args:
        requester_name : Name of the user
        subject        : Ticket subject
        action         : What action was taken
        category       : Ticket category

    Returns:
        Formatted message string
    """
    category_labels = {
        "app_install"       : "software installation",
        "antivirus"         : "antivirus update",
        "password_reset"    : "password reset",
        "os_issue"          : "system repair",
        "printer"           : "printer fix",
        "email_issue"       : "email repair",
        "network"           : "network fix",
    }

    label = category_labels.get(category, "issue resolution")

    message = (
        f"Dear {requester_name},\n\n"
        f"Your ticket '{subject}' has been automatically resolved "
        f"by our AI support system.\n\n"
        f"Action taken: {action}\n\n"
        f"Your {label} has been completed remotely on your machine. "
        f"Please restart your computer if required and verify the issue is resolved.\n\n"
        f"If you are still facing any issues, please raise a new ticket "
        f"and our team will assist you promptly.\n\n"
        f"Ticket ID    : #{subject}\n"
        f"Resolved by  : AI Auto-Resolver\n\n"
        f"Thank you,\n"
        f"IT Support Team\n"
        f"ICICI Bank"
    )

    return message


def _build_kb_message(
    requester_name: str,
    subject       : str,
    guide         : str,
) -> str:
    """
    Build the email/reply message sent to the user
    when a knowledge base guide is found for their issue.

    Args:
        requester_name : Name of the user
        subject        : Ticket subject
        guide          : KB guide content text

    Returns:
        Formatted message string
    """
    message = (
        f"Dear {requester_name},\n\n"
        f"Thank you for raising a ticket regarding '{subject}'.\n\n"
        f"We found a self-help guide that may resolve your issue:\n\n"
        f"{'─'*50}\n"
        f"{guide}\n"
        f"{'─'*50}\n\n"
        f"Please follow the steps above and let us know if this resolves the issue.\n\n"
        f"If the problem persists, an engineer from our team will follow up "
        f"with you shortly.\n\n"
        f"Thank you,\n"
        f"IT Support Team\n"
        f"ICICI Bank"
    )

    return message


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("ORCHESTRATOR TEST RUN")
    print("=" * 60 + "\n")

    test_cases = [
        {
            "label": "Auto-resolvable — App Install",
            "ticket": {
                "id"              : 1001,
                "subject"         : "Install Zoom on my laptop",
                "description"     : "I need Zoom installed on PC-ICICI-0042 urgently.",
                "requester_email" : "rahul.sharma@icici.com",
                "requester_name"  : "Rahul Sharma",
                "machine_name"    : "PC-ICICI-0042",
                "mentioned_apps"  : ["zoom"],
                "urgency_level"   : "high",
            },
            "classification": {
                "category"        : "app_install",
                "priority"        : "high",
                "can_auto_resolve": True,
                "suggested_action": "Push Zoom installation via SCCM.",
                "confidence"      : "high",
            },
        },
        {
            "label": "Non-auto-resolvable — Hardware Issue",
            "ticket": {
                "id"              : 1002,
                "subject"         : "Laptop screen is flickering",
                "description"     : "My laptop screen has been flickering since morning.",
                "requester_email" : "priya.mehta@icici.com",
                "requester_name"  : "Priya Mehta",
                "machine_name"    : "LAPTOP-ICICI-115",
                "mentioned_apps"  : [],
                "urgency_level"   : "medium",
            },
            "classification": {
                "category"        : "hardware",
                "priority"        : "medium",
                "can_auto_resolve": False,
                "suggested_action": "Schedule on-site hardware inspection.",
                "confidence"      : "high",
            },
        },
        {
            "label": "Missing email — Validation fail",
            "ticket": {
                "id"              : 1003,
                "subject"         : "Cannot print documents",
                "description"     : "Printer is showing offline.",
                "requester_email" : "",
                "requester_name"  : "Unknown",
                "machine_name"    : "PC-ICICI-0099",
                "mentioned_apps"  : [],
                "urgency_level"   : "low",
            },
            "classification": {
                "category"        : "printer",
                "priority"        : "low",
                "can_auto_resolve": True,
                "suggested_action": "Restart print spooler remotely.",
                "confidence"      : "medium",
            },
        },
    ]

    for tc in test_cases:
        print(f"\nTest: {tc['label']}")
        print(f"  Ticket  : #{tc['ticket']['id']} — {tc['ticket']['subject']}")
        print(f"  Category: {tc['classification']['category']}")
        print(f"  Auto    : {tc['classification']['can_auto_resolve']}")

        result = orchestrate(tc["ticket"], tc["classification"])

        print(f"  Result  : {'RESOLVED' if result else 'ESCALATED/FAILED'}")
        print("-" * 55)