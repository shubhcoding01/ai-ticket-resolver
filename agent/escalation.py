import os
import logging
from datetime   import datetime
from dotenv     import load_dotenv

from ingestion.freshdesk_client import (
    update_ticket_status,
    add_internal_note,
    assign_ticket_to_agent,
    add_tag_to_ticket,
    set_ticket_priority,
    add_public_reply,
)
from agent.notifier import notify_engineer

load_dotenv()

log = logging.getLogger(__name__)

ESCALATION_AGENT_ID    = int(os.getenv("ESCALATION_AGENT_ID",    0))
ESCALATION_GROUP_ID    = int(os.getenv("ESCALATION_GROUP_ID",    0))
ENGINEER_EMAIL         = os.getenv("ENGINEER_EMAIL",         "")
COMPANY_NAME           = os.getenv("COMPANY_NAME",           "ICICI Bank")


def escalate_ticket(
    ticket_id : int,
    note      : str,
    agent_id  : int = None,
) -> bool:
    """
    Escalate a ticket to the engineer queue.
    Updates status to pending, adds internal note,
    assigns to escalation agent if configured.

    Args:
        ticket_id : Freshdesk ticket ID
        note      : Reason for escalation
        agent_id  : Optional specific agent ID to assign to

    Returns:
        True if escalation succeeded, False otherwise
    """
    log.info(f"Escalating ticket #{ticket_id}...")

    status_ok = update_ticket_status(ticket_id, "pending")

    if not status_ok:
        log.error(f"Failed to update status for ticket #{ticket_id}")
        return False

    timestamp  = datetime.utcnow().strftime("%d %b %Y %I:%M %p UTC")
    full_note  = (
        f"[AI ESCALATION — {timestamp}]\n"
        f"{'─'*40}\n"
        f"{note}\n"
        f"{'─'*40}\n"
        f"This ticket was processed by the AI Ticket Resolver system\n"
        f"and requires manual engineer review."
    )

    add_internal_note(ticket_id, full_note)

    target_agent = agent_id or ESCALATION_AGENT_ID
    if target_agent:
        assigned = assign_ticket_to_agent(ticket_id, target_agent)
        if assigned:
            log.info(f"Ticket #{ticket_id} assigned to agent #{target_agent}.")
        else:
            log.warning(f"Could not assign ticket #{ticket_id} to agent #{target_agent}.")

    add_tag_to_ticket(ticket_id, ["ai-escalated", "needs-engineer"])

    log.info(f"Ticket #{ticket_id} escalated successfully.")
    return True


def escalate_with_full_details(
    ticket        : dict,
    classification: dict,
    reason        : str,
) -> bool:
    """
    Full escalation with engineer email notification.
    Sends a detailed email to the engineer with AI summary,
    ticket details, requester info, and suggested action.

    Args:
        ticket         : Parsed ticket dict from ticket_parser.py
        classification : Classification dict from ai_classifier.py
        reason         : Why this ticket is being escalated

    Returns:
        True if escalation and notification succeeded
    """
    ticket_id        = ticket.get("id", 0)
    subject          = ticket.get("subject", "")
    requester_name   = ticket.get("requester_name", "Unknown")
    requester_email  = ticket.get("requester_email", "")
    machine_name     = ticket.get("machine_name", "UNKNOWN")
    description      = ticket.get("description", "")
    category         = classification.get("category", "other")
    priority         = classification.get("priority", "medium")
    suggested_action = classification.get("suggested_action", "Manual review required.")
    confidence       = classification.get("confidence", "low")

    log.info(f"Full escalation for ticket #{ticket_id}...")

    basic_ok = escalate_ticket(
        ticket_id = ticket_id,
        note      = reason,
    )

    if ENGINEER_EMAIL:
        ai_summary = _build_ai_summary(
            description      = description,
            category         = category,
            confidence       = confidence,
            reason           = reason,
            suggested_action = suggested_action,
        )

        notify_engineer(
            engineer_email   = ENGINEER_EMAIL,
            ticket_id        = ticket_id,
            subject          = subject,
            category         = category,
            priority         = priority,
            ai_summary       = ai_summary,
            requester_name   = requester_name,
            requester_email  = requester_email,
            machine_name     = machine_name,
            suggested_action = suggested_action,
        )
    else:
        log.warning(
            "ENGINEER_EMAIL not set in .env — "
            "engineer notification email not sent."
        )

    return basic_ok


def escalate_high_priority(
    ticket        : dict,
    classification: dict,
) -> bool:
    """
    Special escalation path for HIGH and URGENT priority tickets.
    Sets priority in Freshdesk to urgent, adds urgent tag,
    and notifies engineer immediately.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification dict

    Returns:
        True if escalation succeeded
    """
    ticket_id = ticket.get("id", 0)
    priority  = classification.get("priority", "medium")

    log.warning(
        f"HIGH PRIORITY escalation for ticket #{ticket_id} "
        f"(priority: {priority})"
    )

    if priority in ["high", "urgent"]:
        set_ticket_priority(ticket_id, "urgent")
        add_tag_to_ticket(ticket_id, ["urgent", "high-priority", "immediate-action"])

    reason = (
        f"HIGH PRIORITY TICKET — Immediate action required.\n"
        f"Priority : {priority.upper()}\n"
        f"Category : {classification.get('category', 'other')}\n"
        f"Action   : {classification.get('suggested_action', '')}"
    )

    return escalate_with_full_details(
        ticket         = ticket,
        classification = classification,
        reason         = reason,
    )


def escalate_after_business_hours(ticket: dict, classification: dict) -> bool:
    """
    Escalation for tickets raised outside business hours.
    Adds a note that ticket will be reviewed next business day
    and sends user an acknowledgement.

    Args:
        ticket         : Parsed ticket dict
        classification : Classification dict

    Returns:
        True if escalation succeeded
    """
    ticket_id      = ticket.get("id", 0)
    requester_email = ticket.get("requester_email", "")
    requester_name  = ticket.get("requester_name", "User")
    subject         = ticket.get("subject", "")

    log.info(f"After-hours escalation for ticket #{ticket_id}.")

    reason = (
        "Ticket received outside business hours (9AM–6PM IST).\n"
        "Will be reviewed by engineer on next business day.\n"
        f"Category : {classification.get('category', 'other')}\n"
        f"Suggested: {classification.get('suggested_action', '')}"
    )

    escalate_ticket(ticket_id=ticket_id, note=reason)

    add_tag_to_ticket(ticket_id, ["after-hours", "next-business-day"])

    if requester_email:
        from agent.notifier import notify_user
        notify_user(
            email      = requester_email,
            ticket_id  = ticket_id,
            subject    = subject,
            message    = (
                f"Dear {requester_name},\n\n"
                f"Thank you for raising a support ticket.\n\n"
                f"Your ticket #{ticket_id} has been received outside "
                f"our business hours (9AM – 6PM IST, Monday to Friday).\n\n"
                f"Our support team will review and respond to your ticket "
                f"on the next business day.\n\n"
                f"If this is an emergency, please call the IT helpdesk:\n"
                f"Phone: 1800-XXX-XXXX\n\n"
                f"Thank you for your patience.\n\n"
                f"IT Support Team\n{COMPANY_NAME}"
            ),
            notif_type = "escalated",
        )

    return True


def _build_ai_summary(
    description     : str,
    category        : str,
    confidence      : str,
    reason          : str,
    suggested_action: str,
) -> str:
    """
    Build a clear AI analysis summary for the engineer email.

    Args:
        description      : Original ticket description
        category         : Classified category
        confidence       : Classifier confidence level
        reason           : Why ticket was escalated
        suggested_action : What AI recommends

    Returns:
        Formatted summary string
    """
    short_desc = description[:300] + "..." if len(description) > 300 else description

    summary = (
        f"AI CLASSIFICATION SUMMARY\n"
        f"{'─'*40}\n"
        f"Category         : {category.replace('_', ' ').title()}\n"
        f"Confidence       : {confidence.upper()}\n"
        f"Suggested Action : {suggested_action}\n\n"
        f"ESCALATION REASON\n"
        f"{'─'*40}\n"
        f"{reason}\n\n"
        f"ORIGINAL TICKET DESCRIPTION\n"
        f"{'─'*40}\n"
        f"{short_desc}"
    )

    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("ESCALATION MODULE TEST")
    print("=" * 60 + "\n")

    sample_ticket = {
        "id"              : 2001,
        "subject"         : "Laptop screen flickering badly",
        "description"     : "My laptop screen has been flickering since morning. Cannot work.",
        "requester_name"  : "Rahul Sharma",
        "requester_email" : "rahul.sharma@icici.com",
        "machine_name"    : "LAPTOP-ICICI-115",
    }

    sample_classification = {
        "category"        : "hardware",
        "priority"        : "high",
        "can_auto_resolve": False,
        "suggested_action": "Schedule on-site hardware inspection.",
        "confidence"      : "high",
    }

    print("Testing basic escalation...")
    result = escalate_ticket(
        ticket_id = sample_ticket["id"],
        note      = "Hardware issue — cannot be auto-resolved. Needs on-site engineer."
    )
    print(f"Result: {'SUCCESS' if result else 'FAILED'}\n")

    print("Testing full escalation with engineer notification...")
    result = escalate_with_full_details(
        ticket         = sample_ticket,
        classification = sample_classification,
        reason         = "Hardware issue — physical inspection required.",
    )
    print(f"Result: {'SUCCESS' if result else 'FAILED'}")