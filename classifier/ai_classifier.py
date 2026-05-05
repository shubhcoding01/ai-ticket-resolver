# import os
# import json
# import logging
# from anthropic import Anthropic
# from dotenv import load_dotenv

# load_dotenv()

# log = logging.getLogger(__name__)

# client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# SYSTEM_PROMPT = """
# You are an expert IT support ticket classifier working for a large enterprise company (ICICI Bank).
# Your job is to read a support ticket and return a structured JSON classification.

# You must classify every ticket into exactly one of these categories:
# - app_install       : User wants software/application installed (Zoom, Chrome, MS Office, Teams, etc.)
# - antivirus         : Antivirus not working, not updating, virus detected, scan failed
# - password_reset    : Forgot password, account locked, password expired, MFA issues
# - network           : No internet, VPN not connecting, slow network, WiFi issues
# - printer           : Printer not working, unable to print, printer offline
# - email_issue       : Outlook not opening, email not syncing, PST corrupt, cannot send/receive
# - hardware          : Laptop slow, screen broken, keyboard not working, battery issue
# - os_issue          : Windows update failed, blue screen (BSOD), system crash, OS corrupt
# - access_permission : Cannot access shared drive, folder permission denied, login blocked
# - other             : Anything that does not fit the above categories

# Priority rules:
# - high   : Production blocked, cannot work at all, data loss risk, multiple users affected
# - medium : Work is difficult but partially possible, single user affected
# - low    : Minor inconvenience, cosmetic issue, non-urgent request

# Auto-resolve rules (can_auto_resolve: true only if ALL of these are true):
# - The fix can be done remotely via a script or tool
# - No physical hardware interaction is needed
# - No manual investigation is needed
# - Categories that CAN be auto-resolved: app_install, antivirus, password_reset, printer (basic), os_issue (basic)
# - Categories that CANNOT be auto-resolved: hardware, network (complex), access_permission, other

# IMPORTANT:
# - Always return ONLY valid JSON. No extra text, no markdown, no explanation.
# - If you are unsure, make your best guess based on the ticket content.
# - The suggested_action must be a single clear sentence describing what should be done.
# """


# def classify_ticket(subject: str, description: str) -> dict:
#     """
#     Classify a support ticket using Claude AI.

#     Args:
#         subject     : Ticket subject/title
#         description : Full ticket description from the user

#     Returns:
#         dict with keys: category, priority, can_auto_resolve, suggested_action, confidence
#     """

#     user_message = f"""
# Classify this IT support ticket:

# SUBJECT: {subject}

# DESCRIPTION: {description}

# Return ONLY a JSON object in exactly this format:
# {{
#     "category": "<one of the categories listed>",
#     "priority": "<high|medium|low>",
#     "can_auto_resolve": <true|false>,
#     "suggested_action": "<one clear sentence about what action to take>",
#     "confidence": "<high|medium|low>"
# }}
# """

#     log.info(f"Classifying ticket — Subject: {subject[:60]}...")

#     try:
#         response = client.messages.create(
#             model="claude-sonnet-4-20250514",
#             max_tokens=500,
#             messages=[
#                 {"role": "user", "content": user_message}
#             ],
#             system=SYSTEM_PROMPT
#         )

#         raw_text = response.content[0].text.strip()
#         log.debug(f"Raw Claude response: {raw_text}")

#         result = _parse_response(raw_text)
#         result = _validate_result(result)

#         log.info(f"Classification result: {result}")
#         return result

#     except Exception as e:
#         log.error(f"Claude API call failed: {e}")
#         return _fallback_classification(subject, description)


# def _parse_response(raw_text: str) -> dict:
#     """
#     Safely parse the JSON response from Claude.
#     Handles edge cases where Claude adds extra text around the JSON.
#     """
#     try:
#         return json.loads(raw_text)

#     except json.JSONDecodeError:
#         log.warning("Direct JSON parse failed. Trying to extract JSON block...")

#         start = raw_text.find("{")
#         end   = raw_text.rfind("}") + 1

#         if start != -1 and end > start:
#             try:
#                 return json.loads(raw_text[start:end])
#             except json.JSONDecodeError:
#                 pass

#         log.error("Could not extract valid JSON from Claude response.")
#         raise ValueError(f"Invalid JSON from Claude: {raw_text}")


# def _validate_result(result: dict) -> dict:
#     """
#     Validate and sanitize the classification result.
#     Fills in safe defaults if any field is missing or invalid.
#     """

#     valid_categories = [
#         "app_install", "antivirus", "password_reset", "network",
#         "printer", "email_issue", "hardware", "os_issue",
#         "access_permission", "other"
#     ]
#     valid_priorities   = ["high", "medium", "low"]
#     valid_confidences  = ["high", "medium", "low"]

#     if result.get("category") not in valid_categories:
#         log.warning(f"Invalid category '{result.get('category')}'. Defaulting to 'other'.")
#         result["category"] = "other"

#     if result.get("priority") not in valid_priorities:
#         log.warning(f"Invalid priority '{result.get('priority')}'. Defaulting to 'medium'.")
#         result["priority"] = "medium"

#     if not isinstance(result.get("can_auto_resolve"), bool):
#         log.warning("Invalid can_auto_resolve value. Defaulting to False.")
#         result["can_auto_resolve"] = False

#     if not result.get("suggested_action"):
#         result["suggested_action"] = "Manual review required."

#     if result.get("confidence") not in valid_confidences:
#         result["confidence"] = "medium"

#     return result


# def _fallback_classification(subject: str, description: str) -> dict:
#     """
#     Keyword-based fallback classifier used when the Claude API is unavailable.
#     Not as accurate as AI but ensures the system keeps running.
#     """
#     log.warning("Using keyword fallback classifier (Claude API unavailable).")

#     text = (subject + " " + description).lower()

#     category        = "other"
#     can_auto_resolve = False
#     priority        = "medium"

#     keyword_map = {
#         "app_install"       : ["install", "installation", "setup", "zoom", "teams", "chrome",
#                                "office", "software", "application", "download"],
#         "antivirus"         : ["antivirus", "virus", "malware", "defender", "symantec",
#                                "mcafee", "scan", "threat", "infected"],
#         "password_reset"    : ["password", "reset", "locked", "expired", "forgot",
#                                "mfa", "otp", "login failed", "account locked"],
#         "network"           : ["internet", "network", "vpn", "wifi", "wi-fi",
#                                "no connection", "slow internet", "cannot connect"],
#         "printer"           : ["print", "printer", "printing", "offline printer",
#                                "paper jam", "cannot print"],
#         "email_issue"       : ["outlook", "email", "mail", "pst", "inbox",
#                                "send", "receive", "exchange"],
#         "hardware"          : ["laptop", "screen", "keyboard", "mouse", "battery",
#                                "slow computer", "hardware", "broken"],
#         "os_issue"          : ["windows", "update", "blue screen", "bsod", "crash",
#                                "restart", "os", "system error"],
#         "access_permission" : ["access", "permission", "denied", "shared drive",
#                                "folder", "cannot open", "unauthorized"],
#     }

#     auto_resolvable = {
#         "app_install", "antivirus", "password_reset"
#     }

#     high_priority_keywords = [
#         "urgent", "asap", "immediately", "production", "cannot work",
#         "critical", "blocked", "emergency", "data loss"
#     ]

#     for cat, keywords in keyword_map.items():
#         if any(kw in text for kw in keywords):
#             category = cat
#             break

#     if any(kw in text for kw in high_priority_keywords):
#         priority = "high"

#     if category in auto_resolvable:
#         can_auto_resolve = True

#     suggested_action = _get_suggested_action(category)

#     return {
#         "category"        : category,
#         "priority"        : priority,
#         "can_auto_resolve": can_auto_resolve,
#         "suggested_action": suggested_action,
#         "confidence"      : "low"
#     }


# def _get_suggested_action(category: str) -> str:
#     actions = {
#         "app_install"       : "Push software installation remotely via SCCM or Intune.",
#         "antivirus"         : "Trigger remote antivirus update and full scan on user machine.",
#         "password_reset"    : "Reset user password via Active Directory and notify user.",
#         "network"           : "Check VPN config and network adapter settings on user machine.",
#         "printer"           : "Restart print spooler and reinstall printer driver remotely.",
#         "email_issue"       : "Rebuild Outlook profile or repair PST file remotely.",
#         "hardware"          : "Schedule on-site hardware inspection with engineer.",
#         "os_issue"          : "Run Windows repair tools remotely (sfc /scannow, DISM).",
#         "access_permission" : "Review and update Active Directory group permissions.",
#         "other"             : "Assign to engineer for manual investigation.",
#     }
#     return actions.get(category, "Manual review required.")


# def batch_classify(tickets: list) -> list:
#     """
#     Classify multiple tickets at once.

#     Args:
#         tickets : List of dicts, each with 'id', 'subject', 'description'

#     Returns:
#         List of dicts with original ticket data + classification result
#     """
#     results = []

#     for ticket in tickets:
#         log.info(f"Batch classifying ticket #{ticket.get('id', 'N/A')}...")
#         classification = classify_ticket(
#             subject=ticket.get("subject", ""),
#             description=ticket.get("description", "")
#         )
#         results.append({
#             **ticket,
#             "classification": classification
#         })

#     return results


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)

#     test_tickets = [
#         {
#             "subject"    : "Zoom not installed on my laptop",
#             "description": "Hi team, I need Zoom installed on my Dell laptop urgently. "
#                            "I have a client call in 2 hours and it's not installed. My machine is PC-ICICI-0042."
#         },
#         {
#             "subject"    : "Antivirus showing error and not updating",
#             "description": "My Symantec antivirus is showing a red warning and says 'definitions out of date'. "
#                            "I tried updating manually but it fails every time."
#         },
#         {
#             "subject"    : "Forgot my Windows login password",
#             "description": "I changed my password last week and now I cannot remember it. "
#                            "My account says it's locked. Please reset urgently."
#         },
#         {
#             "subject"    : "Cannot connect to company VPN",
#             "description": "Since this morning I am unable to connect to VPN from home. "
#                            "It shows 'Connection timed out'. Other colleagues are fine."
#         },
#     ]

#     print("\n" + "="*60)
#     print("AI CLASSIFIER TEST RUN")
#     print("="*60 + "\n")

#     for t in test_tickets:
#         print(f"Subject   : {t['subject']}")
#         result = classify_ticket(t["subject"], t["description"])
#         print(f"Category  : {result['category']}")
#         print(f"Priority  : {result['priority']}")
#         print(f"Auto-fix  : {result['can_auto_resolve']}")
#         print(f"Action    : {result['suggested_action']}")
#         print(f"Confidence: {result['confidence']}")
#         print("-" * 50)


import os
import json
import logging
from dotenv import load_dotenv

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE        = os.getenv("DEMO_MODE",        "false").strip().lower() == "true"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

client = None

if not DEMO_MODE and ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "DEMO_KEY_NOT_REAL":
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        log.info("Anthropic client initialized successfully.")
    except Exception as e:
        log.warning(f"Failed to initialize Anthropic client: {e}")
        log.warning("Falling back to rule-based classifier.")
        client = None
else:
    if DEMO_MODE:
        log.info("DEMO MODE — Anthropic client skipped. Using rule-based classifier.")
    else:
        log.warning("ANTHROPIC_API_KEY not set. Using rule-based classifier.")


SYSTEM_PROMPT = """
You are an expert IT support ticket classifier working for
a large enterprise company (ICICI Bank).
Your job is to read a support ticket and return a structured
JSON classification.

You must classify every ticket into exactly one of these categories:
- app_install       : User wants software/application installed
                      (Zoom, Chrome, MS Office, Teams, etc.)
- antivirus         : Antivirus not working, not updating,
                      virus detected, scan failed
- password_reset    : Forgot password, account locked,
                      password expired, MFA issues
- network           : No internet, VPN not connecting,
                      slow network, WiFi issues
- printer           : Printer not working, unable to print,
                      printer offline
- email_issue       : Outlook not opening, email not syncing,
                      PST corrupt, cannot send/receive
- hardware          : Laptop slow, screen broken,
                      keyboard not working, battery issue
- os_issue          : Windows update failed, blue screen (BSOD),
                      system crash, OS corrupt
- access_permission : Cannot access shared drive,
                      folder permission denied, login blocked
- other             : Anything that does not fit above categories

Priority rules:
- high   : Production blocked, cannot work at all,
           data loss risk, multiple users affected
- medium : Work is difficult but partially possible,
           single user affected
- low    : Minor inconvenience, cosmetic issue,
           non-urgent request

Auto-resolve rules (can_auto_resolve: true ONLY if ALL true):
- The fix can be done remotely via a script or tool
- No physical hardware interaction is needed
- No manual investigation is needed
- CAN be auto-resolved: app_install, antivirus, password_reset,
                        printer (basic), os_issue (basic)
- CANNOT be auto-resolved: hardware, network, access_permission,
                            other

IMPORTANT:
- Always return ONLY valid JSON. No extra text. No markdown.
- The suggested_action must be one clear sentence.
- confidence: high if very certain, medium if likely,
              low if uncertain
"""


DEMO_CLASSIFICATION_MAP = {
    "zoom"             : {
        "category"        : "app_install",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Push Zoom installation remotely via SCCM or Intune.",
        "confidence"      : "high",
    },
    "teams"            : {
        "category"        : "app_install",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Deploy Microsoft Teams via Intune app catalog.",
        "confidence"      : "high",
    },
    "microsoft teams"  : {
        "category"        : "app_install",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Deploy Microsoft Teams via Intune app catalog.",
        "confidence"      : "high",
    },
    "chrome"           : {
        "category"        : "app_install",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Install Google Chrome via winget remotely.",
        "confidence"      : "high",
    },
    "install"          : {
        "category"        : "app_install",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Push software installation remotely via SCCM or Intune.",
        "confidence"      : "medium",
    },
    "antivirus"        : {
        "category"        : "antivirus",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Trigger remote antivirus update and full scan.",
        "confidence"      : "high",
    },
    "virus"            : {
        "category"        : "antivirus",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Trigger remote antivirus scan and quarantine threats.",
        "confidence"      : "high",
    },
    "symantec"         : {
        "category"        : "antivirus",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Update Symantec definitions via SEPM and run full scan.",
        "confidence"      : "high",
    },
    "defender"         : {
        "category"        : "antivirus",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Update Windows Defender definitions via PowerShell remotely.",
        "confidence"      : "high",
    },
    "password"         : {
        "category"        : "password_reset",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Reset user password via Active Directory and notify user.",
        "confidence"      : "high",
    },
    "locked"           : {
        "category"        : "password_reset",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Unlock AD account and reset password for user.",
        "confidence"      : "high",
    },
    "forgot"           : {
        "category"        : "password_reset",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Reset user password via Active Directory and notify user.",
        "confidence"      : "high",
    },
    "vpn"              : {
        "category"        : "network",
        "priority"        : "high",
        "can_auto_resolve": False,
        "suggested_action": "Check VPN config and network adapter settings on user machine.",
        "confidence"      : "high",
    },
    "internet"         : {
        "category"        : "network",
        "priority"        : "high",
        "can_auto_resolve": False,
        "suggested_action": "Diagnose network connectivity and reset adapter remotely.",
        "confidence"      : "medium",
    },
    "network"          : {
        "category"        : "network",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Check network configuration and escalate to network team.",
        "confidence"      : "medium",
    },
    "printer"          : {
        "category"        : "printer",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Restart print spooler and clear print queue remotely.",
        "confidence"      : "high",
    },
    "print"            : {
        "category"        : "printer",
        "priority"        : "low",
        "can_auto_resolve": True,
        "suggested_action": "Restart print spooler and reinstall printer driver remotely.",
        "confidence"      : "medium",
    },
    "outlook"          : {
        "category"        : "email_issue",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Rebuild Outlook profile or repair PST file remotely.",
        "confidence"      : "high",
    },
    "email"            : {
        "category"        : "email_issue",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Check Exchange connectivity and rebuild Outlook profile.",
        "confidence"      : "medium",
    },
    "pst"              : {
        "category"        : "email_issue",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Run scanpst.exe remotely to repair corrupt PST file.",
        "confidence"      : "high",
    },
    "screen"           : {
        "category"        : "hardware",
        "priority"        : "high",
        "can_auto_resolve": False,
        "suggested_action": "Schedule on-site hardware inspection with engineer.",
        "confidence"      : "high",
    },
    "flickering"       : {
        "category"        : "hardware",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Schedule on-site display inspection with engineer.",
        "confidence"      : "high",
    },
    "keyboard"         : {
        "category"        : "hardware",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Schedule on-site hardware replacement with engineer.",
        "confidence"      : "high",
    },
    "battery"          : {
        "category"        : "hardware",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Schedule on-site battery replacement with engineer.",
        "confidence"      : "high",
    },
    "hardware"         : {
        "category"        : "hardware",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Schedule on-site hardware inspection with engineer.",
        "confidence"      : "medium",
    },
    "windows update"   : {
        "category"        : "os_issue",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Clear Windows Update cache and run repair remotely.",
        "confidence"      : "high",
    },
    "update"           : {
        "category"        : "os_issue",
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": "Run Windows Update troubleshooter and repair remotely.",
        "confidence"      : "medium",
    },
    "blue screen"      : {
        "category"        : "os_issue",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Check event logs and run sfc /scannow and DISM remotely.",
        "confidence"      : "high",
    },
    "bsod"             : {
        "category"        : "os_issue",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Run sfc /scannow and DISM repair remotely, check drivers.",
        "confidence"      : "high",
    },
    "crash"            : {
        "category"        : "os_issue",
        "priority"        : "high",
        "can_auto_resolve": True,
        "suggested_action": "Check crash dump and run Windows repair tools remotely.",
        "confidence"      : "medium",
    },
    "access"           : {
        "category"        : "access_permission",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Review AD group memberships and update folder permissions.",
        "confidence"      : "medium",
    },
    "permission"       : {
        "category"        : "access_permission",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Review and update Active Directory group permissions.",
        "confidence"      : "high",
    },
    "denied"           : {
        "category"        : "access_permission",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Grant appropriate AD permissions for the requested resource.",
        "confidence"      : "high",
    },
    "shared drive"     : {
        "category"        : "access_permission",
        "priority"        : "medium",
        "can_auto_resolve": False,
        "suggested_action": "Review shared drive permissions in Active Directory.",
        "confidence"      : "high",
    },
}


def classify_ticket(
    subject        : str,
    description    : str,
    ticket_id      : int = 0,
    machine_name   : str = "UNKNOWN",
    requester_name : str = "User",
) -> dict:
    """
    Classify a support ticket using Claude AI.
    In demo mode uses the rule-based classifier instead.
    Falls back to rule-based classifier if Claude API fails.

    Args:
        subject        : Ticket subject / title
        description    : Full ticket description from the user
        ticket_id      : Freshdesk ticket ID (used for logging)
        machine_name   : User machine name (optional context)
        requester_name : Requester name (optional context)

    Returns:
        Dict with keys:
            category, priority, can_auto_resolve,
            suggested_action, confidence
    """
    log.info(
        f"Classifying ticket #{ticket_id}: "
        f"'{subject[:60]}...'"
    )

    if DEMO_MODE or client is None:
        if DEMO_MODE:
            log.info(
                f"[DEMO] Using rule-based classifier "
                f"for ticket #{ticket_id}"
            )
        else:
            log.warning(
                "Claude client unavailable — "
                "using rule-based classifier."
            )
        return _fallback_classification(subject, description)

    from classifier.prompts import (
        get_system_prompt,
        build_classification_prompt,
    )

    try:
        system  = get_system_prompt()
        message = build_classification_prompt(
            subject        = subject,
            description    = description,
            ticket_id      = ticket_id,
            machine_name   = machine_name,
            requester_name = requester_name,
        )
    except ImportError:
        system  = SYSTEM_PROMPT
        message = (
            f"Classify this IT support ticket:\n\n"
            f"SUBJECT: {subject}\n\n"
            f"DESCRIPTION: {description}\n\n"
            f"Return ONLY valid JSON with keys: "
            f"category, priority, can_auto_resolve, "
            f"suggested_action, confidence"
        )

    try:
        response = client.messages.create(
            model      = os.getenv(
                "CLAUDE_MODEL",
                "claude-sonnet-4-20250514"
            ),
            max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", 500)),
            system     = system,
            messages   = [
                {"role": "user", "content": message}
            ],
        )

        raw_text = response.content[0].text.strip()
        log.debug(f"Raw Claude response: {raw_text}")

        result = _parse_response(raw_text)
        result = _validate_result(result)

        log.info(
            f"Claude classification — "
            f"category: {result['category']}, "
            f"priority: {result['priority']}, "
            f"auto: {result['can_auto_resolve']}, "
            f"confidence: {result['confidence']}"
        )

        return result

    except Exception as e:
        log.error(f"Claude API call failed: {e}")
        log.warning("Falling back to rule-based classifier...")
        return _fallback_classification(subject, description)


def _parse_response(raw_text: str) -> dict:
    """
    Safely parse the JSON response from Claude.
    Handles edge cases where Claude wraps JSON in markdown
    or adds extra explanation text around it.

    Args:
        raw_text : Raw string response from Claude API

    Returns:
        Parsed dict

    Raises:
        ValueError if no valid JSON can be extracted
    """
    try:
        return json.loads(raw_text)

    except json.JSONDecodeError:
        log.warning(
            "Direct JSON parse failed. "
            "Trying to extract JSON block..."
        )

        cleaned = raw_text
        for marker in ["```json", "```JSON", "```"]:
            cleaned = cleaned.replace(marker, "")
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        start = raw_text.find("{")
        end   = raw_text.rfind("}") + 1

        if start != -1 and end > start:
            try:
                return json.loads(raw_text[start:end])
            except json.JSONDecodeError:
                pass

        log.error(
            "Could not extract valid JSON from Claude response."
        )
        raise ValueError(
            f"Invalid JSON from Claude: {raw_text}"
        )


def _validate_result(result: dict) -> dict:
    """
    Validate and sanitize the classification result.
    Fills in safe defaults if any field is missing or invalid.
    Ensures the system never crashes due to bad AI output.

    Args:
        result : Raw parsed dict from Claude response

    Returns:
        Validated and sanitized dict
    """
    valid_categories = [
        "app_install", "antivirus", "password_reset",
        "network", "printer", "email_issue", "hardware",
        "os_issue", "access_permission", "other",
    ]
    valid_priorities  = ["high", "medium", "low", "urgent"]
    valid_confidences = ["high", "medium", "low"]

    if result.get("category") not in valid_categories:
        log.warning(
            f"Invalid category '{result.get('category')}'. "
            "Defaulting to 'other'."
        )
        result["category"] = "other"

    priority = result.get("priority", "medium")
    if priority == "urgent":
        priority = "high"
    if priority not in valid_priorities:
        log.warning(
            f"Invalid priority '{result.get('priority')}'. "
            "Defaulting to 'medium'."
        )
        priority = "medium"
    result["priority"] = priority

    if not isinstance(result.get("can_auto_resolve"), bool):
        val = str(result.get("can_auto_resolve", "")).lower()
        if val in ("true", "yes", "1"):
            result["can_auto_resolve"] = True
        else:
            log.warning(
                "Invalid can_auto_resolve. Defaulting to False."
            )
            result["can_auto_resolve"] = False

    if not result.get("suggested_action", "").strip():
        result["suggested_action"] = (
            _get_suggested_action(result["category"])
        )

    if result.get("confidence") not in valid_confidences:
        result["confidence"] = "medium"

    hardware_cats = ["hardware", "access_permission", "other"]
    if result["category"] in hardware_cats:
        result["can_auto_resolve"] = False

    return result


def _fallback_classification(
    subject    : str,
    description: str,
) -> dict:
    """
    Rule-based fallback classifier.
    Used when DEMO_MODE=true or when the Claude API is unavailable.
    Uses DEMO_CLASSIFICATION_MAP for accurate keyword-based matching,
    then falls back to the full category_rules classifier.

    Args:
        subject     : Ticket subject
        description : Ticket description

    Returns:
        Classification result dict
    """
    text = f"{subject} {description}".lower()

    for keyword, result in DEMO_CLASSIFICATION_MAP.items():
        if keyword in text:
            log.info(
                f"Demo map match on keyword '{keyword}' "
                f"→ category: {result['category']}"
            )
            return dict(result)

    try:
        from classifier.category_rules import classify_by_rules
        log.info("Using full rule-based classifier...")
        result = classify_by_rules(subject, description)
        return {
            "category"        : result.get("category",         "other"),
            "priority"        : result.get("priority",         "medium"),
            "can_auto_resolve": result.get("can_auto_resolve", False),
            "suggested_action": result.get("suggested_action", "Manual review required."),
            "confidence"      : result.get("confidence",       "low"),
        }

    except Exception as e:
        log.warning(
            f"category_rules import failed: {e}. "
            "Using minimal fallback."
        )
        return {
            "category"        : "other",
            "priority"        : "medium",
            "can_auto_resolve": False,
            "suggested_action": "Manual review required.",
            "confidence"      : "low",
        }


def _get_suggested_action(category: str) -> str:
    """
    Return a default suggested action for a given category.
    Used as fallback when Claude does not provide one.

    Args:
        category : Ticket category string

    Returns:
        Suggested action string
    """
    actions = {
        "app_install"       : (
            "Push software installation remotely "
            "via SCCM or Intune."
        ),
        "antivirus"         : (
            "Trigger remote antivirus update "
            "and full scan on user machine."
        ),
        "password_reset"    : (
            "Reset user password via Active Directory "
            "and notify user."
        ),
        "network"           : (
            "Check VPN config and network adapter "
            "settings on user machine."
        ),
        "printer"           : (
            "Restart print spooler and reinstall "
            "printer driver remotely."
        ),
        "email_issue"       : (
            "Rebuild Outlook profile or repair "
            "PST file remotely."
        ),
        "hardware"          : (
            "Schedule on-site hardware inspection "
            "with engineer."
        ),
        "os_issue"          : (
            "Run Windows repair tools remotely "
            "(sfc /scannow, DISM)."
        ),
        "access_permission" : (
            "Review and update Active Directory "
            "group permissions."
        ),
        "other"             : (
            "Assign to engineer for manual investigation."
        ),
    }
    return actions.get(category, "Manual review required.")


def batch_classify(tickets: list) -> list:
    """
    Classify multiple tickets at once.
    Processes each ticket sequentially and returns results
    in the same order as the input list.

    Args:
        tickets : List of dicts with 'id', 'subject', 'description'

    Returns:
        List of dicts — original ticket data + 'classification' key
    """
    if not tickets:
        log.info("batch_classify received empty ticket list.")
        return []

    results = []
    log.info(f"Batch classifying {len(tickets)} ticket(s)...")

    for ticket in tickets:
        ticket_id = ticket.get("id", "N/A")
        log.info(f"Batch classifying ticket #{ticket_id}...")

        try:
            classification = classify_ticket(
                subject        = ticket.get("subject",      ""),
                description    = ticket.get("description",  ""),
                ticket_id      = ticket.get("id",           0),
                machine_name   = ticket.get("machine_name", "UNKNOWN"),
                requester_name = ticket.get("requester_name", "User"),
            )
        except Exception as e:
            log.error(
                f"Failed to classify ticket #{ticket_id}: {e}"
            )
            classification = {
                "category"        : "other",
                "priority"        : "medium",
                "can_auto_resolve": False,
                "suggested_action": "Classification failed — manual review.",
                "confidence"      : "low",
            }

        results.append({
            **ticket,
            "classification": classification,
        })

    log.info(f"Batch classification complete — {len(results)} results.")
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("AI CLASSIFIER TEST RUN")
    print("=" * 60)
    print(
        f"  Mode   : "
        f"{'DEMO (rule-based)' if DEMO_MODE or client is None else 'LIVE (Claude API)'}"
    )
    print(
        f"  API Key: "
        f"{'Not set / demo key' if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == 'DEMO_KEY_NOT_REAL' else 'Set ✓'}"
    )
    print()

    test_tickets = [
        {
            "id"           : 1001,
            "subject"      : "Zoom not installed on my laptop",
            "description"  : (
                "Hi team, I need Zoom installed on my Dell laptop urgently. "
                "I have a client call in 2 hours and it is not installed. "
                "My machine is PC-ICICI-0042."
            ),
            "machine_name" : "PC-ICICI-0042",
        },
        {
            "id"           : 1002,
            "subject"      : "Antivirus showing error and not updating",
            "description"  : (
                "My Symantec antivirus is showing a red warning and says "
                "definitions out of date. I tried updating manually but "
                "it fails every time."
            ),
            "machine_name" : "LAPTOP-ICICI-115",
        },
        {
            "id"           : 1003,
            "subject"      : "Forgot my Windows login password",
            "description"  : (
                "I changed my password last week and now I cannot remember it. "
                "My account says it is locked. Please reset urgently."
            ),
            "machine_name" : "PC-ICICI-0099",
        },
        {
            "id"           : 1004,
            "subject"      : "Cannot connect to company VPN",
            "description"  : (
                "Since this morning I am unable to connect to VPN from home. "
                "It shows Connection timed out. Other colleagues are fine."
            ),
            "machine_name" : "LAPTOP-ICICI-088",
        },
        {
            "id"           : 1005,
            "subject"      : "Laptop screen is flickering badly",
            "description"  : (
                "My laptop screen has been flickering continuously. "
                "Sometimes it goes blank. I think the display is damaged."
            ),
            "machine_name" : "LAPTOP-ICICI-220",
        },
        {
            "id"           : 1006,
            "subject"      : "Windows update failed with error 0x80070002",
            "description"  : (
                "My Windows 10 update keeps failing with error 0x80070002. "
                "I tried the troubleshooter but it did not help. "
                "Machine: PC-ICICI-0077."
            ),
            "machine_name" : "PC-ICICI-0077",
        },
        {
            "id"           : 1007,
            "subject"      : "Cannot access shared Finance drive",
            "description"  : (
                "Getting permission denied when opening the Finance drive. "
                "I had access last week. Need it urgently for month-end."
            ),
            "machine_name" : "PC-ICICI-0033",
        },
    ]

    print(
        f"  {'#':<6} "
        f"{'SUBJECT':<40} "
        f"{'CATEGORY':<18} "
        f"{'PRI':<8} "
        f"{'AUTO':<7} "
        f"{'CONF'}"
    )
    print(
        f"  {'-'*6} "
        f"{'-'*40} "
        f"{'-'*18} "
        f"{'-'*8} "
        f"{'-'*7} "
        f"{'-'*6}"
    )

    for t in test_tickets:
        result = classify_ticket(
            subject        = t["subject"],
            description    = t["description"],
            ticket_id      = t["id"],
            machine_name   = t.get("machine_name", "UNKNOWN"),
        )
        subject_short = t["subject"][:38]
        auto_icon     = "✓" if result["can_auto_resolve"] else "✗"
        print(
            f"  {t['id']:<6} "
            f"{subject_short:<40} "
            f"{result['category']:<18} "
            f"{result['priority']:<8} "
            f"{auto_icon:<7} "
            f"{result['confidence']}"
        )

    print()
    print("--- Batch classify test ---")
    batch_results = batch_classify(test_tickets[:3])
    print(f"Batch classified {len(batch_results)} tickets.")
    for r in batch_results:
        print(
            f"  Ticket #{r['id']} → "
            f"{r['classification']['category']} "
            f"({r['classification']['priority']})"
        )

    print("\n" + "=" * 60)
    print("All classifier tests complete.")
    print("=" * 60 + "\n")