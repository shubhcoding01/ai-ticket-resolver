# import os
# import sys
# import time
# import random
# import logging
# import sqlite3
# from datetime import datetime, timezone
# from pathlib  import Path

# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# from dotenv import load_dotenv
# load_dotenv("config/.env")

# from config.settings  import setup_logging, COMPANY_NAME
# from database.db_setup import initialize_database
# from database.db_logger import (
#     log_ticket_action,
#     log_classification,
#     log_automation,
#     log_notification,
#     get_resolution_stats,
#     get_all_ticket_logs,
#     get_daily_stats,
# )
# from knowledge_base.kb_indexer import (
#     create_sample_docs,
#     build_index,
# )
# from knowledge_base.kb_search import (
#     search_knowledge_base,
#     is_kb_available,
# )
# from classifier.category_rules import classify_by_rules

# setup_logging()
# log = logging.getLogger(__name__)


# DEMO_TICKETS = [
#     {
#         "id"              : 1001,
#         "subject"         : "Please install Zoom on my laptop urgently",
#         "description"     : (
#             "Hi team, I need Zoom installed on my machine PC-ICICI-0042. "
#             "I have a client call in 2 hours and Zoom is not installed. "
#             "Please help asap."
#         ),
#         "requester_name"  : "Rahul Sharma",
#         "requester_email" : "rahul.sharma@icici.com",
#         "machine_name"    : "PC-ICICI-0042",
#         "mentioned_apps"  : ["zoom"],
#         "urgency_level"   : "high",
#     },
#     {
#         "id"              : 1002,
#         "subject"         : "Antivirus showing red warning — definitions out of date",
#         "description"     : (
#             "My Symantec antivirus is showing a red warning. "
#             "The virus definitions are out of date. "
#             "I tried updating manually but it fails every time. "
#             "My machine is LAPTOP-ICICI-115."
#         ),
#         "requester_name"  : "Priya Mehta",
#         "requester_email" : "priya.mehta@icici.com",
#         "machine_name"    : "LAPTOP-ICICI-115",
#         "mentioned_apps"  : ["symantec"],
#         "urgency_level"   : "medium",
#     },
#     {
#         "id"              : 1003,
#         "subject"         : "Cannot login — account locked out",
#         "description"     : (
#             "I forgot my Windows password and now my account is locked. "
#             "I tried 5 times and it says account is locked. "
#             "Please reset my password. I cannot work at all."
#         ),
#         "requester_name"  : "Amit Patel",
#         "requester_email" : "amit.patel@icici.com",
#         "machine_name"    : "PC-ICICI-0099",
#         "mentioned_apps"  : [],
#         "urgency_level"   : "high",
#     },
#     {
#         "id"              : 1004,
#         "subject"         : "Cannot connect to VPN from home",
#         "description"     : (
#             "Since this morning I am unable to connect to VPN. "
#             "Cisco AnyConnect shows connection timed out error. "
#             "My colleagues are able to connect fine. "
#             "I have a critical presentation in 1 hour."
#         ),
#         "requester_name"  : "Sneha Reddy",
#         "requester_email" : "sneha.reddy@icici.com",
#         "machine_name"    : "LAPTOP-ICICI-088",
#         "mentioned_apps"  : ["anyconnect"],
#         "urgency_level"   : "high",
#     },
#     {
#         "id"              : 1005,
#         "subject"         : "Printer offline — cannot print documents",
#         "description"     : (
#             "My printer is showing as offline. "
#             "I cannot print any documents since yesterday. "
#             "The print queue shows jobs stuck. "
#             "Machine: WS-ICICI-201."
#         ),
#         "requester_name"  : "Vikram Singh",
#         "requester_email" : "vikram.singh@icici.com",
#         "machine_name"    : "WS-ICICI-201",
#         "mentioned_apps"  : [],
#         "urgency_level"   : "low",
#     },
#     {
#         "id"              : 1006,
#         "subject"         : "Outlook not opening — PST file error",
#         "description"     : (
#             "Outlook is not opening this morning. "
#             "It shows an error about a corrupt PST file. "
#             "I cannot send or receive any emails. "
#             "This is very urgent as I have client emails pending."
#         ),
#         "requester_name"  : "Deepa Nair",
#         "requester_email" : "deepa.nair@icici.com",
#         "machine_name"    : "PC-ICICI-0055",
#         "mentioned_apps"  : ["outlook"],
#         "urgency_level"   : "high",
#     },
#     {
#         "id"              : 1007,
#         "subject"         : "Laptop screen is flickering badly",
#         "description"     : (
#             "My laptop screen has been flickering continuously since morning. "
#             "Sometimes it goes completely blank for a few seconds. "
#             "I think the display cable or screen might be damaged physically."
#         ),
#         "requester_name"  : "Karan Malhotra",
#         "requester_email" : "karan.malhotra@icici.com",
#         "machine_name"    : "LAPTOP-ICICI-220",
#         "mentioned_apps"  : [],
#         "urgency_level"   : "medium",
#     },
#     {
#         "id"              : 1008,
#         "subject"         : "Windows update failed with error code 0x80070002",
#         "description"     : (
#             "My Windows 10 update has been failing for the last 3 days. "
#             "Error code 0x80070002. I tried running Windows Update "
#             "troubleshooter but it did not fix. "
#             "Machine: PC-ICICI-0077."
#         ),
#         "requester_name"  : "Ananya Krishnan",
#         "requester_email" : "ananya.krishnan@icici.com",
#         "machine_name"    : "PC-ICICI-0077",
#         "mentioned_apps"  : [],
#         "urgency_level"   : "medium",
#     },
#     {
#         "id"              : 1009,
#         "subject"         : "Cannot access shared drive — permission denied",
#         "description"     : (
#             "I am getting permission denied error when trying to open "
#             "the Finance shared drive on the network. "
#             "I had access last week but now it says access denied. "
#             "I need access urgently for month-end reports."
#         ),
#         "requester_name"  : "Rohit Gupta",
#         "requester_email" : "rohit.gupta@icici.com",
#         "machine_name"    : "PC-ICICI-0033",
#         "mentioned_apps"  : [],
#         "urgency_level"   : "high",
#     },
#     {
#         "id"              : 1010,
#         "subject"         : "Need Microsoft Teams installed",
#         "description"     : (
#             "Please install Microsoft Teams on my desktop. "
#             "My manager has asked me to join the team channel. "
#             "Machine name is DESKTOP-ICICI-009."
#         ),
#         "requester_name"  : "Pooja Sharma",
#         "requester_email" : "pooja.sharma@icici.com",
#         "machine_name"    : "DESKTOP-ICICI-009",
#         "mentioned_apps"  : ["microsoft teams"],
#         "urgency_level"   : "medium",
#     },
# ]


# MOCK_AUTOMATION_RESULTS = {
#     "app_install"    : True,
#     "antivirus"      : True,
#     "password_reset" : True,
#     "printer"        : True,
#     "os_issue"       : True,
#     "email_issue"    : True,
#     "network"        : False,
#     "hardware"       : False,
#     "access_permission": False,
#     "other"          : False,
# }


# def _mock_classify(ticket: dict) -> dict:
#     """
#     Classify a ticket using the rule-based classifier.
#     No API key needed — works completely offline.

#     Args:
#         ticket : Demo ticket dict

#     Returns:
#         Classification result dict
#     """
#     result = classify_by_rules(
#         subject     = ticket["subject"],
#         description = ticket["description"],
#     )
#     return result


# def _mock_run_automation(ticket: dict, classification: dict) -> bool:
#     """
#     Simulate running a PowerShell automation script.
#     Returns a realistic success/failure based on category.
#     Adds a small delay to simulate real script execution time.

#     Args:
#         ticket         : Demo ticket dict
#         classification : Classification result dict

#     Returns:
#         True if automation would succeed, False otherwise
#     """
#     category     = classification.get("category", "other")
#     machine_name = ticket.get("machine_name", "UNKNOWN")

#     if machine_name == "UNKNOWN":
#         log.warning("  Cannot run automation — machine name UNKNOWN.")
#         return False

#     time.sleep(random.uniform(0.3, 0.8))

#     success = MOCK_AUTOMATION_RESULTS.get(category, False)

#     script_map = {
#         "app_install"    : "install_app.ps1",
#         "antivirus"      : "update_antivirus.ps1",
#         "password_reset" : "reset_password.ps1",
#         "printer"        : "restart_print_spooler.ps1",
#         "os_issue"       : "clear_disk_space.ps1",
#         "email_issue"    : "repair_outlook.ps1",
#     }

#     script = script_map.get(category, "no_script.ps1")

#     log_automation(
#         ticket_id     = ticket["id"],
#         script_name   = script,
#         machine_name  = machine_name,
#         success       = success,
#         output        = (
#             f"[DEMO] Script {script} executed on {machine_name}. "
#             f"Result: {'SUCCESS' if success else 'FAILED'}"
#         ),
#         duration_secs = random.uniform(5.0, 45.0),
#     )

#     return success


# def _mock_search_kb(description: str) -> str | None:
#     """
#     Search the real KB index if available,
#     otherwise return a demo guide string.

#     Args:
#         description : Ticket description to search

#     Returns:
#         Guide text string or None
#     """
#     if is_kb_available():
#         return search_knowledge_base(description)

#     demo_guides = {
#         "vpn"        : (
#             "VPN Self-Help Guide\n"
#             "1. Open Cisco AnyConnect from Start menu\n"
#             "2. Enter: vpn.icici.com\n"
#             "3. Click Connect and enter your domain credentials\n"
#             "4. If it fails: restart AnyConnect service in Task Manager"
#         ),
#         "password"   : (
#             "Password Reset Guide\n"
#             "1. Go to password.icici.com\n"
#             "2. Click 'Forgot Password'\n"
#             "3. Enter your employee ID\n"
#             "4. OTP will be sent to your registered mobile number"
#         ),
#         "printer"    : (
#             "Printer Troubleshooting Guide\n"
#             "1. Check if printer is powered on\n"
#             "2. Right-click printer → See what's printing\n"
#             "3. Cancel all stuck jobs\n"
#             "4. Restart Print Spooler from Services"
#         ),
#         "outlook"    : (
#             "Outlook Troubleshooting Guide\n"
#             "1. Close Outlook completely\n"
#             "2. Press Win+R → type: outlook.exe /safe\n"
#             "3. If opens in Safe Mode — disable all add-ins\n"
#             "4. Restart Outlook normally"
#         ),
#     }

#     desc_lower = description.lower()
#     for keyword, guide in demo_guides.items():
#         if keyword in desc_lower:
#             return guide

#     return None


# def _mock_notify(
#     ticket        : dict,
#     notification_type: str,
#     message       : str,
# ) -> None:
#     """
#     Simulate sending an email notification.
#     In demo mode we just log it instead of sending a real email.

#     Args:
#         ticket            : Demo ticket dict
#         notification_type : Type of notification
#         message           : Message that would be sent
#     """
#     email = ticket.get("requester_email", "unknown")
#     name  = ticket.get("requester_name",  "User")

#     log.info(
#         f"  [DEMO EMAIL] To: {email} "
#         f"| Type: {notification_type} "
#         f"| Subject: Ticket #{ticket['id']}"
#     )

#     log_notification(
#         ticket_id  = ticket["id"],
#         recipient  = email,
#         notif_type = notification_type,
#         subject    = ticket["subject"],
#         success    = True,
#     )


# def process_demo_ticket(ticket: dict) -> dict:
#     """
#     Process a single demo ticket through the complete
#     AI resolution pipeline.

#     Full flow:
#         1.  Classify using rule-based classifier (no API needed)
#         2.  Check for force-escalation triggers
#         3.  Simulate automation if can_auto_resolve
#         4.  Search KB for self-help guide
#         5.  Log everything to database
#         6.  Return result summary

#     Args:
#         ticket : Demo ticket dict from DEMO_TICKETS list

#     Returns:
#         Dict with processing result and classification
#     """
#     ticket_id = ticket["id"]
#     subject   = ticket["subject"]

#     log.info("")
#     log.info(f"  ┌─ Processing Ticket #{ticket_id}")
#     log.info(f"  │  Subject   : {subject}")
#     log.info(f"  │  Requester : {ticket['requester_name']}")
#     log.info(f"  │  Machine   : {ticket['machine_name']}")

#     classification   = _mock_classify(ticket)
#     category         = classification["category"]
#     priority         = classification["priority"]
#     can_auto         = classification["can_auto_resolve"]
#     suggested_action = classification["suggested_action"]
#     confidence       = classification["confidence"]
#     force_escalate   = classification.get("force_escalate", False)

#     log.info(f"  │  Category  : {category}")
#     log.info(f"  │  Priority  : {priority}")
#     log.info(f"  │  Auto      : {can_auto}")
#     log.info(f"  │  Confidence: {confidence}")

#     log_classification(
#         ticket_id        = ticket_id,
#         subject          = subject,
#         category         = category,
#         priority         = priority,
#         can_auto_resolve = can_auto,
#         suggested_action = suggested_action,
#         confidence       = confidence,
#     )

#     if force_escalate:
#         log.warning(f"  │  FORCE ESCALATION TRIGGERED!")
#         log_ticket_action(
#             ticket_id    = ticket_id,
#             category     = category,
#             priority     = "urgent",
#             action_taken = "Force-escalated — critical keyword detected.",
#             resolved_by  = "FORCE_ESCALATION",
#             status       = "ESCALATED",
#         )
#         log.info(f"  └─ Ticket #{ticket_id} → FORCE ESCALATED")
#         return {
#             "ticket_id" : ticket_id,
#             "status"    : "ESCALATED",
#             "reason"    : "force_escalation",
#             "category"  : category,
#             "priority"  : "urgent",
#         }

#     if can_auto:
#         log.info(f"  │  Running automation simulation...")
#         auto_success = _mock_run_automation(ticket, classification)

#         if auto_success:
#             log.info(f"  │  Automation SUCCESS ✓")
#             _mock_notify(ticket, "resolved", suggested_action)
#             log_ticket_action(
#                 ticket_id    = ticket_id,
#                 category     = category,
#                 priority     = priority,
#                 action_taken = suggested_action,
#                 resolved_by  = "AI_AUTO",
#                 status       = "RESOLVED",
#             )
#             log.info(f"  └─ Ticket #{ticket_id} → RESOLVED ✓")
#             return {
#                 "ticket_id" : ticket_id,
#                 "status"    : "RESOLVED",
#                 "reason"    : "auto_resolved",
#                 "category"  : category,
#                 "priority"  : priority,
#             }

#         else:
#             log.warning(f"  │  Automation FAILED — searching KB...")
#             kb_guide = _mock_search_kb(ticket["description"])

#             if kb_guide:
#                 log.info(f"  │  KB guide found and sent to user.")
#                 _mock_notify(ticket, "kb_guide_sent", kb_guide)
#                 log_ticket_action(
#                     ticket_id    = ticket_id,
#                     category     = category,
#                     priority     = priority,
#                     action_taken = "Auto-resolve failed. KB guide sent.",
#                     resolved_by  = "KB+ESCALATION",
#                     status       = "ESCALATED",
#                 )
#                 log.info(f"  └─ Ticket #{ticket_id} → KB SENT + ESCALATED")
#                 return {
#                     "ticket_id" : ticket_id,
#                     "status"    : "ESCALATED",
#                     "reason"    : "auto_failed_kb_sent",
#                     "category"  : category,
#                     "priority"  : priority,
#                 }

#             else:
#                 log_ticket_action(
#                     ticket_id    = ticket_id,
#                     category     = category,
#                     priority     = priority,
#                     action_taken = "Auto-resolve failed. Escalated.",
#                     resolved_by  = "ESCALATION",
#                     status       = "ESCALATED",
#                 )
#                 log.info(f"  └─ Ticket #{ticket_id} → ESCALATED")
#                 return {
#                     "ticket_id" : ticket_id,
#                     "status"    : "ESCALATED",
#                     "reason"    : "auto_failed_no_kb",
#                     "category"  : category,
#                     "priority"  : priority,
#                 }

#     else:
#         log.info(f"  │  Cannot auto-resolve — searching KB...")
#         kb_guide = _mock_search_kb(ticket["description"])

#         if kb_guide:
#             log.info(f"  │  KB guide found and sent.")
#             _mock_notify(ticket, "kb_guide_sent", kb_guide)
#             resolved_by = "KB+ESCALATION"
#         else:
#             log.info(f"  │  No KB guide found.")
#             resolved_by = "ESCALATION"

#         _mock_notify(ticket, "escalated", suggested_action)
#         log_ticket_action(
#             ticket_id    = ticket_id,
#             category     = category,
#             priority     = priority,
#             action_taken = f"Escalated — {suggested_action}",
#             resolved_by  = resolved_by,
#             status       = "ESCALATED",
#         )
#         log.info(f"  └─ Ticket #{ticket_id} → ESCALATED")
#         return {
#             "ticket_id" : ticket_id,
#             "status"    : "ESCALATED",
#             "reason"    : "manual_escalation",
#             "category"  : category,
#             "priority"  : priority,
#         }


# def run_demo() -> None:
#     """
#     Run the complete demo — processes all 10 sample tickets,
#     prints a results table, and shows final statistics.
#     No API keys or real systems needed.
#     """
#     print("\n")
#     print("=" * 65)
#     print(f"  AI TICKET RESOLVER — DEMO MODE")
#     print(f"  Company  : {COMPANY_NAME}")
#     print(f"  Time     : {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}")
#     print(f"  Tickets  : {len(DEMO_TICKETS)} sample tickets")
#     print("=" * 65)

#     print("\nStep 1/4 — Initializing database...")
#     initialize_database()
#     print("Database ready.\n")

#     # print("Step 2/4 — Setting up knowledge base...")
#     # create_sample_docs()
#     # build_index(force_rebuild=False)
#     # kb_ok = is_kb_available()
#     # print(f"Knowledge base: {'READY' if kb_ok else 'NOT INDEXED'}\n")

#     print("Step 2/4 — Setting up knowledge base...")
#     create_sample_docs()
#     build_index(force_rebuild=False)

#     import knowledge_base.kb_search as _kb_mod
#     _kb_mod._collection = None
#     _kb_mod._chroma_client = None

#     kb_ok = is_kb_available()
#     print(f"Knowledge base: {'READY' if kb_ok else 'NOT INDEXED'}\n")

#     print("Step 3/4 — Processing demo tickets...\n")
#     print("-" * 65)

#     results   = []
#     start     = time.time()

#     for ticket in DEMO_TICKETS:
#         result = process_demo_ticket(ticket)
#         results.append(result)
#         time.sleep(0.2)

#     duration = round(time.time() - start, 1)

#     print("\n" + "-" * 65)
#     print("Step 4/4 — Results summary\n")

#     print(f"  {'#':<6} {'SUBJECT':<42} {'CATEGORY':<18} {'STATUS'}")
#     print(f"  {'-'*6} {'-'*42} {'-'*18} {'-'*10}")

#     for i, (ticket, result) in enumerate(
#         zip(DEMO_TICKETS, results), start=1
#     ):
#         subject_short = ticket["subject"][:40]
#         category      = result["category"].replace("_", " ")
#         status        = result["status"]
#         status_icon   = "✓ RESOLVED" if status == "RESOLVED" else "→ ESCALATED"
#         print(
#             f"  {i:<6} {subject_short:<42} "
#             f"{category:<18} {status_icon}"
#         )

#     total     = len(results)
#     resolved  = sum(1 for r in results if r["status"] == "RESOLVED")
#     escalated = sum(1 for r in results if r["status"] == "ESCALATED")
#     rate      = round(resolved / total * 100, 1)

#     print("\n" + "=" * 65)
#     print("  DEMO RESULTS")
#     print("=" * 65)
#     print(f"  Total tickets processed  : {total}")
#     print(f"  Auto-resolved            : {resolved}")
#     print(f"  Escalated to engineer    : {escalated}")
#     print(f"  Auto-resolution rate     : {rate}%")
#     print(f"  Processing time          : {duration}s")
#     print("=" * 65)

#     db_stats = get_resolution_stats()
#     print("\n  DATABASE STATS (all time)")
#     print(f"  Total logged             : {db_stats['total']}")
#     print(f"  Resolved in DB           : {db_stats['resolved']}")
#     print(f"  Escalated in DB          : {db_stats['escalated']}")
#     print(f"  Top category             : {db_stats['top_category']}")
#     print("=" * 65)

#     print("\n  CATEGORY BREAKDOWN")
#     for cat, count in db_stats.get("category_counts", {}).items():
#         bar   = "█" * count
#         label = cat.replace("_", " ").title()
#         print(f"  {label:<25} : {bar} ({count})")

#     print("\n" + "=" * 65)
#     print("  DEMO COMPLETE")
#     print("  Next steps:")
#     print("  1. Run dashboard : streamlit run dashboard/app.py")
#     print("  2. Add real keys : edit config/.env")
#     print("  3. Run live mode : python main.py")
#     print("=" * 65 + "\n")


# if __name__ == "__main__":
#     run_demo()


import os
import sys
import time
import random
import logging
from datetime import datetime, timezone
from pathlib  import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv("config/.env")

from config.settings   import setup_logging, COMPANY_NAME
from database.db_setup import initialize_database, check_database_health
from database.db_logger import (
    log_ticket_action,
    log_classification,
    log_automation,
    log_notification,
    get_resolution_stats,
    get_all_ticket_logs,
    get_daily_stats,
    get_category_stats,
    delete_all_logs,
)
from knowledge_base.kb_indexer import (
    create_sample_docs,
    build_index,
    get_index_stats,
)
import knowledge_base.kb_search as _kb_mod
from knowledge_base.kb_search import (
    search_knowledge_base,
    is_kb_available,
    get_kb_stats,
)
from classifier.category_rules import classify_by_rules

setup_logging()
log = logging.getLogger(__name__)


DEMO_TICKETS = [
    {
        "id"              : 1001,
        "subject"         : "Please install Zoom on my laptop urgently",
        "description"     : (
            "Hi team, I need Zoom installed on my machine PC-ICICI-0042. "
            "I have a client call in 2 hours and Zoom is not installed. "
            "Please help asap."
        ),
        "requester_name"  : "Rahul Sharma",
        "requester_email" : "rahul.sharma@icici.com",
        "machine_name"    : "PC-ICICI-0042",
        "mentioned_apps"  : ["zoom"],
        "urgency_level"   : "high",
    },
    {
        "id"              : 1002,
        "subject"         : "Antivirus showing red warning — definitions out of date",
        "description"     : (
            "My Symantec antivirus is showing a red warning. "
            "The virus definitions are out of date. "
            "I tried updating manually but it fails every time. "
            "My machine is LAPTOP-ICICI-115."
        ),
        "requester_name"  : "Priya Mehta",
        "requester_email" : "priya.mehta@icici.com",
        "machine_name"    : "LAPTOP-ICICI-115",
        "mentioned_apps"  : ["symantec"],
        "urgency_level"   : "medium",
    },
    {
        "id"              : 1003,
        "subject"         : "Cannot login — account locked out",
        "description"     : (
            "I forgot my Windows password and now my account is locked. "
            "I tried 5 times and it says account is locked. "
            "Please reset my password. I cannot work at all."
        ),
        "requester_name"  : "Amit Patel",
        "requester_email" : "amit.patel@icici.com",
        "machine_name"    : "PC-ICICI-0099",
        "mentioned_apps"  : [],
        "urgency_level"   : "high",
    },
    {
        "id"              : 1004,
        "subject"         : "Cannot connect to VPN from home",
        "description"     : (
            "Since this morning I am unable to connect to VPN. "
            "Cisco AnyConnect shows connection timed out error. "
            "My colleagues are able to connect fine. "
            "I have a critical presentation in 1 hour."
        ),
        "requester_name"  : "Sneha Reddy",
        "requester_email" : "sneha.reddy@icici.com",
        "machine_name"    : "LAPTOP-ICICI-088",
        "mentioned_apps"  : ["anyconnect"],
        "urgency_level"   : "high",
    },
    {
        "id"              : 1005,
        "subject"         : "Printer offline — cannot print documents",
        "description"     : (
            "My printer is showing as offline. "
            "I cannot print any documents since yesterday. "
            "The print queue shows jobs stuck. "
            "Machine: WS-ICICI-201."
        ),
        "requester_name"  : "Vikram Singh",
        "requester_email" : "vikram.singh@icici.com",
        "machine_name"    : "WS-ICICI-201",
        "mentioned_apps"  : [],
        "urgency_level"   : "low",
    },
    {
        "id"              : 1006,
        "subject"         : "Outlook not opening — PST file error",
        "description"     : (
            "Outlook is not opening this morning. "
            "It shows an error about a corrupt PST file. "
            "I cannot send or receive any emails. "
            "This is very urgent as I have client emails pending."
        ),
        "requester_name"  : "Deepa Nair",
        "requester_email" : "deepa.nair@icici.com",
        "machine_name"    : "PC-ICICI-0055",
        "mentioned_apps"  : ["outlook"],
        "urgency_level"   : "high",
    },
    {
        "id"              : 1007,
        "subject"         : "Laptop screen is flickering badly",
        "description"     : (
            "My laptop screen has been flickering continuously since morning. "
            "Sometimes it goes completely blank for a few seconds. "
            "I think the display cable or screen might be damaged physically."
        ),
        "requester_name"  : "Karan Malhotra",
        "requester_email" : "karan.malhotra@icici.com",
        "machine_name"    : "LAPTOP-ICICI-220",
        "mentioned_apps"  : [],
        "urgency_level"   : "medium",
    },
    {
        "id"              : 1008,
        "subject"         : "Windows update failed with error code 0x80070002",
        "description"     : (
            "My Windows 10 update has been failing for the last 3 days. "
            "Error code 0x80070002. I tried running Windows Update "
            "troubleshooter but it did not fix. "
            "Machine: PC-ICICI-0077."
        ),
        "requester_name"  : "Ananya Krishnan",
        "requester_email" : "ananya.krishnan@icici.com",
        "machine_name"    : "PC-ICICI-0077",
        "mentioned_apps"  : [],
        "urgency_level"   : "medium",
    },
    {
        "id"              : 1009,
        "subject"         : "Cannot access shared drive — permission denied",
        "description"     : (
            "I am getting permission denied error when trying to open "
            "the Finance shared drive on the network. "
            "I had access last week but now it says access denied. "
            "I need access urgently for month-end reports."
        ),
        "requester_name"  : "Rohit Gupta",
        "requester_email" : "rohit.gupta@icici.com",
        "machine_name"    : "PC-ICICI-0033",
        "mentioned_apps"  : [],
        "urgency_level"   : "high",
    },
    {
        "id"              : 1010,
        "subject"         : "Need Microsoft Teams installed",
        "description"     : (
            "Please install Microsoft Teams on my desktop. "
            "My manager has asked me to join the team channel. "
            "Machine name is DESKTOP-ICICI-009."
        ),
        "requester_name"  : "Pooja Sharma",
        "requester_email" : "pooja.sharma@icici.com",
        "machine_name"    : "DESKTOP-ICICI-009",
        "mentioned_apps"  : ["microsoft teams"],
        "urgency_level"   : "medium",
    },
]


MOCK_AUTOMATION_RESULTS = {
    "app_install"      : True,
    "antivirus"        : True,
    "password_reset"   : True,
    "printer"          : True,
    "os_issue"         : True,
    "email_issue"      : True,
    "network"          : False,
    "hardware"         : False,
    "access_permission": False,
    "other"            : False,
}

MOCK_AUTOMATION_OUTPUT = {
    "app_install"      : "SUCCESS: App installed via winget on remote machine.",
    "antivirus"        : "SUCCESS: AV definitions updated. Full scan triggered.",
    "password_reset"   : "SUCCESS: AD password reset. SMS sent to user.",
    "printer"          : "SUCCESS: Print Spooler restarted. Queue cleared.",
    "os_issue"         : "SUCCESS: sfc /scannow done. Temp files cleared.",
    "email_issue"      : "SUCCESS: Outlook profile rebuilt. PST repaired.",
    "network"          : "FAILED: Cannot reach machine remotely.",
    "hardware"         : "FAILED: Hardware requires on-site inspection.",
    "access_permission": "FAILED: AD group changes require manual approval.",
    "other"            : "FAILED: No automation script for this category.",
}


def _mock_classify(ticket: dict) -> dict:
    """
    Classify a ticket using the rule-based classifier.
    No Claude API key needed — works completely offline.
    Also checks machine name and disables auto-resolve
    if machine is UNKNOWN.

    Args:
        ticket : Demo ticket dict

    Returns:
        Classification result dict
    """
    result = classify_by_rules(
        subject     = ticket["subject"],
        description = ticket["description"],
    )

    if ticket.get("machine_name", "UNKNOWN") == "UNKNOWN":
        if result.get("can_auto_resolve"):
            result["can_auto_resolve"] = False
            log.warning(
                f"  │  Machine UNKNOWN — "
                "auto-resolve disabled."
            )

    return result


def _mock_run_automation(
    ticket        : dict,
    classification: dict,
) -> bool:
    """
    Simulate running a PowerShell automation script.
    Returns realistic success/failure based on category.
    Logs to automation_logs table just like the real runner.
    Adds a small delay to simulate real script execution time.

    Args:
        ticket         : Demo ticket dict
        classification : Classification result dict

    Returns:
        True if automation would succeed, False otherwise
    """
    category     = classification.get("category", "other")
    machine_name = ticket.get("machine_name", "UNKNOWN")

    if machine_name == "UNKNOWN":
        log.warning(
            "  │  Cannot run — machine UNKNOWN."
        )
        return False

    time.sleep(random.uniform(0.2, 0.5))

    success = MOCK_AUTOMATION_RESULTS.get(category, False)
    output  = MOCK_AUTOMATION_OUTPUT.get(category, "No output.")

    script_map = {
        "app_install"    : "install_app.ps1",
        "antivirus"      : "update_antivirus.ps1",
        "password_reset" : "reset_password.ps1",
        "printer"        : "restart_print_spooler.ps1",
        "os_issue"       : "clear_disk_space.ps1",
        "email_issue"    : "repair_outlook.ps1",
    }
    script = script_map.get(category, "no_script.ps1")

    if success:
        log.info(f"  │  [DEMO] {script} → {output}")
    else:
        log.warning(f"  │  [DEMO] {script} → {output}")

    try:
        log_automation(
            ticket_id     = ticket["id"],
            script_name   = script,
            machine_name  = machine_name,
            success       = success,
            output        = f"[DEMO] {output}",
            duration_secs = random.uniform(5.0, 45.0),
        )
    except Exception as e:
        log.warning(f"  │  Automation log failed: {e}")

    return success


def _mock_search_kb(description: str) -> str | None:
    """
    Search the real ChromaDB KB index if available.
    Falls back to hardcoded demo guides if KB not indexed.
    This matches the real orchestrator behavior exactly.

    Args:
        description : Ticket description text to search

    Returns:
        Guide text string or None if nothing found
    """
    try:
        if is_kb_available():
            result = search_knowledge_base(description)
            if result:
                return result
    except Exception as e:
        log.warning(f"  │  KB search error: {e}")

    demo_guides = {
        "vpn"      : (
            "VPN Self-Help Guide\n"
            "1. Open Cisco AnyConnect from Start menu\n"
            "2. Enter server: vpn.icici.com\n"
            "3. Click Connect and enter your domain credentials\n"
            "4. If fails: restart the AnyConnect service\n"
            "   Open Task Manager → Services → vpnagent → Restart"
        ),
        "password" : (
            "Password Reset Self-Help\n"
            "1. Go to password.icici.com\n"
            "2. Click Forgot Password\n"
            "3. Enter your employee ID\n"
            "4. OTP will be sent to your registered mobile number\n"
            "5. Set new password — min 8 chars, 1 uppercase, 1 number"
        ),
        "printer"  : (
            "Printer Troubleshooting Guide\n"
            "1. Check printer is powered on and paper is loaded\n"
            "2. Open Control Panel → Devices and Printers\n"
            "3. Right-click printer → See what is printing\n"
            "4. Cancel all stuck jobs\n"
            "5. Open services.msc → Print Spooler → Restart"
        ),
        "outlook"  : (
            "Outlook Troubleshooting Guide\n"
            "1. Close Outlook completely\n"
            "2. Press Win+R → type: outlook.exe /safe → Enter\n"
            "3. If opens in Safe Mode → File → Options → Add-ins\n"
            "4. Disable all add-ins and restart Outlook normally\n"
            "5. If PST error: IT will run scanpst.exe remotely"
        ),
        "antivirus": (
            "Antivirus Troubleshooting Guide\n"
            "1. Open Windows Security from Start menu\n"
            "2. Click Virus and threat protection\n"
            "3. Click Check for updates\n"
            "4. Allow update to complete (5-10 minutes)\n"
            "5. If update fails: restart PC and try again"
        ),
        "access"   : (
            "Shared Drive Access Guide\n"
            "1. Verify you are connected to office network or VPN\n"
            "2. Try accessing via: \\\\fileserver01\\Finance\n"
            "3. If access denied: raise a ticket with your manager\n"
            "   approval to request AD group membership update\n"
            "4. IT will update your permissions within 4 hours"
        ),
    }

    desc_lower = description.lower()
    for keyword, guide in demo_guides.items():
        if keyword in desc_lower:
            return guide

    return None


def _mock_notify(
    ticket           : dict,
    notification_type: str,
    message          : str,
) -> None:
    """
    Simulate sending an email notification.
    In demo mode logs the notification instead of sending
    a real email via SMTP. Still logs to notification_logs
    table so the dashboard shows notification history.

    Args:
        ticket            : Demo ticket dict
        notification_type : Type — resolved | escalated |
                            kb_guide_sent | in_progress
        message           : Message that would be sent to user
    """
    email = ticket.get("requester_email", "unknown")

    log.info(
        f"  [DEMO EMAIL] To: {email} "
        f"| Type: {notification_type} "
        f"| Ticket: #{ticket['id']}"
    )

    try:
        log_notification(
            ticket_id  = ticket["id"],
            recipient  = email,
            notif_type = notification_type,
            subject    = ticket["subject"],
            success    = True,
        )
    except Exception as e:
        log.warning(f"  Notification log failed: {e}")


def process_demo_ticket(ticket: dict) -> dict:
    """
    Process a single demo ticket through the complete
    AI resolution pipeline end to end.

    Flow:
        1. Classify using rule-based classifier (offline)
        2. Check for force-escalation keywords
        3. Check machine name — disable auto if UNKNOWN
        4. If can_auto → simulate automation script
           a. Success → log RESOLVED, notify user
           b. Fail    → search KB, send guide, escalate
        5. If no auto → search KB, send guide, escalate
        6. Log all actions to database
        7. Return result summary dict

    Args:
        ticket : Demo ticket dict from DEMO_TICKETS list

    Returns:
        Dict with: ticket_id, status, reason, category, priority
    """
    ticket_id = ticket["id"]
    subject   = ticket["subject"]

    log.info("")
    log.info(f"  ┌─ Ticket #{ticket_id}: {subject[:55]}")
    log.info(f"  │  Requester : {ticket['requester_name']}")
    log.info(f"  │  Machine   : {ticket['machine_name']}")
    log.info(f"  │  Urgency   : {ticket['urgency_level']}")

    classification   = _mock_classify(ticket)
    category         = classification["category"]
    priority         = classification["priority"]
    can_auto         = classification["can_auto_resolve"]
    suggested_action = classification["suggested_action"]
    confidence       = classification["confidence"]
    force_escalate   = classification.get("force_escalate", False)

    log.info(f"  │  Category  : {category}")
    log.info(f"  │  Priority  : {priority}")
    log.info(f"  │  Auto      : {can_auto}")
    log.info(f"  │  Confidence: {confidence}")

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
        log.warning(f"  │  Classification log failed: {e}")

    if force_escalate:
        log.warning(
            f"  │  FORCE ESCALATION — critical keyword!"
        )
        try:
            log_ticket_action(
                ticket_id    = ticket_id,
                category     = category,
                priority     = "urgent",
                action_taken = "Force-escalated — critical keyword.",
                resolved_by  = "FORCE_ESCALATION",
                status       = "ESCALATED",
            )
        except Exception as e:
            log.warning(f"  │  DB log failed: {e}")

        log.info(f"  └─ Ticket #{ticket_id} → FORCE ESCALATED")
        return {
            "ticket_id": ticket_id,
            "status"   : "ESCALATED",
            "reason"   : "force_escalation",
            "category" : category,
            "priority" : "urgent",
        }

    if can_auto:
        log.info("  │  Running automation simulation...")
        auto_success = _mock_run_automation(ticket, classification)

        if auto_success:
            log.info("  │  Automation SUCCESS ✓")
            _mock_notify(ticket, "resolved", suggested_action)

            try:
                log_ticket_action(
                    ticket_id    = ticket_id,
                    category     = category,
                    priority     = priority,
                    action_taken = suggested_action,
                    resolved_by  = "AI_AUTO",
                    status       = "RESOLVED",
                )
            except Exception as e:
                log.warning(f"  │  DB log failed: {e}")

            log.info(f"  └─ Ticket #{ticket_id} → RESOLVED ✓")
            return {
                "ticket_id": ticket_id,
                "status"   : "RESOLVED",
                "reason"   : "auto_resolved",
                "category" : category,
                "priority" : priority,
            }

        else:
            log.warning(
                "  │  Automation FAILED — searching KB..."
            )
            kb_guide = _mock_search_kb(ticket["description"])

            if kb_guide:
                log.info("  │  KB guide found — sending to user.")
                _mock_notify(
                    ticket, "kb_guide_sent", kb_guide
                )
                resolved_by = "KB+ESCALATION"
                action      = "Auto-resolve failed. KB guide sent."
            else:
                log.info("  │  No KB guide found. Escalating.")
                resolved_by = "ESCALATION"
                action      = (
                    f"Auto-resolve failed. "
                    f"Escalated — {suggested_action}"
                )

            _mock_notify(ticket, "escalated", suggested_action)

            try:
                log_ticket_action(
                    ticket_id    = ticket_id,
                    category     = category,
                    priority     = priority,
                    action_taken = action,
                    resolved_by  = resolved_by,
                    status       = "ESCALATED",
                )
            except Exception as e:
                log.warning(f"  │  DB log failed: {e}")

            reason = (
                "auto_failed_kb_sent"
                if kb_guide else
                "auto_failed_no_kb"
            )
            log.info(f"  └─ Ticket #{ticket_id} → ESCALATED")
            return {
                "ticket_id": ticket_id,
                "status"   : "ESCALATED",
                "reason"   : reason,
                "category" : category,
                "priority" : priority,
            }

    else:
        log.info(
            "  │  Cannot auto-resolve — searching KB..."
        )
        kb_guide = _mock_search_kb(ticket["description"])

        if kb_guide:
            log.info("  │  KB guide found — sending to user.")
            _mock_notify(ticket, "kb_guide_sent", kb_guide)
            resolved_by = "KB+ESCALATION"
        else:
            log.info("  │  No KB guide. Escalating directly.")
            resolved_by = "ESCALATION"

        _mock_notify(ticket, "escalated", suggested_action)

        try:
            log_ticket_action(
                ticket_id    = ticket_id,
                category     = category,
                priority     = priority,
                action_taken = f"Escalated — {suggested_action}",
                resolved_by  = resolved_by,
                status       = "ESCALATED",
            )
        except Exception as e:
            log.warning(f"  │  DB log failed: {e}")

        log.info(f"  └─ Ticket #{ticket_id} → ESCALATED")
        return {
            "ticket_id": ticket_id,
            "status"   : "ESCALATED",
            "reason"   : "manual_escalation",
            "category" : category,
            "priority" : priority,
        }


def _setup_knowledge_base() -> bool:
    """
    Set up the ChromaDB knowledge base for the demo.
    Creates sample docs, builds index if needed, and
    resets the singleton connection so fresh queries work.

    Returns:
        True if KB is available, False otherwise
    """
    try:
        create_sample_docs()
        build_index(force_rebuild=False)

        _kb_mod._collection    = None
        _kb_mod._chroma_client = None

        kb_ok = is_kb_available()
        return kb_ok

    except Exception as e:
        log.warning(f"KB setup warning: {e}")
        return False


def run_demo() -> None:
    """
    Run the complete AI Ticket Resolver demo.
    Processes all 10 sample ICICI Bank tickets end to end
    and prints a full results table with statistics.

    No API keys, no Freshdesk account, no real machines needed.
    Everything is simulated using real logic and real DB logging.
    """
    print("\n")
    print("=" * 65)
    print(f"  AI TICKET RESOLVER — DEMO MODE")
    print(f"  Company  : {COMPANY_NAME}")
    print(
        f"  Time     : "
        f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
    )
    print(f"  Tickets  : {len(DEMO_TICKETS)} sample tickets")
    print(f"  Classifier: Rule-based (offline, no API needed)")
    print("=" * 65)

    print("\nStep 1/4 — Initializing database...")
    try:
        initialize_database()
        health = check_database_health()
        if health["status"] == "OK":
            print(
                f"Database ready ✓  "
                f"(tables: {len(health['row_counts'])}, "
                f"indexes: {health.get('index_count', 0)})\n"
            )
        else:
            print(f"Database warning: {health.get('error')}\n")
    except Exception as e:
        print(f"Database error: {e}\n")

    print("Step 2/4 — Setting up knowledge base...")
    kb_ok = _setup_knowledge_base()
    if kb_ok:
        kb_stats = get_kb_stats()
        print(
            f"Knowledge base ready ✓  "
            f"({kb_stats.get('total_chunks', 0)} chunks indexed)\n"
        )
    else:
        print(
            "Knowledge base not indexed "
            "(fallback demo guides will be used)\n"
        )

    print("Step 3/4 — Processing demo tickets...")
    print("-" * 65)

    results = []
    start   = time.time()

    for ticket in DEMO_TICKETS:
        try:
            result = process_demo_ticket(ticket)
        except Exception as e:
            log.error(
                f"Failed to process ticket "
                f"#{ticket['id']}: {e}"
            )
            result = {
                "ticket_id": ticket["id"],
                "status"   : "ESCALATED",
                "reason"   : "processing_error",
                "category" : "other",
                "priority" : "medium",
            }
        results.append(result)
        time.sleep(0.1)

    duration = round(time.time() - start, 1)

    print("\n" + "-" * 65)
    print("Step 4/4 — Results\n")

    print(
        f"  {'#':<5} "
        f"{'SUBJECT':<42} "
        f"{'CATEGORY':<18} "
        f"{'STATUS'}"
    )
    print(
        f"  {'-'*5} "
        f"{'-'*42} "
        f"{'-'*18} "
        f"{'-'*12}"
    )

    for i, (ticket, result) in enumerate(
        zip(DEMO_TICKETS, results), start=1
    ):
        subject_short = ticket["subject"][:40]
        category      = result["category"].replace("_", " ")
        status_icon   = (
            "✓ RESOLVED"
            if result["status"] == "RESOLVED"
            else "→ ESCALATED"
        )
        print(
            f"  {i:<5} "
            f"{subject_short:<42} "
            f"{category:<18} "
            f"{status_icon}"
        )

    total     = len(results)
    resolved  = sum(
        1 for r in results if r["status"] == "RESOLVED"
    )
    escalated = total - resolved
    rate      = (
        round(resolved / total * 100, 1) if total > 0 else 0
    )

    print("\n" + "=" * 65)
    print("  DEMO RESULTS")
    print("=" * 65)
    print(f"  Total tickets processed  : {total}")
    print(f"  Auto-resolved            : {resolved}  ✓")
    print(f"  Escalated to engineer    : {escalated}")
    print(f"  Auto-resolution rate     : {rate}%")
    print(f"  Processing time          : {duration}s")
    print(f"  KB available             : {'Yes ✓' if kb_ok else 'No (fallback used)'}")
    print("=" * 65)

    print("\n  REASON BREAKDOWN")
    reason_map = {
        "auto_resolved"      : "✓ AI Auto-Resolved",
        "auto_failed_kb_sent": "📚 KB Guide Sent + Escalated",
        "auto_failed_no_kb"  : "→ Auto Failed + Escalated",
        "manual_escalation"  : "→ Manual Escalation",
        "force_escalation"   : "🚨 Force Escalated",
        "processing_error"   : "⚠ Processing Error",
    }
    reason_counts: dict = {}
    for r in results:
        reason = reason_map.get(r["reason"], r["reason"])
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    for reason, count in sorted(
        reason_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        bar = "█" * count
        print(f"  {reason:<35} : {bar} ({count})")

    print("\n  CATEGORY BREAKDOWN")
    try:
        db_stats = get_resolution_stats()
        for cat, count in sorted(
            db_stats.get("category_counts", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            bar   = "█" * count
            label = cat.replace("_", " ").title()
            print(f"  {label:<25} : {bar} ({count})")
    except Exception as e:
        log.warning(f"Could not fetch category stats: {e}")

    print("\n  DATABASE STATS (all time)")
    try:
        db_stats = get_resolution_stats()
        print(f"  Total logged             : {db_stats['total']}")
        print(f"  Resolved in DB           : {db_stats['resolved']}")
        print(f"  Escalated in DB          : {db_stats['escalated']}")
        print(f"  AI auto-resolved         : {db_stats['ai_resolved']}")
        print(f"  Auto-resolve rate        : {db_stats['auto_rate_pct']}%")
        print(f"  Top category             : {db_stats['top_category']}")
        print(f"  KB guides sent           : {db_stats.get('kb_sent', 0)}")
    except Exception as e:
        log.warning(f"Could not fetch DB stats: {e}")

    print("\n" + "=" * 65)
    print("  DEMO COMPLETE ✓")
    print("=" * 65)
    print("\n  Next steps:")
    print(
        "  1. View dashboard  →  "
        "streamlit run dashboard/app.py"
    )
    print(
        "  2. Run tests       →  "
        "python tests/test_classifier.py"
    )
    print(
        "  3. Run again       →  "
        "python main.py   (adds more data to dashboard)"
    )
    print(
        "  4. Reset demo data →  "
        "python demo/demo_runner.py --reset"
    )
    print(
        "  5. Switch to live  →  "
        "set DEMO_MODE=false in config/.env"
    )
    print("=" * 65 + "\n")


if __name__ == "__main__":
    import sys as _sys

    if "--reset" in _sys.argv:
        print("\nResetting all demo data...")
        setup_logging()
        initialize_database()
        deleted = delete_all_logs()
        if deleted:
            print("All logs cleared ✓")
            print("Run python main.py to start fresh.\n")
        else:
            print("Reset failed — check logs.\n")
    else:
        run_demo()