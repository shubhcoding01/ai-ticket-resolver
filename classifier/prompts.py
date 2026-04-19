import os
from datetime import datetime
from dotenv   import load_dotenv

load_dotenv()

COMPANY_NAME   = os.getenv("COMPANY_NAME",   "ICICI Bank")
SUPPORT_NAME   = os.getenv("SUPPORT_NAME",   "IT Support Team")
COMPANY_DOMAIN = os.getenv("COMPANY_DOMAIN", "icici.com")


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

VALID_PRIORITIES = [
    "low",
    "medium",
    "high",
    "urgent",
]

VALID_CONFIDENCES = [
    "low",
    "medium",
    "high",
]


SYSTEM_PROMPT = f"""
You are an expert IT support ticket classifier working for
{COMPANY_NAME}. You have 15 years of experience in enterprise
desktop support and IT helpdesk operations.

Your sole job is to read a support ticket and return a perfectly
structured JSON classification. You never chat, never explain,
never add extra text — you only return valid JSON.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATEGORY DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app_install
    User needs software or an application installed on
    their machine. Covers any software request — Zoom,
    Teams, Chrome, Office, Adobe, VPN clients, SAP,
    Oracle, or any other business application.
    Trigger words: install, setup, deploy, need software,
    missing application, download.

antivirus
    Antivirus not working, not updating, showing errors,
    virus or malware detected, definitions out of date,
    real-time protection disabled, scan failing.
    Covers: Windows Defender, Symantec, McAfee, Kaspersky,
    Sophos, Trend Micro, Avast.
    Trigger words: virus, malware, definitions, scan,
    threat, quarantine, antivirus error.

password_reset
    Forgot password, account locked, password expired,
    cannot login to Windows or any corporate system,
    MFA not working, OTP not received, authenticator issues.
    Trigger words: password, locked, forgot, expired,
    cannot login, MFA, OTP, account disabled.

network
    No internet, VPN not connecting, slow network, WiFi
    issues, network drive not accessible, remote desktop
    not working, DNS issues, proxy errors, disconnections.
    Trigger words: internet, network, VPN, WiFi, connection,
    no access, slow, timeout, disconnected.

printer
    Printer offline, cannot print, print queue stuck,
    paper jam, printer driver missing, spooler error,
    network printer not found.
    Trigger words: print, printer, offline, queue, jam,
    spooler, driver, toner.

email_issue
    Outlook not opening or crashing, cannot send or
    receive emails, PST file corrupt, mailbox full,
    email not syncing, calendar issues, Exchange errors.
    Trigger words: outlook, email, PST, mailbox, inbox,
    send, receive, Exchange, sync.

hardware
    Physical hardware problems — laptop not turning on,
    screen broken or flickering, keyboard not working,
    battery issues, USB ports not working, overheating,
    slow performance due to hardware failure.
    Trigger words: screen, keyboard, battery, broken,
    physical, hardware, not turning on, damaged.

os_issue
    Windows problems — update failed, blue screen (BSOD),
    system crashes or restarts, slow performance, disk full,
    system files corrupt, startup errors, driver problems.
    Trigger words: windows, update, crash, BSOD, slow,
    restart, startup, sfc, DISM, registry.

access_permission
    Cannot access shared folders, drives or portals,
    permission denied errors, needs elevated access,
    Active Directory group membership issues,
    SharePoint or OneDrive access problems.
    Trigger words: access denied, permission, cannot open,
    shared drive, folder, unauthorized, restricted.

other
    Anything that does not fit any of the above categories.
    Use this sparingly — only when truly no other category
    applies. Always prefer a specific category over other.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIORITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

urgent
    Use when: Complete work stoppage, data loss risk,
    security breach, ransomware, multiple users affected,
    executive or senior management affected, production
    system down, regulatory or compliance deadline.
    Keywords: critical, emergency, data loss, hacked,
    ransomware, production down, all users affected,
    board meeting, CEO, MD.

high
    Use when: Single user completely blocked from working,
    time-sensitive deadline within hours, client meeting
    or presentation imminent, security-related issues.
    Keywords: urgent, cannot work, blocked, asap, client
    call, meeting in X hours, deadline today.

medium
    Use when: User can partially work but has a significant
    issue. Work is slower or harder but not impossible.
    Single user affected, no immediate deadline.
    Keywords: issue, problem, not working properly,
    error, need help.

low
    Use when: Minor inconvenience, cosmetic issue,
    non-urgent enhancement request, user has a workaround.
    Keywords: when possible, not urgent, minor, small,
    no rush, whenever convenient.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTO-RESOLVE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Set can_auto_resolve to TRUE only when ALL of these are true:
    1. The fix can be done entirely via remote script or tool
    2. No physical presence or hardware inspection is needed
    3. No complex investigation or manual diagnosis is needed
    4. The category is in this list:
         app_install, antivirus, password_reset,
         printer (basic spooler restart only),
         os_issue (basic cleanup/repair only),
         email_issue (basic Outlook repair only)

Set can_auto_resolve to FALSE when ANY of these are true:
    1. Hardware issue requiring physical inspection
    2. Complex network investigation needed
    3. Security breach or ransomware detected
    4. Access permission requiring AD group policy changes
    5. Machine name is UNKNOWN (cannot run remote script)
    6. Multiple systems or users affected
    7. Category is: hardware, access_permission, other
    8. Confidence in classification is low

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Return ONLY valid JSON. Zero extra text before or after.
2. Never use markdown code blocks or backticks.
3. All string values must be in double quotes.
4. Boolean values must be lowercase true or false.
5. category must be one of the 10 defined values exactly.
6. priority must be one of: low, medium, high, urgent.
7. confidence must be one of: low, medium, high.
8. suggested_action must be a single clear sentence of
   maximum 20 words describing what action to take.
9. If you are genuinely uncertain, use category other
   with confidence low rather than guessing wrong.
10. Never include personally identifiable information
    such as names, emails, or phone numbers in any field.
"""


CLASSIFICATION_PROMPT_TEMPLATE = """
Classify this IT support ticket from {company_name}.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET DETAILS
━━━━━━━━━━━━━━━━━━━━━━━
TICKET ID   : {ticket_id}
SUBJECT     : {subject}
DESCRIPTION : {description}
MACHINE     : {machine_name}
REQUESTER   : {requester_name}
SUBMITTED   : {submitted_at}
━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY this JSON object with no other text:

{{
    "category"         : "<category>",
    "priority"         : "<priority>",
    "can_auto_resolve" : <true|false>,
    "suggested_action" : "<one sentence action>",
    "confidence"       : "<confidence>",
    "reasoning"        : "<one sentence why this category>"
}}
"""


BATCH_CLASSIFICATION_PROMPT_TEMPLATE = """
Classify these {count} IT support tickets from {company_name}.

Return a JSON array with exactly {count} objects in the same
order as the tickets below. No extra text, no markdown.

TICKETS:
{tickets_block}

Return ONLY this JSON array:
[
    {{
        "ticket_id"        : <id>,
        "category"         : "<category>",
        "priority"         : "<priority>",
        "can_auto_resolve" : <true|false>,
        "suggested_action" : "<one sentence action>",
        "confidence"       : "<confidence>"
    }},
    ...
]
"""


RECLASSIFICATION_PROMPT_TEMPLATE = """
A previous AI classification of this IT ticket may be incorrect.
Please review the original classification and correct it if needed.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET
━━━━━━━━━━━━━━━━━━━━━━━
SUBJECT     : {subject}
DESCRIPTION : {description}

━━━━━━━━━━━━━━━━━━━━━━━
PREVIOUS CLASSIFICATION
━━━━━━━━━━━━━━━━━━━━━━━
Category         : {prev_category}
Priority         : {prev_priority}
Can Auto-Resolve : {prev_auto}
Confidence       : {prev_confidence}
Reason flagged   : {flag_reason}

━━━━━━━━━━━━━━━━━━━━━━━

Carefully re-read the ticket and return a corrected JSON:

{{
    "category"         : "<category>",
    "priority"         : "<priority>",
    "can_auto_resolve" : <true|false>,
    "suggested_action" : "<one sentence action>",
    "confidence"       : "<confidence>",
    "reasoning"        : "<one sentence explaining correction>",
    "changed"          : <true|false>
}}

Set changed to true if you changed the category or priority.
Set changed to false if the original classification was correct.
"""


AMBIGUOUS_TICKET_PROMPT_TEMPLATE = """
This IT support ticket is ambiguous or unclear.
It may describe multiple issues or use vague language.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET
━━━━━━━━━━━━━━━━━━━━━━━
SUBJECT     : {subject}
DESCRIPTION : {description}

━━━━━━━━━━━━━━━━━━━━━━━

Your job is to:
1. Identify the PRIMARY issue (the one that needs fixing first)
2. List any SECONDARY issues if present
3. Classify based on the primary issue only

Return ONLY this JSON:

{{
    "primary_issue"    : "<brief description of main problem>",
    "secondary_issues" : ["<issue 1>", "<issue 2>"],
    "category"         : "<category based on primary issue>",
    "priority"         : "<priority>",
    "can_auto_resolve" : <true|false>,
    "suggested_action" : "<one sentence action>",
    "confidence"       : "<confidence>",
    "is_ambiguous"     : true
}}

If there are no secondary issues return an empty array [].
"""


SENTIMENT_ANALYSIS_PROMPT_TEMPLATE = """
Analyze the sentiment and tone of this IT support ticket.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET
━━━━━━━━━━━━━━━━━━━━━━━
SUBJECT     : {subject}
DESCRIPTION : {description}
━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY this JSON:

{{
    "sentiment"          : "<positive|neutral|frustrated|angry|urgent>",
    "frustration_level"  : <0 to 10>,
    "urgency_signals"    : ["<signal 1>", "<signal 2>"],
    "polite"             : <true|false>,
    "needs_empathy"      : <true|false>,
    "priority_boost"     : <true|false>,
    "boost_reason"       : "<why priority should be boosted or empty string>"
}}

frustration_level: 0 = completely calm, 10 = extremely frustrated.
urgency_signals: list specific words or phrases showing urgency.
priority_boost: true if sentiment suggests priority should be raised
                above what the content alone would indicate.
"""


SUMMARY_GENERATION_PROMPT_TEMPLATE = """
Generate a concise professional summary of this IT support ticket
for the engineer who will handle it.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET
━━━━━━━━━━━━━━━━━━━━━━━
SUBJECT          : {subject}
DESCRIPTION      : {description}
CATEGORY         : {category}
PRIORITY         : {priority}
MACHINE          : {machine_name}
REQUESTER        : {requester_name}
SUGGESTED ACTION : {suggested_action}
━━━━━━━━━━━━━━━━━━━━━━━

Write a summary for the engineer in this exact JSON format:

{{
    "one_liner"       : "<single sentence describing the issue>",
    "problem"         : "<2-3 sentences describing what is wrong>",
    "impact"          : "<1-2 sentences on how user is affected>",
    "recommended_steps" : [
        "<step 1>",
        "<step 2>",
        "<step 3>"
    ],
    "things_to_check" : [
        "<check 1>",
        "<check 2>"
    ],
    "estimated_time"  : "<estimated resolution time e.g. 15 minutes>"
}}

Keep each field concise. Steps should be actionable and specific.
"""


TICKET_QUALITY_PROMPT_TEMPLATE = """
Assess the quality and completeness of this IT support ticket.
Determine if there is enough information to resolve it.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET
━━━━━━━━━━━━━━━━━━━━━━━
SUBJECT     : {subject}
DESCRIPTION : {description}
MACHINE     : {machine_name}
━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY this JSON:

{{
    "has_enough_info"     : <true|false>,
    "missing_fields"      : ["<field 1>", "<field 2>"],
    "quality_score"       : <1 to 10>,
    "clarifying_questions": [
        "<question 1>",
        "<question 2>"
    ],
    "can_proceed"         : <true|false>
}}

has_enough_info: true if the ticket has sufficient detail
                 to attempt resolution.
missing_fields: list what critical info is absent.
                Common missing fields: machine name, exact error
                message, steps already tried, since when issue
                started, affected users count.
quality_score: 1 = completely unusable, 10 = perfect detail.
clarifying_questions: questions to ask the user if more info
                      is needed. Return empty array [] if not needed.
can_proceed: true if automation or engineer can attempt resolution
             despite missing information.
"""


AUTO_REPLY_PROMPT_TEMPLATE = """
Write a professional and empathetic auto-reply email to the user
who raised this IT support ticket at {company_name}.

━━━━━━━━━━━━━━━━━━━━━━━
TICKET CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━
TICKET ID        : {ticket_id}
SUBJECT          : {subject}
REQUESTER NAME   : {requester_name}
CATEGORY         : {category}
PRIORITY         : {priority}
CAN AUTO-RESOLVE : {can_auto_resolve}
ESTIMATED TIME   : {estimated_time}
━━━━━━━━━━━━━━━━━━━━━━━

Write the reply in this JSON format:

{{
    "subject_line" : "<email subject line>",
    "greeting"     : "<personalized greeting>",
    "body"         : "<main email body>",
    "closing"      : "<professional closing>",
    "tone"         : "<professional|empathetic|urgent>"
}}

Rules for the reply:
- Address the user by first name
- Acknowledge their specific issue by name
- If can_auto_resolve is true: tell them the issue is being
  fixed automatically and give a realistic time estimate
- If can_auto_resolve is false: tell them an engineer will
  review and set expectations for response time
- Keep the body to 3-4 sentences maximum
- Never promise specific times you cannot guarantee
- Never use technical jargon the user would not understand
- Always end with a helpdesk contact option
- Tone should be warm, professional, and reassuring
"""


def build_classification_prompt(
    subject        : str,
    description    : str,
    ticket_id      : int   = 0,
    machine_name   : str   = "UNKNOWN",
    requester_name : str   = "User",
    submitted_at   : str   = None,
) -> str:
    """
    Build the user message for standard ticket classification.
    Fills in the CLASSIFICATION_PROMPT_TEMPLATE with ticket data.

    Args:
        subject        : Ticket subject line
        description    : Full ticket description
        ticket_id      : Freshdesk ticket ID
        machine_name   : User's machine name
        requester_name : Name of user who raised ticket
        submitted_at   : When the ticket was submitted

    Returns:
        Formatted prompt string ready to send to Claude
    """
    if not submitted_at:
        submitted_at = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")

    description_trimmed = description[:1500] if len(description) > 1500 else description

    return CLASSIFICATION_PROMPT_TEMPLATE.format(
        company_name   = COMPANY_NAME,
        ticket_id      = ticket_id,
        subject        = subject.strip(),
        description    = description_trimmed.strip(),
        machine_name   = machine_name or "UNKNOWN",
        requester_name = requester_name or "User",
        submitted_at   = submitted_at,
    )


def build_batch_classification_prompt(tickets: list) -> str:
    """
    Build the user message for batch ticket classification.
    Formats multiple tickets into a single prompt.

    Args:
        tickets : List of dicts each with id, subject, description

    Returns:
        Formatted batch prompt string
    """
    ticket_lines = []

    for i, ticket in enumerate(tickets, start=1):
        desc = ticket.get("description", "")
        desc_trimmed = desc[:400] if len(desc) > 400 else desc

        block = (
            f"--- Ticket {i} ---\n"
            f"ID          : {ticket.get('id', i)}\n"
            f"Subject     : {ticket.get('subject', '')}\n"
            f"Description : {desc_trimmed}\n"
        )
        ticket_lines.append(block)

    tickets_block = "\n".join(ticket_lines)

    return BATCH_CLASSIFICATION_PROMPT_TEMPLATE.format(
        count        = len(tickets),
        company_name = COMPANY_NAME,
        tickets_block = tickets_block,
    )


def build_reclassification_prompt(
    subject         : str,
    description     : str,
    prev_category   : str,
    prev_priority   : str,
    prev_auto       : bool,
    prev_confidence : str,
    flag_reason     : str,
) -> str:
    """
    Build prompt for re-classifying a previously classified ticket
    that was flagged as potentially incorrect.

    Args:
        subject         : Ticket subject
        description     : Ticket description
        prev_category   : Original AI category
        prev_priority   : Original AI priority
        prev_auto       : Original can_auto_resolve value
        prev_confidence : Original confidence level
        flag_reason     : Why this ticket was flagged for review

    Returns:
        Formatted reclass prompt string
    """
    desc_trimmed = description[:1500] if len(description) > 1500 else description

    return RECLASSIFICATION_PROMPT_TEMPLATE.format(
        subject         = subject.strip(),
        description     = desc_trimmed.strip(),
        prev_category   = prev_category,
        prev_priority   = prev_priority,
        prev_auto       = str(prev_auto).lower(),
        prev_confidence = prev_confidence,
        flag_reason     = flag_reason,
    )


def build_ambiguous_ticket_prompt(
    subject     : str,
    description : str,
) -> str:
    """
    Build prompt for handling ambiguous tickets that describe
    multiple issues or use unclear language.

    Args:
        subject     : Ticket subject
        description : Ticket description

    Returns:
        Formatted ambiguous prompt string
    """
    desc_trimmed = description[:1500] if len(description) > 1500 else description

    return AMBIGUOUS_TICKET_PROMPT_TEMPLATE.format(
        subject     = subject.strip(),
        description = desc_trimmed.strip(),
    )


def build_sentiment_prompt(
    subject     : str,
    description : str,
) -> str:
    """
    Build prompt for analyzing user sentiment in a ticket.
    Used to detect frustrated or angry users who need priority boost.

    Args:
        subject     : Ticket subject
        description : Ticket description

    Returns:
        Formatted sentiment prompt string
    """
    desc_trimmed = description[:1000] if len(description) > 1000 else description

    return SENTIMENT_ANALYSIS_PROMPT_TEMPLATE.format(
        subject     = subject.strip(),
        description = desc_trimmed.strip(),
    )


def build_summary_prompt(
    subject          : str,
    description      : str,
    category         : str,
    priority         : str,
    machine_name     : str = "UNKNOWN",
    requester_name   : str = "User",
    suggested_action : str = "",
) -> str:
    """
    Build prompt for generating an engineer-facing ticket summary.
    Used by escalation.py to give engineers full context.

    Args:
        subject          : Ticket subject
        description      : Full ticket description
        category         : AI classified category
        priority         : AI classified priority
        machine_name     : User's machine name
        requester_name   : User's full name
        suggested_action : AI recommended action

    Returns:
        Formatted summary prompt string
    """
    desc_trimmed = description[:1500] if len(description) > 1500 else description

    return SUMMARY_GENERATION_PROMPT_TEMPLATE.format(
        subject          = subject.strip(),
        description      = desc_trimmed.strip(),
        category         = category,
        priority         = priority,
        machine_name     = machine_name or "UNKNOWN",
        requester_name   = requester_name or "User",
        suggested_action = suggested_action,
    )


def build_quality_check_prompt(
    subject      : str,
    description  : str,
    machine_name : str = "UNKNOWN",
) -> str:
    """
    Build prompt for assessing ticket completeness.
    Used to detect tickets that need more info before processing.

    Args:
        subject      : Ticket subject
        description  : Ticket description
        machine_name : User's machine name

    Returns:
        Formatted quality check prompt string
    """
    desc_trimmed = description[:1000] if len(description) > 1000 else description

    return TICKET_QUALITY_PROMPT_TEMPLATE.format(
        subject      = subject.strip(),
        description  = desc_trimmed.strip(),
        machine_name = machine_name or "UNKNOWN",
    )


def build_auto_reply_prompt(
    ticket_id      : int,
    subject        : str,
    requester_name : str,
    category       : str,
    priority       : str,
    can_auto_resolve: bool,
    estimated_time  : str = "2-4 hours",
) -> str:
    """
    Build prompt for generating personalized auto-reply emails.
    Used by notifier.py for richer email generation.

    Args:
        ticket_id        : Freshdesk ticket ID
        subject          : Ticket subject
        requester_name   : User's full name
        category         : AI classified category
        priority         : AI classified priority
        can_auto_resolve : Whether ticket can be auto-resolved
        estimated_time   : Expected resolution time string

    Returns:
        Formatted auto-reply prompt string
    """
    return AUTO_REPLY_PROMPT_TEMPLATE.format(
        company_name     = COMPANY_NAME,
        ticket_id        = ticket_id,
        subject          = subject.strip(),
        requester_name   = requester_name or "User",
        category         = category.replace("_", " ").title(),
        priority         = priority.title(),
        can_auto_resolve = str(can_auto_resolve).lower(),
        estimated_time   = estimated_time,
    )


def get_system_prompt() -> str:
    """
    Return the system prompt used for all Claude API calls.
    Called by ai_classifier.py when building API requests.

    Returns:
        System prompt string
    """
    return SYSTEM_PROMPT.strip()


def get_valid_categories() -> list:
    """
    Return the list of all valid category values.
    Used by ai_classifier.py for response validation.

    Returns:
        List of valid category strings
    """
    return VALID_CATEGORIES.copy()


def get_valid_priorities() -> list:
    """
    Return the list of all valid priority values.
    Used by ai_classifier.py for response validation.

    Returns:
        List of valid priority strings
    """
    return VALID_PRIORITIES.copy()


def get_valid_confidences() -> list:
    """
    Return the list of all valid confidence values.
    Used by ai_classifier.py for response validation.

    Returns:
        List of valid confidence strings
    """
    return VALID_CONFIDENCES.copy()


def get_category_description(category: str) -> str:
    """
    Return the human-readable description for a category.
    Used in engineer escalation emails and dashboard labels.

    Args:
        category : Category string e.g. 'app_install'

    Returns:
        Description string
    """
    descriptions = {
        "app_install"       : "Software / Application Installation",
        "antivirus"         : "Antivirus / Security Issue",
        "password_reset"    : "Password Reset / Account Lockout",
        "network"           : "Network / VPN / Connectivity",
        "printer"           : "Printer / Printing Issue",
        "email_issue"       : "Email / Outlook Issue",
        "hardware"          : "Hardware / Physical Device Issue",
        "os_issue"          : "Windows OS / System Issue",
        "access_permission" : "Access / Permission Issue",
        "other"             : "Other / Uncategorized",
    }
    return descriptions.get(category, category.replace("_", " ").title())


def get_estimated_resolution_time(
    category : str,
    priority : str,
) -> str:
    """
    Return an estimated resolution time string based on
    category and priority. Used in auto-reply emails to
    set user expectations.

    Args:
        category : Ticket category
        priority : Ticket priority

    Returns:
        Human-readable time estimate string
    """
    base_times = {
        "app_install"       : 30,
        "antivirus"         : 20,
        "password_reset"    : 15,
        "network"           : 60,
        "printer"           : 30,
        "email_issue"       : 45,
        "hardware"          : 240,
        "os_issue"          : 60,
        "access_permission" : 120,
        "other"             : 120,
    }

    priority_multipliers = {
        "urgent" : 0.5,
        "high"   : 0.75,
        "medium" : 1.0,
        "low"    : 1.5,
    }

    base    = base_times.get(category, 60)
    mult    = priority_multipliers.get(priority, 1.0)
    minutes = int(base * mult)

    if minutes < 30:
        return "within 30 minutes"
    elif minutes < 60:
        return f"within {minutes} minutes"
    elif minutes < 120:
        return "within 1-2 hours"
    elif minutes < 480:
        hours = minutes // 60
        return f"within {hours}-{hours + 1} hours"
    else:
        return "within 1 business day"


if __name__ == "__main__":

    print("\n" + "=" * 65)
    print("PROMPTS MODULE — TEST RUN")
    print("=" * 65 + "\n")

    print("--- System Prompt Preview (first 300 chars) ---")
    sp = get_system_prompt()
    print(sp[:300] + "...\n")

    print("--- Classification Prompt ---")
    cp = build_classification_prompt(
        subject        = "Zoom not installed on my laptop",
        description    = (
            "Hi team, I need Zoom installed on my machine. "
            "I have a client call in 2 hours and Zoom is not "
            "installed. My machine is PC-ICICI-0042. Please help."
        ),
        ticket_id      = 1001,
        machine_name   = "PC-ICICI-0042",
        requester_name = "Rahul Sharma",
    )
    print(cp)

    print("\n--- Batch Classification Prompt ---")
    tickets = [
        {
            "id"          : 1001,
            "subject"     : "Install Zoom urgently",
            "description" : "Need Zoom on PC-ICICI-0042 for client call.",
        },
        {
            "id"          : 1002,
            "subject"     : "Antivirus not updating",
            "description" : "Symantec showing red error, definitions outdated.",
        },
        {
            "id"          : 1003,
            "subject"     : "Cannot login — locked out",
            "description" : "Forgot password, account locked after 5 attempts.",
        },
    ]
    bp = build_batch_classification_prompt(tickets)
    print(bp)

    print("\n--- Sentiment Prompt ---")
    sp2 = build_sentiment_prompt(
        subject     = "URGENT — Cannot work at all!!",
        description = (
            "I have been trying to fix this since morning! "
            "Nothing is working and I have a client deadline "
            "in 1 hour. This is completely unacceptable. "
            "Please help me RIGHT NOW."
        ),
    )
    print(sp2)

    print("\n--- Summary Prompt ---")
    sump = build_summary_prompt(
        subject          = "VPN not connecting from home",
        description      = "Cannot connect to VPN. AnyConnect times out.",
        category         = "network",
        priority         = "high",
        machine_name     = "LAPTOP-ICICI-115",
        requester_name   = "Priya Mehta",
        suggested_action = "Check VPN config and reset network adapter.",
    )
    print(sump)

    print("\n--- Quality Check Prompt ---")
    qp = build_quality_check_prompt(
        subject      = "Not working",
        description  = "Please fix asap.",
        machine_name = "UNKNOWN",
    )
    print(qp)

    print("\n--- Category Descriptions ---")
    for cat in get_valid_categories():
        desc = get_category_description(cat)
        print(f"  {cat:<20} → {desc}")

    print("\n--- Estimated Resolution Times ---")
    for cat in ["app_install", "antivirus", "hardware", "network"]:
        for pri in ["urgent", "high", "medium", "low"]:
            t = get_estimated_resolution_time(cat, pri)
            print(f"  {cat:<18} + {pri:<7} → {t}")

    print("\n--- Valid Values ---")
    print(f"Categories  : {get_valid_categories()}")
    print(f"Priorities  : {get_valid_priorities()}")
    print(f"Confidences : {get_valid_confidences()}")

    print("\nAll prompt tests complete.")