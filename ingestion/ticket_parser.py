# import logging
# import re
# from datetime import datetime

# log = logging.getLogger(__name__)

# FRESHDESK_STATUS_MAP = {
#     2: "open",
#     3: "pending",
#     4: "resolved",
#     5: "closed",
#     6: "waiting_on_third_party",
# }

# FRESHDESK_PRIORITY_MAP = {
#     1: "low",
#     2: "medium",
#     3: "high",
#     4: "urgent",
# }

# COMMON_MACHINE_PATTERNS = [
#     r'\b([A-Z]{2,6}[-_]?[A-Z]{0,4}[-_]?\d{3,6})\b',
#     r'\b(PC[-_]\w{3,10})\b',
#     r'\b(LAPTOP[-_]\w{3,10})\b',
#     r'\b(DESKTOP[-_]\w{3,10})\b',
#     r'\b(WS[-_]\w{3,10})\b',
#     r'\b(ICICI[-_]\w{3,10})\b',
# ]

# COMMON_APP_PATTERNS = [
#     "zoom", "teams", "microsoft teams", "ms teams",
#     "chrome", "google chrome", "firefox", "edge",
#     "office", "ms office", "microsoft office", "word", "excel", "powerpoint",
#     "outlook", "skype", "slack", "webex",
#     "adobe", "acrobat", "photoshop",
#     "vpn", "cisco vpn", "anyconnect",
#     "sap", "oracle", "tally",
#     "antivirus", "symantec", "mcafee", "defender",
#     "putty", "winscp", "notepad++", "7zip",
# ]

# URGENCY_KEYWORDS = {
#     "critical" : ["critical", "emergency", "data loss", "breach", "hacked",
#                   "virus detected", "ransomware", "production down"],
#     "high"     : ["urgent", "asap", "immediately", "cannot work", "blocked",
#                   "meeting in", "call in", "deadline", "client call", "not working at all"],
#     "medium"   : ["please help", "issue", "problem", "not working", "error",
#                   "failed", "unable to"],
#     "low"      : ["when possible", "not urgent", "minor", "small issue",
#                   "whenever", "if possible", "low priority"],
# }


# def parse_ticket(raw_ticket: dict) -> dict:
#     """
#     Convert a raw Freshdesk API ticket response into a clean,
#     normalized dictionary that the rest of the system can use.

#     Args:
#         raw_ticket : Raw dict from Freshdesk API response

#     Returns:
#         Clean normalized ticket dict
#     """
#     if not raw_ticket or not isinstance(raw_ticket, dict):
#         log.error("parse_ticket received invalid input — expected a dict.")
#         return _empty_ticket()

#     try:
#         ticket_id    = raw_ticket.get("id", 0)
#         subject      = _clean_text(raw_ticket.get("subject", ""))
#         description  = _clean_html(raw_ticket.get("description", ""))
#         desc_text    = _clean_html(raw_ticket.get("description_text", description))

#         full_text = f"{subject} {desc_text}"

#         status_code   = raw_ticket.get("status", 2)
#         priority_code = raw_ticket.get("priority", 2)

#         status   = FRESHDESK_STATUS_MAP.get(status_code, "open")
#         priority = FRESHDESK_PRIORITY_MAP.get(priority_code, "medium")

#         requester_id    = raw_ticket.get("requester_id")
#         requester_info  = raw_ticket.get("requester", {})
#         requester_email = requester_info.get("email", "")
#         requester_name  = requester_info.get("name", "Unknown User")

#         responder_id = raw_ticket.get("responder_id")
#         group_id     = raw_ticket.get("group_id")

#         created_at = _parse_datetime(raw_ticket.get("created_at"))
#         updated_at = _parse_datetime(raw_ticket.get("updated_at"))
#         due_by     = _parse_datetime(raw_ticket.get("due_by"))

#         tags              = raw_ticket.get("tags", [])
#         custom_fields     = raw_ticket.get("custom_fields", {})
#         attachments       = raw_ticket.get("attachments", [])
#         conversation_count = raw_ticket.get("nr_of_activities", 0)

#         machine_name    = _extract_machine_name(full_text, custom_fields)
#         mentioned_apps  = _extract_app_names(full_text)
#         urgency_level   = _detect_urgency(full_text)
#         is_first_ticket = conversation_count == 0
#         has_attachment  = len(attachments) > 0
#         word_count      = len(desc_text.split())
#         ticket_age_hrs  = _get_ticket_age_hours(created_at)

#         parsed = {
#             "id"               : ticket_id,
#             "subject"          : subject,
#             "description"      : desc_text,
#             "full_text"        : full_text,
#             "status"           : status,
#             "status_code"      : status_code,
#             "priority"         : priority,
#             "priority_code"    : priority_code,
#             "requester_id"     : requester_id,
#             "requester_email"  : requester_email,
#             "requester_name"   : requester_name,
#             "responder_id"     : responder_id,
#             "group_id"         : group_id,
#             "created_at"       : created_at,
#             "updated_at"       : updated_at,
#             "due_by"           : due_by,
#             "tags"             : tags,
#             "custom_fields"    : custom_fields,
#             "attachments"      : attachments,
#             "has_attachment"   : has_attachment,
#             "machine_name"     : machine_name,
#             "mentioned_apps"   : mentioned_apps,
#             "urgency_level"    : urgency_level,
#             "is_first_ticket"  : is_first_ticket,
#             "word_count"       : word_count,
#             "ticket_age_hours" : ticket_age_hrs,
#             "conversation_count": conversation_count,
#             "source"           : _get_source_name(raw_ticket.get("source", 1)),
#         }

#         log.info(f"Parsed ticket #{ticket_id}: '{subject[:50]}...' "
#                  f"| Status: {status} | Priority: {priority} "
#                  f"| Machine: {machine_name} | Apps: {mentioned_apps}")

#         return parsed

#     except Exception as e:
#         log.error(f"Error parsing ticket: {e}")
#         log.debug(f"Raw ticket data: {raw_ticket}")
#         return _empty_ticket()


# def parse_tickets_bulk(raw_tickets: list) -> list:
#     """
#     Parse a list of raw Freshdesk tickets all at once.

#     Args:
#         raw_tickets : List of raw ticket dicts from Freshdesk API

#     Returns:
#         List of clean parsed ticket dicts
#     """
#     if not raw_tickets:
#         log.warning("parse_tickets_bulk received an empty list.")
#         return []

#     log.info(f"Bulk parsing {len(raw_tickets)} tickets...")

#     parsed = []
#     failed = 0

#     for raw in raw_tickets:
#         result = parse_ticket(raw)
#         if result["id"] != 0:
#             parsed.append(result)
#         else:
#             failed += 1

#     log.info(f"Bulk parse complete: {len(parsed)} success, {failed} failed.")
#     return parsed


# def _clean_text(text: str) -> str:
#     """
#     Remove extra whitespace and normalize a plain text string.
#     """
#     if not text:
#         return ""
#     text = text.strip()
#     text = re.sub(r'\s+', ' ', text)
#     return text


# def _clean_html(html: str) -> str:
#     """
#     Strip HTML tags from ticket description and return clean plain text.
#     Freshdesk stores descriptions as HTML — this converts them to readable text.
#     """
#     if not html:
#         return ""

#     text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
#     text = re.sub(r'<p\s*/?>', '\n', text, flags=re.IGNORECASE)
#     text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
#     text = re.sub(r'<li\s*/?>', '\n- ', text, flags=re.IGNORECASE)
#     text = re.sub(r'<[^>]+>', '', text)

#     text = text.replace('&nbsp;', ' ')
#     text = text.replace('&amp;', '&')
#     text = text.replace('&lt;', '<')
#     text = text.replace('&gt;', '>')
#     text = text.replace('&quot;', '"')
#     text = text.replace('&#39;', "'")

#     text = re.sub(r'\n{3,}', '\n\n', text)
#     text = re.sub(r'[ \t]+', ' ', text)
#     text = text.strip()

#     return text


# def _extract_machine_name(text: str, custom_fields: dict) -> str:
#     """
#     Try to extract the user's machine/computer name from:
#     1. Custom fields in Freshdesk (most reliable)
#     2. Pattern matching in the ticket text

#     Args:
#         text          : Combined subject + description text
#         custom_fields : Custom fields dict from Freshdesk ticket

#     Returns:
#         Machine name string or 'UNKNOWN' if not found
#     """
#     for field_name in ["machine_name", "computer_name", "hostname",
#                        "asset_name", "device_name", "cf_machine_name",
#                        "cf_computer_name", "cf_asset_tag"]:
#         value = custom_fields.get(field_name)
#         if value and isinstance(value, str) and len(value) > 2:
#             log.debug(f"Machine name from custom field '{field_name}': {value}")
#             return value.strip().upper()

#     text_upper = text.upper()

#     for pattern in COMMON_MACHINE_PATTERNS:
#         matches = re.findall(pattern, text_upper)
#         if matches:
#             machine = matches[0].strip()
#             log.debug(f"Machine name from text pattern: {machine}")
#             return machine

#     return "UNKNOWN"


# def _extract_app_names(text: str) -> list:
#     """
#     Detect any software application names mentioned in the ticket text.
#     Helps automation runner understand which app to install or fix.

#     Args:
#         text : Combined subject + description text

#     Returns:
#         List of detected app name strings (lowercase)
#     """
#     text_lower = text.lower()
#     found = []

#     for app in COMMON_APP_PATTERNS:
#         if app in text_lower and app not in found:
#             found.append(app)

#     return found


# def _detect_urgency(text: str) -> str:
#     """
#     Detect the urgency level from keywords in the ticket text.
#     This supplements the Freshdesk priority field with semantic analysis.

#     Args:
#         text : Combined subject + description text

#     Returns:
#         Urgency level string: 'critical', 'high', 'medium', or 'low'
#     """
#     text_lower = text.lower()

#     for level in ["critical", "high", "medium", "low"]:
#         keywords = URGENCY_KEYWORDS.get(level, [])
#         if any(kw in text_lower for kw in keywords):
#             return level

#     return "medium"


# def _parse_datetime(dt_string: str) -> str | None:
#     """
#     Parse Freshdesk ISO datetime string to a readable format.

#     Args:
#         dt_string : ISO 8601 datetime string from Freshdesk

#     Returns:
#         Formatted datetime string or None
#     """
#     if not dt_string:
#         return None

#     try:
#         dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
#         return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
#     except Exception:
#         return dt_string


# def _get_ticket_age_hours(created_at: str) -> float:
#     """
#     Calculate how many hours old the ticket is.

#     Args:
#         created_at : Formatted datetime string from _parse_datetime()

#     Returns:
#         Age in hours as float, or 0.0 if cannot be calculated
#     """
#     if not created_at:
#         return 0.0

#     try:
#         fmt = "%Y-%m-%d %H:%M:%S UTC"
#         created = datetime.strptime(created_at, fmt)
#         now     = datetime.utcnow()
#         delta   = now - created
#         return round(delta.total_seconds() / 3600, 2)
#     except Exception:
#         return 0.0


# def _get_source_name(source_code: int) -> str:
#     """
#     Convert Freshdesk source code to human readable name.
#     """
#     sources = {
#         1: "email",
#         2: "portal",
#         3: "phone",
#         7: "chat",
#         9: "feedback_widget",
#         10: "outbound_email",
#     }
#     return sources.get(source_code, "unknown")


# def _empty_ticket() -> dict:
#     """
#     Return a safe empty ticket dict used when parsing fails.
#     Prevents the rest of the system from crashing on bad data.
#     """
#     return {
#         "id"               : 0,
#         "subject"          : "",
#         "description"      : "",
#         "full_text"        : "",
#         "status"           : "open",
#         "status_code"      : 2,
#         "priority"         : "medium",
#         "priority_code"    : 2,
#         "requester_id"     : None,
#         "requester_email"  : "",
#         "requester_name"   : "Unknown",
#         "responder_id"     : None,
#         "group_id"         : None,
#         "created_at"       : None,
#         "updated_at"       : None,
#         "due_by"           : None,
#         "tags"             : [],
#         "custom_fields"    : {},
#         "attachments"      : [],
#         "has_attachment"   : False,
#         "machine_name"     : "UNKNOWN",
#         "mentioned_apps"   : [],
#         "urgency_level"    : "medium",
#         "is_first_ticket"  : True,
#         "word_count"       : 0,
#         "ticket_age_hours" : 0.0,
#         "conversation_count": 0,
#         "source"           : "unknown",
#     }


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(message)s"
#     )

#     sample_tickets = [
#         {
#             "id"              : 1001,
#             "subject"         : "Zoom not installed on my laptop",
#             "description"     : "<p>Hi team,</p><p>I need <b>Zoom</b> installed on my machine "
#                                 "PC-ICICI-0042. I have a client call in 2 hours. "
#                                 "Please install it urgently.</p><br>Thanks,<br>Rahul",
#             "description_text": "",
#             "status"          : 2,
#             "priority"        : 3,
#             "requester_id"    : 5001,
#             "requester"       : {"email": "rahul.sharma@icici.com", "name": "Rahul Sharma"},
#             "responder_id"    : None,
#             "group_id"        : 10,
#             "created_at"      : "2024-01-15T09:30:00Z",
#             "updated_at"      : "2024-01-15T09:30:00Z",
#             "due_by"          : "2024-01-15T17:30:00Z",
#             "tags"            : [],
#             "custom_fields"   : {"cf_machine_name": "PC-ICICI-0042"},
#             "attachments"     : [],
#             "source"          : 2,
#             "nr_of_activities": 0,
#         },
#         {
#             "id"              : 1002,
#             "subject"         : "Antivirus showing error - definitions out of date",
#             "description"     : "<p>My Symantec antivirus is showing a red warning. "
#                                 "Definitions are out of date. I tried updating manually "
#                                 "but it fails. My computer name is LAPTOP-ICICI-115.</p>",
#             "description_text": "",
#             "status"          : 2,
#             "priority"        : 2,
#             "requester_id"    : 5002,
#             "requester"       : {"email": "priya.mehta@icici.com", "name": "Priya Mehta"},
#             "responder_id"    : None,
#             "group_id"        : 10,
#             "created_at"      : "2024-01-15T10:00:00Z",
#             "updated_at"      : "2024-01-15T10:00:00Z",
#             "due_by"          : "2024-01-16T10:00:00Z",
#             "tags"            : ["antivirus"],
#             "custom_fields"   : {},
#             "attachments"     : [],
#             "source"          : 1,
#             "nr_of_activities": 0,
#         },
#         {
#             "id"              : 1003,
#             "subject"         : "Cannot connect to VPN from home - urgent",
#             "description"     : "<p>Since this morning I am unable to connect to VPN. "
#                                 "Error says <b>Connection timed out</b>. "
#                                 "I have a critical client presentation in 1 hour. "
#                                 "All my files are on the network drive. Please help ASAP.</p>",
#             "description_text": "",
#             "status"          : 2,
#             "priority"        : 3,
#             "requester_id"    : 5003,
#             "requester"       : {"email": "amit.patel@icici.com", "name": "Amit Patel"},
#             "responder_id"    : None,
#             "group_id"        : 10,
#             "created_at"      : "2024-01-15T08:00:00Z",
#             "updated_at"      : "2024-01-15T08:00:00Z",
#             "due_by"          : "2024-01-15T12:00:00Z",
#             "tags"            : ["vpn", "urgent"],
#             "custom_fields"   : {},
#             "attachments"     : [],
#             "source"          : 1,
#             "nr_of_activities": 2,
#         },
#     ]

#     print("\n" + "=" * 60)
#     print("TICKET PARSER TEST RUN")
#     print("=" * 60 + "\n")

#     for raw in sample_tickets:
#         parsed = parse_ticket(raw)

#         print(f"Ticket ID       : {parsed['id']}")
#         print(f"Subject         : {parsed['subject']}")
#         print(f"Description     : {parsed['description'][:80]}...")
#         print(f"Status          : {parsed['status']}")
#         print(f"Priority        : {parsed['priority']}")
#         print(f"Requester       : {parsed['requester_name']} ({parsed['requester_email']})")
#         print(f"Machine Name    : {parsed['machine_name']}")
#         print(f"Mentioned Apps  : {parsed['mentioned_apps']}")
#         print(f"Urgency Level   : {parsed['urgency_level']}")
#         print(f"Has Attachment  : {parsed['has_attachment']}")
#         print(f"Ticket Age (hrs): {parsed['ticket_age_hours']}")
#         print(f"Source          : {parsed['source']}")
#         print(f"Word Count      : {parsed['word_count']}")
#         print("-" * 60)

#     print("\nBulk parse test:")
#     bulk_results = parse_tickets_bulk(sample_tickets)
#     print(f"Parsed {len(bulk_results)} tickets successfully.")
    

import os
import re
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() == "true"

FRESHDESK_STATUS_MAP = {
    2: "open",
    3: "pending",
    4: "resolved",
    5: "closed",
    6: "waiting_on_third_party",
}

FRESHDESK_PRIORITY_MAP = {
    1: "low",
    2: "medium",
    3: "high",
    4: "urgent",
}

COMMON_MACHINE_PATTERNS = [
    r'\b([A-Z]{2,6}[-_]?[A-Z]{0,4}[-_]?\d{3,6})\b',
    r'\b(PC[-_]\w{3,10})\b',
    r'\b(LAPTOP[-_]\w{3,10})\b',
    r'\b(DESKTOP[-_]\w{3,10})\b',
    r'\b(WS[-_]\w{3,10})\b',
    r'\b(ICICI[-_]\w{3,10})\b',
]

COMMON_APP_PATTERNS = [
    "zoom",
    "teams", "microsoft teams", "ms teams",
    "chrome", "google chrome",
    "firefox", "edge",
    "office", "ms office", "microsoft office",
    "word", "excel", "powerpoint",
    "outlook", "skype", "slack", "webex",
    "adobe", "acrobat", "photoshop",
    "vpn", "cisco vpn", "anyconnect",
    "sap", "oracle", "tally",
    "antivirus", "symantec", "mcafee", "defender",
    "putty", "winscp", "notepad++", "7zip",
]

URGENCY_KEYWORDS = {
    "critical": [
        "critical", "emergency", "data loss", "breach",
        "hacked", "virus detected", "ransomware",
        "production down",
    ],
    "high": [
        "urgent", "asap", "immediately", "cannot work",
        "blocked", "meeting in", "call in", "deadline",
        "client call", "not working at all",
    ],
    "medium": [
        "please help", "issue", "problem", "not working",
        "error", "failed", "unable to",
    ],
    "low": [
        "when possible", "not urgent", "minor",
        "small issue", "whenever", "if possible",
        "low priority",
    ],
}


def parse_ticket(raw_ticket: dict) -> dict:
    """
    Convert a raw Freshdesk API ticket response into a clean
    normalized dictionary the rest of the system can use.

    Also accepts demo ticket dicts from demo_runner.py — these
    already have clean fields so parsing is minimal.

    Args:
        raw_ticket : Raw dict from Freshdesk API or demo_runner

    Returns:
        Clean normalized ticket dict
    """
    if not raw_ticket or not isinstance(raw_ticket, dict):
        log.error(
            "parse_ticket received invalid input — "
            "expected a dict."
        )
        return _empty_ticket()

    if _is_demo_ticket(raw_ticket):
        return _parse_demo_ticket(raw_ticket)

    try:
        ticket_id  = raw_ticket.get("id", 0)
        subject    = _clean_text(raw_ticket.get("subject", ""))
        description = _clean_html(
            raw_ticket.get("description", "")
        )
        desc_text  = _clean_html(
            raw_ticket.get(
                "description_text", description
            )
        )

        full_text = f"{subject} {desc_text}"

        status_code   = raw_ticket.get("status",   2)
        priority_code = raw_ticket.get("priority",  2)
        status        = FRESHDESK_STATUS_MAP.get(
            status_code, "open"
        )
        priority      = FRESHDESK_PRIORITY_MAP.get(
            priority_code, "medium"
        )

        requester_info  = raw_ticket.get("requester", {})
        requester_email = requester_info.get("email", "")
        requester_name  = requester_info.get(
            "name", "Unknown User"
        )

        created_at = _parse_datetime(
            raw_ticket.get("created_at")
        )
        updated_at = _parse_datetime(
            raw_ticket.get("updated_at")
        )
        due_by     = _parse_datetime(
            raw_ticket.get("due_by")
        )

        tags              = raw_ticket.get("tags",         [])
        custom_fields     = raw_ticket.get("custom_fields",{})
        attachments       = raw_ticket.get("attachments",  [])
        conversation_count = raw_ticket.get(
            "nr_of_activities", 0
        )

        machine_name   = _extract_machine_name(
            full_text, custom_fields
        )
        mentioned_apps = _extract_app_names(full_text)
        urgency_level  = _detect_urgency(full_text)
        ticket_age_hrs = _get_ticket_age_hours(created_at)

        parsed = {
            "id"               : ticket_id,
            "subject"          : subject,
            "description"      : desc_text,
            "full_text"        : full_text,
            "status"           : status,
            "status_code"      : status_code,
            "priority"         : priority,
            "priority_code"    : priority_code,
            "requester_id"     : raw_ticket.get("requester_id"),
            "requester_email"  : requester_email,
            "requester_name"   : requester_name,
            "responder_id"     : raw_ticket.get("responder_id"),
            "group_id"         : raw_ticket.get("group_id"),
            "created_at"       : created_at,
            "updated_at"       : updated_at,
            "due_by"           : due_by,
            "tags"             : tags,
            "custom_fields"    : custom_fields,
            "attachments"      : attachments,
            "has_attachment"   : len(attachments) > 0,
            "machine_name"     : machine_name,
            "mentioned_apps"   : mentioned_apps,
            "urgency_level"    : urgency_level,
            "is_first_ticket"  : conversation_count == 0,
            "word_count"       : len(desc_text.split()),
            "ticket_age_hours" : ticket_age_hrs,
            "conversation_count": conversation_count,
            "source"           : _get_source_name(
                raw_ticket.get("source", 1)
            ),
        }

        log.info(
            f"Parsed ticket #{ticket_id}: "
            f"'{subject[:50]}' "
            f"| {status} | {priority} "
            f"| machine: {machine_name} "
            f"| apps: {mentioned_apps}"
        )

        return parsed

    except Exception as e:
        log.error(f"Error parsing ticket: {e}")
        log.debug(f"Raw ticket data: {raw_ticket}")
        return _empty_ticket()


def _is_demo_ticket(raw_ticket: dict) -> bool:
    """
    Detect if a raw ticket dict came from demo_runner.py
    rather than the real Freshdesk API.

    Demo tickets from demo_runner.py already have clean
    fields like 'requester_name', 'machine_name', and
    'mentioned_apps' pre-populated — they do not need
    HTML parsing or field extraction.

    Args:
        raw_ticket : Raw ticket dict to check

    Returns:
        True if this looks like a demo ticket
    """
    return (
        DEMO_MODE
        and "requester_name" in raw_ticket
        and "machine_name"   in raw_ticket
        and "urgency_level"  in raw_ticket
    )


def _parse_demo_ticket(raw_ticket: dict) -> dict:
    """
    Parse a demo ticket dict from demo_runner.py.
    Demo tickets already have clean pre-populated fields
    so this is much simpler than the full Freshdesk parser.

    Args:
        raw_ticket : Demo ticket dict from DEMO_TICKETS list

    Returns:
        Normalized ticket dict compatible with all other modules
    """
    ticket_id   = raw_ticket.get("id", 0)
    subject     = raw_ticket.get("subject",         "")
    description = raw_ticket.get("description",     "")
    full_text   = f"{subject} {description}"

    now_str = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    parsed = {
        "id"               : ticket_id,
        "subject"          : subject,
        "description"      : description,
        "full_text"        : full_text,
        "status"           : "open",
        "status_code"      : 2,
        "priority"         : "medium",
        "priority_code"    : 2,
        "requester_id"     : None,
        "requester_email"  : raw_ticket.get(
            "requester_email", ""
        ),
        "requester_name"   : raw_ticket.get(
            "requester_name", "Unknown User"
        ),
        "responder_id"     : None,
        "group_id"         : None,
        "created_at"       : now_str,
        "updated_at"       : now_str,
        "due_by"           : None,
        "tags"             : [],
        "custom_fields"    : {},
        "attachments"      : [],
        "has_attachment"   : False,
        "machine_name"     : raw_ticket.get(
            "machine_name", "UNKNOWN"
        ),
        "mentioned_apps"   : raw_ticket.get(
            "mentioned_apps", []
        ),
        "urgency_level"    : raw_ticket.get(
            "urgency_level", "medium"
        ),
        "is_first_ticket"  : True,
        "word_count"       : len(description.split()),
        "ticket_age_hours" : 0.0,
        "conversation_count": 0,
        "source"           : "demo",
    }

    log.debug(
        f"[DEMO] Parsed demo ticket #{ticket_id}: "
        f"'{subject[:50]}' "
        f"| machine: {parsed['machine_name']} "
        f"| apps: {parsed['mentioned_apps']}"
    )

    return parsed


def parse_tickets_bulk(raw_tickets: list) -> list:
    """
    Parse a list of raw Freshdesk or demo tickets at once.
    Filters out any tickets that fail parsing (id == 0).

    Args:
        raw_tickets : List of raw ticket dicts

    Returns:
        List of clean parsed ticket dicts
    """
    if not raw_tickets:
        log.warning("parse_tickets_bulk received empty list.")
        return []

    log.info(f"Bulk parsing {len(raw_tickets)} ticket(s)...")

    parsed = []
    failed = 0

    for raw in raw_tickets:
        result = parse_ticket(raw)
        if result["id"] != 0:
            parsed.append(result)
        else:
            failed += 1

    log.info(
        f"Bulk parse complete: "
        f"{len(parsed)} success, {failed} failed."
    )
    return parsed


def _clean_text(text: str) -> str:
    """
    Remove extra whitespace and normalize plain text.

    Args:
        text : Raw text string

    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def _clean_html(html: str) -> str:
    """
    Strip HTML tags from ticket description and return
    clean plain text. Freshdesk stores descriptions as
    HTML — this converts them to readable text.

    Args:
        html : Raw HTML string from Freshdesk

    Returns:
        Clean plain text string
    """
    if not html:
        return ""

    text = re.sub(
        r'<br\s*/?>', '\n', html, flags=re.IGNORECASE
    )
    text = re.sub(
        r'<p\s*/?>', '\n', text, flags=re.IGNORECASE
    )
    text = re.sub(
        r'</p>', '\n', text, flags=re.IGNORECASE
    )
    text = re.sub(
        r'<li\s*/?>', '\n- ', text, flags=re.IGNORECASE
    )
    text = re.sub(r'<[^>]+>', '', text)

    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;',  '&')
    text = text.replace('&lt;',   '<')
    text = text.replace('&gt;',   '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;',  "'")

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()

    return text


def _extract_machine_name(
    text         : str,
    custom_fields: dict,
) -> str:
    """
    Extract the user's machine/computer name from:
    1. Custom fields in Freshdesk (most reliable)
    2. Pattern matching in the ticket text

    Args:
        text          : Combined subject + description text
        custom_fields : Custom fields dict from Freshdesk ticket

    Returns:
        Machine name string or 'UNKNOWN' if not found
    """
    for field_name in [
        "machine_name", "computer_name", "hostname",
        "asset_name",   "device_name",   "cf_machine_name",
        "cf_computer_name", "cf_asset_tag",
    ]:
        value = custom_fields.get(field_name)
        if value and isinstance(value, str) and len(value) > 2:
            log.debug(
                f"Machine name from custom field "
                f"'{field_name}': {value}"
            )
            return value.strip().upper()

    text_upper = text.upper()

    for pattern in COMMON_MACHINE_PATTERNS:
        matches = re.findall(pattern, text_upper)
        if matches:
            machine = matches[0].strip()
            log.debug(
                f"Machine name from text pattern: {machine}"
            )
            return machine

    return "UNKNOWN"


def _extract_app_names(text: str) -> list:
    """
    Detect software application names mentioned in the ticket.
    Helps the automation runner know which app to install.

    Args:
        text : Combined subject + description text

    Returns:
        List of detected app name strings (lowercase)
    """
    text_lower = text.lower()
    found      = []

    for app in COMMON_APP_PATTERNS:
        if app in text_lower and app not in found:
            found.append(app)

    return found


def _detect_urgency(text: str) -> str:
    """
    Detect the urgency level from keywords in ticket text.
    Supplements the Freshdesk priority field with semantic
    analysis of the ticket content.

    Args:
        text : Combined subject + description text

    Returns:
        Urgency string: 'critical', 'high', 'medium', or 'low'
    """
    text_lower = text.lower()

    for level in ["critical", "high", "medium", "low"]:
        keywords = URGENCY_KEYWORDS.get(level, [])
        if any(kw in text_lower for kw in keywords):
            return level

    return "medium"


def _parse_datetime(dt_string: str) -> str | None:
    """
    Parse a Freshdesk ISO datetime string to a readable format.
    Uses timezone-aware datetime to avoid deprecation warnings.

    Args:
        dt_string : ISO 8601 datetime string from Freshdesk

    Returns:
        Formatted datetime string or None
    """
    if not dt_string:
        return None

    try:
        dt = datetime.fromisoformat(
            dt_string.replace("Z", "+00:00")
        )
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return dt_string


def _get_ticket_age_hours(created_at: str) -> float:
    """
    Calculate how many hours old the ticket is.
    Uses timezone-aware datetime to avoid deprecation warnings.

    Args:
        created_at : Formatted datetime string from _parse_datetime()

    Returns:
        Age in hours as float, or 0.0 if cannot be calculated
    """
    if not created_at:
        return 0.0

    try:
        fmt     = "%Y-%m-%d %H:%M:%S UTC"
        created = datetime.strptime(created_at, fmt).replace(
            tzinfo=timezone.utc
        )
        now     = datetime.now(timezone.utc)
        delta   = now - created
        return round(delta.total_seconds() / 3600, 2)
    except Exception:
        return 0.0


def _get_source_name(source_code: int) -> str:
    """
    Convert a Freshdesk source code to a human-readable name.

    Args:
        source_code : Integer source code from Freshdesk API

    Returns:
        Source name string
    """
    sources = {
        1  : "email",
        2  : "portal",
        3  : "phone",
        7  : "chat",
        9  : "feedback_widget",
        10 : "outbound_email",
    }
    return sources.get(source_code, "unknown")


def _empty_ticket() -> dict:
    """
    Return a safe empty ticket dict used when parsing fails.
    Prevents the rest of the system from crashing on bad data.

    Returns:
        Dict with all required keys set to safe defaults
    """
    now_str = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    return {
        "id"               : 0,
        "subject"          : "",
        "description"      : "",
        "full_text"        : "",
        "status"           : "open",
        "status_code"      : 2,
        "priority"         : "medium",
        "priority_code"    : 2,
        "requester_id"     : None,
        "requester_email"  : "",
        "requester_name"   : "Unknown",
        "responder_id"     : None,
        "group_id"         : None,
        "created_at"       : now_str,
        "updated_at"       : now_str,
        "due_by"           : None,
        "tags"             : [],
        "custom_fields"    : {},
        "attachments"      : [],
        "has_attachment"   : False,
        "machine_name"     : "UNKNOWN",
        "mentioned_apps"   : [],
        "urgency_level"    : "medium",
        "is_first_ticket"  : True,
        "word_count"       : 0,
        "ticket_age_hours" : 0.0,
        "conversation_count": 0,
        "source"           : "unknown",
    }


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

    print("\n" + "=" * 60)
    print("TICKET PARSER TEST RUN")
    print("=" * 60)
    print(
        f"  Mode : "
        f"{'DEMO' if DEMO_MODE else 'LIVE'}"
    )
    print()

    freshdesk_tickets = [
        {
            "id"              : 1001,
            "subject"         : "Zoom not installed on my laptop",
            "description"     : (
                "<p>Hi team,</p>"
                "<p>I need <b>Zoom</b> installed on my machine "
                "PC-ICICI-0042. I have a client call in 2 hours. "
                "Please install it urgently.</p>"
                "<br>Thanks,<br>Rahul"
            ),
            "description_text": "",
            "status"          : 2,
            "priority"        : 3,
            "requester_id"    : 5001,
            "requester"       : {
                "email": "rahul.sharma@icici.com",
                "name" : "Rahul Sharma",
            },
            "responder_id"    : None,
            "group_id"        : 10,
            "created_at"      : "2024-01-15T09:30:00Z",
            "updated_at"      : "2024-01-15T09:30:00Z",
            "due_by"          : "2024-01-15T17:30:00Z",
            "tags"            : [],
            "custom_fields"   : {"cf_machine_name": "PC-ICICI-0042"},
            "attachments"     : [],
            "source"          : 2,
            "nr_of_activities": 0,
        },
        {
            "id"              : 1002,
            "subject"         : "Antivirus showing error — definitions out of date",
            "description"     : (
                "<p>My Symantec antivirus is showing a red warning. "
                "Definitions are out of date. I tried updating manually "
                "but it fails. My computer name is LAPTOP-ICICI-115.</p>"
            ),
            "description_text": "",
            "status"          : 2,
            "priority"        : 2,
            "requester_id"    : 5002,
            "requester"       : {
                "email": "priya.mehta@icici.com",
                "name" : "Priya Mehta",
            },
            "responder_id"    : None,
            "group_id"        : 10,
            "created_at"      : "2024-01-15T10:00:00Z",
            "updated_at"      : "2024-01-15T10:00:00Z",
            "due_by"          : "2024-01-16T10:00:00Z",
            "tags"            : ["antivirus"],
            "custom_fields"   : {},
            "attachments"     : [],
            "source"          : 1,
            "nr_of_activities": 0,
        },
        {
            "id"              : 1003,
            "subject"         : "Cannot connect to VPN from home — urgent",
            "description"     : (
                "<p>Since this morning I am unable to connect to VPN. "
                "Error says <b>Connection timed out</b>. "
                "I have a critical client presentation in 1 hour. "
                "Please help ASAP.</p>"
            ),
            "description_text": "",
            "status"          : 2,
            "priority"        : 3,
            "requester_id"    : 5003,
            "requester"       : {
                "email": "amit.patel@icici.com",
                "name" : "Amit Patel",
            },
            "responder_id"    : None,
            "group_id"        : 10,
            "created_at"      : "2024-01-15T08:00:00Z",
            "updated_at"      : "2024-01-15T08:00:00Z",
            "due_by"          : "2024-01-15T12:00:00Z",
            "tags"            : ["vpn", "urgent"],
            "custom_fields"   : {},
            "attachments"     : [],
            "source"          : 1,
            "nr_of_activities": 2,
        },
    ]

    demo_tickets = [
        {
            "id"              : 2001,
            "subject"         : "Please install Zoom on my laptop urgently",
            "description"     : (
                "I need Zoom installed on PC-ICICI-0042. "
                "Client call in 2 hours."
            ),
            "requester_name"  : "Rahul Sharma",
            "requester_email" : "rahul.sharma@icici.com",
            "machine_name"    : "PC-ICICI-0042",
            "mentioned_apps"  : ["zoom"],
            "urgency_level"   : "high",
        },
        {
            "id"              : 2002,
            "subject"         : "Laptop screen is flickering",
            "description"     : "Screen flickering since morning. Physical damage.",
            "requester_name"  : "Karan Malhotra",
            "requester_email" : "karan.malhotra@icici.com",
            "machine_name"    : "LAPTOP-ICICI-220",
            "mentioned_apps"  : [],
            "urgency_level"   : "medium",
        },
    ]

    print("--- Freshdesk API Ticket Parsing ---\n")
    for raw in freshdesk_tickets:
        parsed = parse_ticket(raw)
        print(
            f"  #{parsed['id']:<6} "
            f"{parsed['subject'][:40]:<42} "
            f"| {parsed['priority']:<8} "
            f"| machine: {parsed['machine_name']:<20} "
            f"| apps: {parsed['mentioned_apps']}"
        )

    print("\n--- Demo Ticket Parsing ---\n")
    for raw in demo_tickets:
        parsed = parse_ticket(raw)
        print(
            f"  #{parsed['id']:<6} "
            f"{parsed['subject'][:40]:<42} "
            f"| urgency: {parsed['urgency_level']:<10} "
            f"| machine: {parsed['machine_name']:<20} "
            f"| source: {parsed['source']}"
        )

    print("\n--- Bulk Parse Test ---")
    all_raw   = freshdesk_tickets + demo_tickets
    bulk      = parse_tickets_bulk(all_raw)
    print(f"  Input: {len(all_raw)} tickets")
    print(f"  Parsed: {len(bulk)} successfully")

    print("\n--- Edge Case: Empty input ---")
    empty_result = parse_ticket({})
    print(f"  Empty dict → id: {empty_result['id']}")

    print("\n--- Edge Case: None input ---")
    none_result = parse_ticket(None)
    print(f"  None → id: {none_result['id']}")

    print("\n--- Edge Case: HTML description ---")
    html_ticket = {
        "id"          : 9999,
        "subject"     : "Test HTML ticket",
        "description" : (
            "<p>Hello <b>team</b>,</p>"
            "<br>Please help with this &amp; that issue."
            "<ul><li>Item one</li><li>Item two</li></ul>"
        ),
        "status"      : 2,
        "priority"    : 2,
        "requester"   : {"email": "test@icici.com", "name": "Test"},
    }
    parsed = parse_ticket(html_ticket)
    print(
        f"  HTML cleaned: "
        f"'{parsed['description'][:60]}'"
    )

    print("\n" + "=" * 60)
    print("All ticket parser tests complete.")
    print("=" * 60 + "\n")