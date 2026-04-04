import schedule
import time
import logging
from dotenv import load_dotenv
import os

from ingestion.freshdesk_client import fetch_new_tickets, update_ticket_status, close_ticket
from ingestion.ticket_parser import parse_ticket
from classifier.ai_classifier import classify_ticket
from knowledge_base.kb_search import search_knowledge_base
from automation.runner import run_automation
from agent.orchestrator import orchestrate
from agent.notifier import notify_user
from agent.escalation import escalate_ticket
from database.db_logger import log_ticket_action
from database.db_setup import initialize_database

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("ticket_resolver.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", 5))


def process_tickets():
    log.info("========== Polling for new tickets ==========")

    try:
        raw_tickets = fetch_new_tickets()
    except Exception as e:
        log.error(f"Failed to fetch tickets from Freshdesk: {e}")
        return

    if not raw_tickets:
        log.info("No new tickets found.")
        return

    log.info(f"Found {len(raw_tickets)} new ticket(s). Processing...")

    for raw in raw_tickets:
        ticket = parse_ticket(raw)
        ticket_id   = ticket["id"]
        subject     = ticket["subject"]
        description = ticket["description"]
        requester   = ticket["requester_email"]
        machine     = ticket.get("machine_name", "UNKNOWN")

        log.info(f"--- Ticket #{ticket_id}: {subject} ---")

        try:
            classification = classify_ticket(subject, description)
        except Exception as e:
            log.error(f"Classifier failed for ticket #{ticket_id}: {e}")
            escalate_ticket(ticket_id, "Classifier error — needs manual review.")
            continue

        category        = classification["category"]
        priority        = classification["priority"]
        can_auto        = classification["can_auto_resolve"]
        suggested_action = classification["suggested_action"]

        log.info(f"  Category : {category}")
        log.info(f"  Priority : {priority}")
        log.info(f"  Auto-resolve: {can_auto}")
        log.info(f"  Suggested action: {suggested_action}")

        if can_auto:
            log.info(f"  Attempting auto-resolution for ticket #{ticket_id}...")
            success = orchestrate(ticket, classification)

            if success:
                close_ticket(ticket_id, f"Auto-resolved: {suggested_action}")
                notify_user(
                    email=requester,
                    ticket_id=ticket_id,
                    subject=subject,
                    message=f"Your ticket has been automatically resolved.\n\nAction taken: {suggested_action}\n\nIf the issue persists, please raise a new ticket."
                )
                log.info(f"  Ticket #{ticket_id} auto-resolved and closed.")
                log_ticket_action(
                    ticket_id=ticket_id,
                    category=category,
                    priority=priority,
                    action_taken=suggested_action,
                    resolved_by="AI_AUTO",
                    status="RESOLVED"
                )

            else:
                log.warning(f"  Auto-resolution failed for ticket #{ticket_id}. Checking knowledge base...")
                kb_guide = search_knowledge_base(description)

                if kb_guide:
                    notify_user(
                        email=requester,
                        ticket_id=ticket_id,
                        subject=subject,
                        message=f"We found a self-help guide for your issue:\n\n{kb_guide}\n\nIf this does not help, an engineer will follow up."
                    )
                    escalate_ticket(ticket_id, f"Auto-resolve failed. KB guide sent. Needs engineer review.\nSuggested: {suggested_action}")
                    log.info(f"  KB guide sent. Ticket #{ticket_id} escalated.")
                    log_ticket_action(
                        ticket_id=ticket_id,
                        category=category,
                        priority=priority,
                        action_taken="KB guide sent + escalated",
                        resolved_by="KB+ESCALATION",
                        status="ESCALATED"
                    )
                else:
                    escalate_ticket(ticket_id, f"Auto-resolve failed. No KB guide found.\nSuggested: {suggested_action}")
                    log.info(f"  Ticket #{ticket_id} escalated to engineer.")
                    log_ticket_action(
                        ticket_id=ticket_id,
                        category=category,
                        priority=priority,
                        action_taken="Escalated — no KB match",
                        resolved_by="ESCALATION",
                        status="ESCALATED"
                    )

        else:
            log.info(f"  Ticket #{ticket_id} marked as complex. Searching knowledge base...")
            kb_guide = search_knowledge_base(description)

            if kb_guide:
                notify_user(
                    email=requester,
                    ticket_id=ticket_id,
                    subject=subject,
                    message=f"Here is a self-help guide that may resolve your issue:\n\n{kb_guide}\n\nAn engineer will also follow up shortly."
                )
                log.info(f"  KB guide sent to {requester}.")

            escalate_ticket(ticket_id, f"Requires engineer. AI suggestion: {suggested_action}")
            log.info(f"  Ticket #{ticket_id} escalated to engineer queue.")
            log_ticket_action(
                ticket_id=ticket_id,
                category=category,
                priority=priority,
                action_taken=f"Escalated — {suggested_action}",
                resolved_by="ENGINEER_QUEUE",
                status="ESCALATED"
            )

    log.info("========== Polling cycle complete ==========\n")


def main():
    log.info("AI Ticket Resolver starting up...")
    log.info(f"Poll interval: every {POLL_INTERVAL_MINUTES} minute(s)")

    initialize_database()
    log.info("Database initialized.")

    process_tickets()

    schedule.every(POLL_INTERVAL_MINUTES).minutes.do(process_tickets)

    log.info("Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()