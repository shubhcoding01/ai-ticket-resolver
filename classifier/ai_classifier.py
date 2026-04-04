import os
import json
import logging
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """
You are an expert IT support ticket classifier working for a large enterprise company (ICICI Bank).
Your job is to read a support ticket and return a structured JSON classification.

You must classify every ticket into exactly one of these categories:
- app_install       : User wants software/application installed (Zoom, Chrome, MS Office, Teams, etc.)
- antivirus         : Antivirus not working, not updating, virus detected, scan failed
- password_reset    : Forgot password, account locked, password expired, MFA issues
- network           : No internet, VPN not connecting, slow network, WiFi issues
- printer           : Printer not working, unable to print, printer offline
- email_issue       : Outlook not opening, email not syncing, PST corrupt, cannot send/receive
- hardware          : Laptop slow, screen broken, keyboard not working, battery issue
- os_issue          : Windows update failed, blue screen (BSOD), system crash, OS corrupt
- access_permission : Cannot access shared drive, folder permission denied, login blocked
- other             : Anything that does not fit the above categories

Priority rules:
- high   : Production blocked, cannot work at all, data loss risk, multiple users affected
- medium : Work is difficult but partially possible, single user affected
- low    : Minor inconvenience, cosmetic issue, non-urgent request

Auto-resolve rules (can_auto_resolve: true only if ALL of these are true):
- The fix can be done remotely via a script or tool
- No physical hardware interaction is needed
- No manual investigation is needed
- Categories that CAN be auto-resolved: app_install, antivirus, password_reset, printer (basic), os_issue (basic)
- Categories that CANNOT be auto-resolved: hardware, network (complex), access_permission, other

IMPORTANT:
- Always return ONLY valid JSON. No extra text, no markdown, no explanation.
- If you are unsure, make your best guess based on the ticket content.
- The suggested_action must be a single clear sentence describing what should be done.
"""


def classify_ticket(subject: str, description: str) -> dict:
    """
    Classify a support ticket using Claude AI.

    Args:
        subject     : Ticket subject/title
        description : Full ticket description from the user

    Returns:
        dict with keys: category, priority, can_auto_resolve, suggested_action, confidence
    """

    user_message = f"""
Classify this IT support ticket:

SUBJECT: {subject}

DESCRIPTION: {description}

Return ONLY a JSON object in exactly this format:
{{
    "category": "<one of the categories listed>",
    "priority": "<high|medium|low>",
    "can_auto_resolve": <true|false>,
    "suggested_action": "<one clear sentence about what action to take>",
    "confidence": "<high|medium|low>"
}}
"""

    log.info(f"Classifying ticket — Subject: {subject[:60]}...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=SYSTEM_PROMPT
        )

        raw_text = response.content[0].text.strip()
        log.debug(f"Raw Claude response: {raw_text}")

        result = _parse_response(raw_text)
        result = _validate_result(result)

        log.info(f"Classification result: {result}")
        return result

    except Exception as e:
        log.error(f"Claude API call failed: {e}")
        return _fallback_classification(subject, description)


def _parse_response(raw_text: str) -> dict:
    """
    Safely parse the JSON response from Claude.
    Handles edge cases where Claude adds extra text around the JSON.
    """
    try:
        return json.loads(raw_text)

    except json.JSONDecodeError:
        log.warning("Direct JSON parse failed. Trying to extract JSON block...")

        start = raw_text.find("{")
        end   = raw_text.rfind("}") + 1

        if start != -1 and end > start:
            try:
                return json.loads(raw_text[start:end])
            except json.JSONDecodeError:
                pass

        log.error("Could not extract valid JSON from Claude response.")
        raise ValueError(f"Invalid JSON from Claude: {raw_text}")


def _validate_result(result: dict) -> dict:
    """
    Validate and sanitize the classification result.
    Fills in safe defaults if any field is missing or invalid.
    """

    valid_categories = [
        "app_install", "antivirus", "password_reset", "network",
        "printer", "email_issue", "hardware", "os_issue",
        "access_permission", "other"
    ]
    valid_priorities   = ["high", "medium", "low"]
    valid_confidences  = ["high", "medium", "low"]

    if result.get("category") not in valid_categories:
        log.warning(f"Invalid category '{result.get('category')}'. Defaulting to 'other'.")
        result["category"] = "other"

    if result.get("priority") not in valid_priorities:
        log.warning(f"Invalid priority '{result.get('priority')}'. Defaulting to 'medium'.")
        result["priority"] = "medium"

    if not isinstance(result.get("can_auto_resolve"), bool):
        log.warning("Invalid can_auto_resolve value. Defaulting to False.")
        result["can_auto_resolve"] = False

    if not result.get("suggested_action"):
        result["suggested_action"] = "Manual review required."

    if result.get("confidence") not in valid_confidences:
        result["confidence"] = "medium"

    return result


def _fallback_classification(subject: str, description: str) -> dict:
    """
    Keyword-based fallback classifier used when the Claude API is unavailable.
    Not as accurate as AI but ensures the system keeps running.
    """
    log.warning("Using keyword fallback classifier (Claude API unavailable).")

    text = (subject + " " + description).lower()

    category        = "other"
    can_auto_resolve = False
    priority        = "medium"

    keyword_map = {
        "app_install"       : ["install", "installation", "setup", "zoom", "teams", "chrome",
                               "office", "software", "application", "download"],
        "antivirus"         : ["antivirus", "virus", "malware", "defender", "symantec",
                               "mcafee", "scan", "threat", "infected"],
        "password_reset"    : ["password", "reset", "locked", "expired", "forgot",
                               "mfa", "otp", "login failed", "account locked"],
        "network"           : ["internet", "network", "vpn", "wifi", "wi-fi",
                               "no connection", "slow internet", "cannot connect"],
        "printer"           : ["print", "printer", "printing", "offline printer",
                               "paper jam", "cannot print"],
        "email_issue"       : ["outlook", "email", "mail", "pst", "inbox",
                               "send", "receive", "exchange"],
        "hardware"          : ["laptop", "screen", "keyboard", "mouse", "battery",
                               "slow computer", "hardware", "broken"],
        "os_issue"          : ["windows", "update", "blue screen", "bsod", "crash",
                               "restart", "os", "system error"],
        "access_permission" : ["access", "permission", "denied", "shared drive",
                               "folder", "cannot open", "unauthorized"],
    }

    auto_resolvable = {
        "app_install", "antivirus", "password_reset"
    }

    high_priority_keywords = [
        "urgent", "asap", "immediately", "production", "cannot work",
        "critical", "blocked", "emergency", "data loss"
    ]

    for cat, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            category = cat
            break

    if any(kw in text for kw in high_priority_keywords):
        priority = "high"

    if category in auto_resolvable:
        can_auto_resolve = True

    suggested_action = _get_suggested_action(category)

    return {
        "category"        : category,
        "priority"        : priority,
        "can_auto_resolve": can_auto_resolve,
        "suggested_action": suggested_action,
        "confidence"      : "low"
    }


def _get_suggested_action(category: str) -> str:
    actions = {
        "app_install"       : "Push software installation remotely via SCCM or Intune.",
        "antivirus"         : "Trigger remote antivirus update and full scan on user machine.",
        "password_reset"    : "Reset user password via Active Directory and notify user.",
        "network"           : "Check VPN config and network adapter settings on user machine.",
        "printer"           : "Restart print spooler and reinstall printer driver remotely.",
        "email_issue"       : "Rebuild Outlook profile or repair PST file remotely.",
        "hardware"          : "Schedule on-site hardware inspection with engineer.",
        "os_issue"          : "Run Windows repair tools remotely (sfc /scannow, DISM).",
        "access_permission" : "Review and update Active Directory group permissions.",
        "other"             : "Assign to engineer for manual investigation.",
    }
    return actions.get(category, "Manual review required.")


def batch_classify(tickets: list) -> list:
    """
    Classify multiple tickets at once.

    Args:
        tickets : List of dicts, each with 'id', 'subject', 'description'

    Returns:
        List of dicts with original ticket data + classification result
    """
    results = []

    for ticket in tickets:
        log.info(f"Batch classifying ticket #{ticket.get('id', 'N/A')}...")
        classification = classify_ticket(
            subject=ticket.get("subject", ""),
            description=ticket.get("description", "")
        )
        results.append({
            **ticket,
            "classification": classification
        })

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_tickets = [
        {
            "subject"    : "Zoom not installed on my laptop",
            "description": "Hi team, I need Zoom installed on my Dell laptop urgently. "
                           "I have a client call in 2 hours and it's not installed. My machine is PC-ICICI-0042."
        },
        {
            "subject"    : "Antivirus showing error and not updating",
            "description": "My Symantec antivirus is showing a red warning and says 'definitions out of date'. "
                           "I tried updating manually but it fails every time."
        },
        {
            "subject"    : "Forgot my Windows login password",
            "description": "I changed my password last week and now I cannot remember it. "
                           "My account says it's locked. Please reset urgently."
        },
        {
            "subject"    : "Cannot connect to company VPN",
            "description": "Since this morning I am unable to connect to VPN from home. "
                           "It shows 'Connection timed out'. Other colleagues are fine."
        },
    ]

    print("\n" + "="*60)
    print("AI CLASSIFIER TEST RUN")
    print("="*60 + "\n")

    for t in test_tickets:
        print(f"Subject   : {t['subject']}")
        result = classify_ticket(t["subject"], t["description"])
        print(f"Category  : {result['category']}")
        print(f"Priority  : {result['priority']}")
        print(f"Auto-fix  : {result['can_auto_resolve']}")
        print(f"Action    : {result['suggested_action']}")
        print(f"Confidence: {result['confidence']}")
        print("-" * 50)