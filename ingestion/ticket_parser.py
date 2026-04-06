import logging
import re
from datetime import datetime

log = logging.getLogger(__name__)

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
    "zoom", "teams", "microsoft teams", "ms teams",
    "chrome", "google chrome", "firefox", "edge",
    "office", "ms office", "microsoft office", "word", "excel", "powerpoint",
    "outlook", "skype", "slack", "webex",
    "adobe", "acrobat", "photoshop",
    "vpn", "cisco vpn", "anyconnect",
    "sap", "oracle", "tally",
    "antivirus", "symantec", "mcafee", "defender",
    "putty", "winscp", "notepad++", "7zip",
]

URGENCY_KEYWORDS = {
    "critical" : ["critical", "emergency", "data loss", "breach", "hacked",
                  "virus detected", "ransomware", "production down"],
    "high"     : ["urgent", "asap", "immediately", "cannot work", "blocked",
                  "meeting in", "call in", "deadline", "client call", "not working at all"],
    "medium"   : ["please help", "issue", "problem", "not working", "error",
                  "failed", "unable to"],
    "low"      : ["when possible", "not urgent", "minor", "small issue",
                  "whenever", "if possible", "low priority"],
}


def parse_ticket(raw_ticket: dict) -> dict:
    """
    Convert a raw Freshdesk API ticket response into a clean,
    normalized dictionary that the rest of the system can use.

    Args:
        raw_ticket : Raw dict from Freshdesk API response

    Returns:
        Clean normalized ticket dict
    """
    if not raw_ticket or not isinstance(raw_ticket, dict):
        log.error("parse_ticket received invalid input — expected a dict.")
        return _empty_ticket()

    try:
        ticket_id    = raw_ticket.get("id", 0)
        subject      = _clean_text(raw_ticket.get("subject", ""))
        description  = _clean_html(raw_ticket.get("description", ""))
        desc_text    = _clean_html(raw_ticket.get("description_text", description))

        full_text = f"{subject} {desc_text}"

        status_code   = raw_ticket.get("status", 2)
        priority_code = raw_ticket.get("priority", 2)

        status   = FRESHDESK_STATUS_MAP.get(status_code, "open")
        priority = FRESHDESK_PRIORITY_MAP.get(priority_code, "medium")

        requester_id    = raw_ticket.get("requester_id")
        requester_info  = raw_ticket.get("requester", {})
        requester_email = requester_info.get("email", "")
        requester_name  = requester_info.get("name", "Unknown User")

        responder_id = raw_ticket.get("responder_id")
        group_id     = raw_ticket.get("group_id")

        created_at = _parse_datetime(raw_ticket.get("created_at"))
        updated_at = _parse_datetime(raw_ticket.get("updated_at"))
        due_by     = _parse_datetime(raw_ticket.get("due_by"))

        tags              = raw_ticket.get("tags", [])
        custom_fields     = raw_ticket.get("custom_fields", {})
        attachments       = raw_ticket.get("attachments", [])
        conversation_count = raw_ticket.get("nr_of_activities", 0)

        machine_name    = _extract_machine_name(full_text, custom_fields)
        mentioned_apps  = _extract_app_names(full_text)
        urgency_level   = _detect_urgency(full_text)
        is_first_ticket = conversation_count == 0
        has_attachment  = len(attachments) > 0
        word_count      = len(desc_text.split())
        ticket_age_hrs  = _get_ticket_age_hours(created_at)

        parsed = {
            "id"               : ticket_id,
            "subject"          : subject,
            "description"      : desc_text,
            "full_text"        : full_text,
            "status"           : status,
            "status_code"      : status_code,
            "priority"         : priority,
            "priority_code"    : priority_code,
            "requester_id"     : requester_id,
            "requester_email"  : requester_email,
            "requester_name"   : requester_name,
            "responder_id"     : responder_id,
            "group_id"         : group_id,
            "created_at"       : created_at,
            "updated_at"       : updated_at,
            "due_by"           : due_by,
            "tags"             : tags,
            "custom_fields"    : custom_fields,
            "attachments"      : attachments,
            "has_attachment"   : has_attachment,
            "machine_name"     : machine_name,
            "mentioned_apps"   : mentioned_apps,
            "urgency_level"    : urgency_level,
            "is_first_ticket"  : is_first_ticket,
            "word_count"       : word_count,
            "ticket_age_hours" : ticket_age_hrs,
            "conversation_count": conversation_count,
            "source"           : _get_source_name(raw_ticket.get("source", 1)),
        }

        log.info(f"Parsed ticket #{ticket_id}: '{subject[:50]}...' "
                 f"| Status: {status} | Priority: {priority} "
                 f"| Machine: {machine_name} | Apps: {mentioned_apps}")

        return parsed

    except Exception as e:
        log.error(f"Error parsing ticket: {e}")
        log.debug(f"Raw ticket data: {raw_ticket}")
        return _empty_ticket()


def parse_tickets_bulk(raw_tickets: list) -> list:
    """
    Parse a list of raw Freshdesk tickets all at once.

    Args:
        raw_tickets : List of raw ticket dicts from Freshdesk API

    Returns:
        List of clean parsed ticket dicts
    """
    if not raw_tickets:
        log.warning("parse_tickets_bulk received an empty list.")
        return []

    log.info(f"Bulk parsing {len(raw_tickets)} tickets...")

    parsed = []
    failed = 0

    for raw in raw_tickets:
        result = parse_ticket(raw)
        if result["id"] != 0:
            parsed.append(result)
        else:
            failed += 1

    log.info(f"Bulk parse complete: {len(parsed)} success, {failed} failed.")
    return parsed


def _clean_text(text: str) -> str:
    """
    Remove extra whitespace and normalize a plain text string.
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def _clean_html(html: str) -> str:
    """
    Strip HTML tags from ticket description and return clean plain text.
    Freshdesk stores descriptions as HTML — this converts them to readable text.
    """
    if not html:
        return ""

    text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<p\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li\s*/?>', '\n- ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)

    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()

    return text


def _extract_machine_name(text: str, custom_fields: dict) -> str:
    """
    Try to extract the user's machine/computer name from:
    1. Custom fields in Freshdesk (most reliable)
    2. Pattern matching in the ticket text

    Args:
        text          : Combined subject + description text
        custom_fields : Custom fields dict from Freshdesk ticket

    Returns:
        Machine name string or 'UNKNOWN' if not found
    """
    for field_name in ["machine_name", "computer_name", "hostname",
                       "asset_name", "device_name", "cf_machine_name",
                       "cf_computer_name", "cf_asset_tag"]:
        value = custom_fields.get(field_name)
        if value and isinstance(value, str) and len(value) > 2:
            log.debug(f"Machine name from custom field '{field_name}': {value}")
            return value.strip().upper()

    text_upper = text.upper()

    for pattern in COMMON_MACHINE_PATTERNS:
        matches = re.findall(pattern, text_upper)
        if matches:
            machine = matches[0].strip()
            log.debug(f"Machine name from text pattern: {machine}")
            return machine

    return "UNKNOWN"


def _extract_app_names(text: str) -> list:
    """
    Detect any software application names mentioned in the ticket text.
    Helps automation runner understand which app to install or fix.

    Args:
        text : Combined subject + description text

    Returns:
        List of detected app name strings (lowercase)
    """
    text_lower = text.lower()
    found = []

    for app in COMMON_APP_PATTERNS:
        if app in text_lower and app not in found:
            found.append(app)

    return found


def _detect_urgency(text: str) -> str:
    """
    Detect the urgency level from keywords in the ticket text.
    This supplements the Freshdesk priority field with semantic analysis.

    Args:
        text : Combined subject + description text

    Returns:
        Urgency level string: 'critical', 'high', 'medium', or 'low'
    """
    text_lower = text.lower()

    for level in ["critical", "high", "medium", "low"]:
        keywords = URGENCY_KEYWORDS.get(level, [])
        if any(kw in text_lower for kw in keywords):
            return level

    return "medium"


def _parse_datetime(dt_string: str) -> str | None:
    """
    Parse Freshdesk ISO datetime string to a readable format.

    Args:
        dt_string : ISO 8601 datetime string from Freshdesk

    Returns:
        Formatted datetime string or None
    """
    if not dt_string:
        return None

    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return dt_string


def _get_ticket_age_hours(created_at: str) -> float:
    """
    Calculate how many hours old the ticket is.

    Args:
        created_at : Formatted datetime string from _parse_datetime()

    Returns:
        Age in hours as float, or 0.0 if cannot be calculated
    """
    if not created_at:
        return 0.0

    try:
        fmt = "%Y-%m-%d %H:%M:%S UTC"
        created = datetime.strptime(created_at, fmt)
        now     = datetime.utcnow()
        delta   = now - created
        return round(delta.total_seconds() / 3600, 2)
    except Exception:
        return 0.0


def _get_source_name(source_code: int) -> str:
    """
    Convert Freshdesk source code to human readable name.
    """
    sources = {
        1: "email",
        2: "portal",
        3: "phone",
        7: "chat",
        9: "feedback_widget",
        10: "outbound_email",
    }
    return sources.get(source_code, "unknown")


def _empty_ticket() -> dict:
    """
    Return a safe empty ticket dict used when parsing fails.
    Prevents the rest of the system from crashing on bad data.
    """
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
        "created_at"       : None,
        "updated_at"       : None,
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    sample_tickets = [
        {
            "id"              : 1001,
            "subject"         : "Zoom not installed on my laptop",
            "description"     : "<p>Hi team,</p><p>I need <b>Zoom</b> installed on my machine "
                                "PC-ICICI-0042. I have a client call in 2 hours. "
                                "Please install it urgently.</p><br>Thanks,<br>Rahul",
            "description_text": "",
            "status"          : 2,
            "priority"        : 3,
            "requester_id"    : 5001,
            "requester"       : {"email": "rahul.sharma@icici.com", "name": "Rahul Sharma"},
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
            "subject"         : "Antivirus showing error - definitions out of date",
            "description"     : "<p>My Symantec antivirus is showing a red warning. "
                                "Definitions are out of date. I tried updating manually "
                                "but it fails. My computer name is LAPTOP-ICICI-115.</p>",
            "description_text": "",
            "status"          : 2,
            "priority"        : 2,
            "requester_id"    : 5002,
            "requester"       : {"email": "priya.mehta@icici.com", "name": "Priya Mehta"},
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
            "subject"         : "Cannot connect to VPN from home - urgent",
            "description"     : "<p>Since this morning I am unable to connect to VPN. "
                                "Error says <b>Connection timed out</b>. "
                                "I have a critical client presentation in 1 hour. "
                                "All my files are on the network drive. Please help ASAP.</p>",
            "description_text": "",
            "status"          : 2,
            "priority"        : 3,
            "requester_id"    : 5003,
            "requester"       : {"email": "amit.patel@icici.com", "name": "Amit Patel"},
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

    print("\n" + "=" * 60)
    print("TICKET PARSER TEST RUN")
    print("=" * 60 + "\n")

    for raw in sample_tickets:
        parsed = parse_ticket(raw)

        print(f"Ticket ID       : {parsed['id']}")
        print(f"Subject         : {parsed['subject']}")
        print(f"Description     : {parsed['description'][:80]}...")
        print(f"Status          : {parsed['status']}")
        print(f"Priority        : {parsed['priority']}")
        print(f"Requester       : {parsed['requester_name']} ({parsed['requester_email']})")
        print(f"Machine Name    : {parsed['machine_name']}")
        print(f"Mentioned Apps  : {parsed['mentioned_apps']}")
        print(f"Urgency Level   : {parsed['urgency_level']}")
        print(f"Has Attachment  : {parsed['has_attachment']}")
        print(f"Ticket Age (hrs): {parsed['ticket_age_hours']}")
        print(f"Source          : {parsed['source']}")
        print(f"Word Count      : {parsed['word_count']}")
        print("-" * 60)

    print("\nBulk parse test:")
    bulk_results = parse_tickets_bulk(sample_tickets)
    print(f"Parsed {len(bulk_results)} tickets successfully.")
    