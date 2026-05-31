# import re
# import logging
# from datetime import datetime

# log = logging.getLogger(__name__)

# CATEGORY_RULES = {
#     "app_install": {
#         "keywords": [
#             "install", "installation", "setup", "deploy",
#             "need software", "need application", "need app",
#             "download", "get software", "add software",
#             "zoom", "teams", "microsoft teams", "ms teams",
#             "chrome", "google chrome", "firefox", "mozilla",
#             "edge", "internet explorer",
#             "office", "ms office", "microsoft office",
#             "word", "excel", "powerpoint", "outlook",
#             "adobe", "acrobat", "reader", "photoshop",
#             "skype", "slack", "webex", "cisco webex",
#             "anyconnect", "cisco anyconnect",
#             "putty", "winscp", "filezilla",
#             "notepad++", "7zip", "winrar", "winzip",
#             "vlc", "media player",
#             "tally", "sap", "oracle",
#             "antivirus software", "endpoint protection",
#             "visual studio", "vscode", "eclipse",
#             "java", "python", "nodejs",
#             "git", "github desktop",
#             "postman", "dbeaver", "sql server management",
#         ],
#         "phrases": [
#             "please install",
#             "need to install",
#             "want to install",
#             "can you install",
#             "install on my",
#             "install on laptop",
#             "install on desktop",
#             "install on machine",
#             "install on pc",
#             "software not installed",
#             "application not installed",
#             "app not installed",
#             "missing software",
#             "missing application",
#             "not available on my",
#             "not installed on my",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : True,
#         "default_priority" : "medium",
#     },

#     "antivirus": {
#         "keywords": [
#             "antivirus", "anti-virus", "anti virus",
#             "virus", "malware", "ransomware", "spyware",
#             "trojan", "worm", "threat", "infected",
#             "malicious", "suspicious file",
#             "symantec", "norton", "mcafee",
#             "defender", "windows defender",
#             "kaspersky", "trend micro", "sophos",
#             "avast", "avg", "bitdefender",
#             "endpoint protection", "endpoint security",
#             "definitions", "virus definitions",
#             "signature update", "dat file",
#             "quarantine", "quarantined",
#             "scan", "full scan", "quick scan",
#             "real-time protection", "real time protection",
#             "firewall", "intrusion detection",
#         ],
#         "phrases": [
#             "antivirus not working",
#             "antivirus not updating",
#             "antivirus error",
#             "virus detected",
#             "malware detected",
#             "threat detected",
#             "definitions out of date",
#             "definitions outdated",
#             "signature out of date",
#             "av not updating",
#             "scan failed",
#             "scan not running",
#             "protection disabled",
#             "real-time protection off",
#             "virus warning",
#             "security alert",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : True,
#         "default_priority" : "high",
#     },

#     "password_reset": {
#         "keywords": [
#             "password", "passwd", "pwd",
#             "reset", "forgot", "forget",
#             "locked", "lock out", "lockout",
#             "expired", "expiry", "expiration",
#             "account locked", "account disabled",
#             "login failed", "cannot login", "cant login",
#             "unable to login", "login issue",
#             "credentials", "credential",
#             "mfa", "multi factor", "multifactor",
#             "two factor", "2fa", "authenticator",
#             "otp", "one time password",
#             "pin", "pin reset",
#             "active directory", "ad account",
#             "domain account", "windows login",
#             "network login",
#         ],
#         "phrases": [
#             "forgot my password",
#             "forgot password",
#             "reset my password",
#             "reset password",
#             "account is locked",
#             "account locked out",
#             "password expired",
#             "password has expired",
#             "cannot log in",
#             "unable to log in",
#             "login is not working",
#             "password not working",
#             "wrong password",
#             "change my password",
#             "mfa not working",
#             "authenticator not working",
#             "otp not received",
#             "otp not working",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : True,
#         "default_priority" : "high",
#     },

#     "network": {
#         "keywords": [
#             "internet", "network", "connectivity",
#             "wifi", "wi-fi", "wireless",
#             "ethernet", "lan", "wan",
#             "vpn", "virtual private network",
#             "proxy", "dns", "ip address", "dhcp",
#             "ping", "traceroute", "packet loss",
#             "bandwidth", "slow internet", "slow network",
#             "no internet", "no network", "no connectivity",
#             "connection", "disconnected", "disconnect",
#             "timeout", "timed out", "connection refused",
#             "firewall", "port blocked", "port forwarding",
#             "remote desktop", "rdp",
#             "network drive", "shared drive",
#             "mapped drive", "network share",
#             "router", "switch", "access point",
#             "ssid", "network adapter",
#             "ipconfig", "netstat",
#         ],
#         "phrases": [
#             "no internet access",
#             "cannot access internet",
#             "internet not working",
#             "wifi not working",
#             "wi-fi not connecting",
#             "vpn not connecting",
#             "vpn connection failed",
#             "vpn not working",
#             "cannot connect to vpn",
#             "network is slow",
#             "slow connection",
#             "keeps disconnecting",
#             "dropping connection",
#             "no network access",
#             "cannot access network",
#             "network drive not accessible",
#             "cannot map drive",
#             "shared folder not accessible",
#             "remote desktop not working",
#             "rdp not connecting",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : False,
#         "default_priority" : "high",
#     },

#     "printer": {
#         "keywords": [
#             "print", "printer", "printing",
#             "print job", "print queue", "print spooler",
#             "offline printer", "printer offline",
#             "paper jam", "jam", "paper stuck",
#             "toner", "ink", "cartridge",
#             "driver", "printer driver",
#             "default printer",
#             "network printer", "shared printer",
#             "hp", "canon", "epson", "brother",
#             "xerox", "ricoh", "kyocera",
#             "scanner", "scan to email",
#             "multifunction", "mfp",
#             "print server",
#         ],
#         "phrases": [
#             "cannot print",
#             "printer not working",
#             "printer not responding",
#             "printer is offline",
#             "printer offline",
#             "print job stuck",
#             "print queue stuck",
#             "printing not working",
#             "unable to print",
#             "document not printing",
#             "printer driver issue",
#             "printer driver missing",
#             "printer not found",
#             "printer not detected",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : True,
#         "default_priority" : "low",
#     },

#     "email_issue": {
#         "keywords": [
#             "email", "e-mail", "mail",
#             "outlook", "thunderbird",
#             "inbox", "mailbox",
#             "pst", "ost", "archive",
#             "exchange", "exchange server",
#             "smtp", "imap", "pop3",
#             "send", "receive", "sync",
#             "attachment", "calendar",
#             "meeting invite", "meeting request",
#             "contact", "address book",
#             "signature", "out of office",
#             "shared mailbox", "delegate",
#             "distribution list", "mailing list",
#             "spam", "junk mail",
#             "email quota", "mailbox full",
#             "auto-reply", "autoresponse",
#         ],
#         "phrases": [
#             "outlook not opening",
#             "outlook not working",
#             "outlook crashing",
#             "cannot send email",
#             "cannot receive email",
#             "email not sending",
#             "email not receiving",
#             "emails not syncing",
#             "mailbox full",
#             "pst file corrupt",
#             "pst not loading",
#             "outlook profile corrupt",
#             "cannot open outlook",
#             "email not working",
#             "cannot access email",
#             "emails disappeared",
#             "inbox empty",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : True,
#         "default_priority" : "medium",
#     },

#     "hardware": {
#         "keywords": [
#             "laptop", "desktop", "computer", "pc",
#             "screen", "monitor", "display",
#             "keyboard", "mouse", "trackpad", "touchpad",
#             "battery", "charger", "power adapter",
#             "hard disk", "hdd", "ssd", "storage",
#             "ram", "memory",
#             "usb", "usb port", "usb hub",
#             "headphone", "headset", "speaker", "microphone",
#             "webcam", "camera",
#             "overheating", "overheat", "hot",
#             "fan", "cooling",
#             "physical damage", "broken", "cracked",
#             "docking station", "dock",
#             "external drive", "pen drive", "flash drive",
#             "hdmi", "vga", "display port",
#             "slow laptop", "slow computer",
#             "freezing", "frozen",
#             "blue screen", "bsod",
#         ],
#         "phrases": [
#             "laptop not turning on",
#             "computer not starting",
#             "pc not booting",
#             "screen is blank",
#             "screen not working",
#             "screen flickering",
#             "display problem",
#             "keyboard not working",
#             "keys not working",
#             "mouse not working",
#             "battery not charging",
#             "battery draining fast",
#             "laptop very slow",
#             "computer very slow",
#             "running slow",
#             "getting hot",
#             "overheating issue",
#             "usb not working",
#             "usb not detected",
#             "hard disk full",
#             "no storage space",
#             "ram issue",
#             "memory issue",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : False,
#         "default_priority" : "high",
#     },

#     "os_issue": {
#         "keywords": [
#             "windows", "windows 10", "windows 11",
#             "operating system", "os",
#             "update", "windows update",
#             "patch", "cumulative update",
#             "blue screen", "bsod",
#             "crash", "system crash",
#             "restart", "reboot",
#             "startup", "boot", "booting",
#             "shutdown", "not shutting down",
#             "registry", "system file",
#             "corrupt", "corrupted",
#             "sfc", "dism", "chkdsk",
#             "event log", "error log",
#             "driver", "device driver",
#             "system restore", "recovery",
#             "task manager", "services",
#             "cpu usage", "disk usage", "ram usage",
#             "performance", "slow performance",
#             "temp files", "disk space",
#             "recycle bin", "junk files",
#         ],
#         "phrases": [
#             "windows update failed",
#             "update not installing",
#             "cannot update windows",
#             "blue screen error",
#             "blue screen of death",
#             "system is crashing",
#             "computer keeps crashing",
#             "computer keeps restarting",
#             "automatic restart",
#             "system not booting",
#             "not starting up",
#             "startup error",
#             "black screen on startup",
#             "slow after update",
#             "performance issue",
#             "disk space full",
#             "c drive full",
#             "system files corrupt",
#             "dll missing",
#             "dll error",
#             "application error",
#             "runtime error",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : True,
#         "default_priority" : "high",
#     },

#     "access_permission": {
#         "keywords": [
#             "access", "permission", "permissions",
#             "denied", "access denied",
#             "unauthorized", "not authorized",
#             "forbidden", "restricted",
#             "shared drive", "shared folder",
#             "network share", "file share",
#             "role", "role access",
#             "group", "ad group",
#             "active directory", "ad permission",
#             "folder access", "file access",
#             "read", "write", "modify",
#             "elevation", "admin rights",
#             "administrator", "local admin",
#             "user account control", "uac",
#             "sharepoint", "onedrive",
#             "teams access", "channel access",
#             "portal access", "system access",
#             "application access",
#         ],
#         "phrases": [
#             "access denied",
#             "cannot access",
#             "don't have access",
#             "do not have access",
#             "no permission",
#             "permission denied",
#             "not authorized",
#             "need access to",
#             "require access to",
#             "requesting access",
#             "grant me access",
#             "give me access",
#             "folder is locked",
#             "cannot open folder",
#             "cannot open file",
#             "restricted access",
#             "blocked from accessing",
#         ],
#         "weight"           : 1.0,
#         "can_auto_resolve" : False,
#         "default_priority" : "medium",
#     },
# }

# PRIORITY_RULES = {
#     "urgent": {
#         "keywords": [
#             "urgent", "urgently", "emergency", "critical",
#             "immediately", "asap", "right now", "right away",
#             "production down", "system down", "server down",
#             "data loss", "data lost", "data breach",
#             "hacked", "ransomware", "virus attack",
#             "cannot work at all", "completely blocked",
#             "all users affected", "multiple users",
#             "entire team", "everyone affected",
#             "ceo", "md", "director", "vp",
#             "client meeting", "board meeting",
#             "presentation in", "call in",
#             "deadline today", "deadline in",
#         ],
#         "weight": 3.0,
#     },
#     "high": {
#         "keywords": [
#             "urgent", "asap", "important",
#             "cannot work", "not able to work",
#             "blocked", "blocking",
#             "need today", "needed today",
#             "please help", "desperately",
#             "senior", "manager", "head",
#             "meeting in", "interview",
#             "client call", "customer call",
#         ],
#         "weight": 2.0,
#     },
#     "medium": {
#         "keywords": [
#             "issue", "problem", "error",
#             "not working", "not functioning",
#             "please resolve", "need assistance",
#             "help needed", "need help",
#             "broken", "failing",
#         ],
#         "weight": 1.0,
#     },
#     "low": {
#         "keywords": [
#             "not urgent", "low priority",
#             "when possible", "whenever convenient",
#             "no rush", "take your time",
#             "minor issue", "small problem",
#             "if possible", "when you get a chance",
#             "enhancement", "improvement",
#             "suggestion", "request",
#         ],
#         "weight": 0.5,
#     },
# }

# ESCALATION_TRIGGERS = [
#     "data loss",
#     "data breach",
#     "security breach",
#     "hacked",
#     "ransomware",
#     "all users affected",
#     "production is down",
#     "system is down",
#     "server is down",
#     "ceo",
#     "managing director",
#     "rbi audit",
#     "regulatory",
#     "compliance issue",
#     "legal",
# ]

# BUSINESS_HOURS = {
#     "start_hour" : 9,
#     "end_hour"   : 18,
#     "timezone"   : "IST",
#     "workdays"   : [0, 1, 2, 3, 4],
# }


# def classify_by_rules(subject: str, description: str) -> dict:
#     """
#     Main rule-based classifier function.
#     Called by ai_classifier.py as a fallback when the Claude
#     API is unavailable, and also used to cross-validate AI results.

#     Scoring system:
#         - Each keyword match adds the category weight to its score
#         - Each phrase match adds 2x the category weight (phrases are more specific)
#         - The category with the highest total score wins
#         - Priority is determined by a separate priority scoring pass
#         - If no category scores above threshold, defaults to 'other'

#     Args:
#         subject     : Ticket subject / title text
#         description : Full ticket description text

#     Returns:
#         Dict with keys: category, priority, can_auto_resolve,
#                         suggested_action, confidence, scores
#     """
#     if not subject and not description:
#         log.warning("classify_by_rules received empty subject and description.")
#         return _default_result()

#     full_text  = f"{subject} {description}".lower().strip()
#     full_text  = _normalize_text(full_text)

#     log.info(f"Rule-based classification on: '{subject[:60]}...'")

#     category_scores = _score_categories(full_text)
#     priority        = _detect_priority(full_text)
#     force_escalate  = _check_escalation_triggers(full_text)
#     after_hours     = _is_after_business_hours()
#     urgency_boost   = _detect_urgency_boost(full_text)

#     category, score, confidence = _pick_best_category(category_scores)

#     if urgency_boost and priority == "medium":
#         priority = "high"

#     if force_escalate:
#         log.warning(
#             f"Escalation trigger detected in ticket — "
#             f"forcing can_auto_resolve=False."
#         )

#     can_auto = (
#         CATEGORY_RULES.get(category, {}).get("can_auto_resolve", False)
#         and not force_escalate
#     )

#     suggested_action = _get_suggested_action(category, full_text)

#     result = {
#         "category"        : category,
#         "priority"        : priority,
#         "can_auto_resolve": can_auto,
#         "suggested_action": suggested_action,
#         "confidence"      : confidence,
#         "scores"          : category_scores,
#         "force_escalate"  : force_escalate,
#         "after_hours"     : after_hours,
#         "classified_by"   : "rules",
#     }

#     log.info(
#         f"Rule classification result — "
#         f"category: {category}, "
#         f"priority: {priority}, "
#         f"confidence: {confidence}, "
#         f"auto: {can_auto}"
#     )

#     return result


# def _score_categories(text: str) -> dict:
#     """
#     Score every category by counting keyword and phrase matches
#     in the ticket text. Phrases score 2x keywords.

#     Args:
#         text : Normalized lowercase full ticket text

#     Returns:
#         Dict of category -> score (float)
#     """
#     scores = {cat: 0.0 for cat in CATEGORY_RULES}

#     for category, rules in CATEGORY_RULES.items():
#         weight   = rules.get("weight", 1.0)
#         keywords = rules.get("keywords", [])
#         phrases  = rules.get("phrases",  [])

#         for keyword in keywords:
#             if keyword.lower() in text:
#                 scores[category] += weight * 1.0
#                 log.debug(
#                     f"  Keyword match [{category}]: '{keyword}'"
#                 )

#         for phrase in phrases:
#             if phrase.lower() in text:
#                 scores[category] += weight * 2.0
#                 log.debug(
#                     f"  Phrase match [{category}]: '{phrase}'"
#                 )

#     return scores


# def _pick_best_category(scores: dict) -> tuple:
#     """
#     Select the category with the highest score.
#     Calculates confidence based on how much the winner
#     leads the second-place category.

#     Args:
#         scores : Dict of category -> score from _score_categories()

#     Returns:
#         Tuple of (category, score, confidence)
#         where confidence is 'high', 'medium', or 'low'
#     """
#     if not any(scores.values()):
#         log.info("No category matched — defaulting to 'other'.")
#         return "other", 0.0, "low"

#     sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
#     best_cat    = sorted_cats[0][0]
#     best_score  = sorted_cats[0][1]
#     second_score = sorted_cats[1][1] if len(sorted_cats) > 1 else 0.0

#     if best_score == 0.0:
#         return "other", 0.0, "low"

#     gap = best_score - second_score

#     if best_score >= 4.0 and gap >= 2.0:
#         confidence = "high"
#     elif best_score >= 2.0 and gap >= 1.0:
#         confidence = "medium"
#     else:
#         confidence = "low"

#     log.debug(
#         f"Best category: {best_cat} "
#         f"(score={best_score:.1f}, gap={gap:.1f}, "
#         f"confidence={confidence})"
#     )

#     return best_cat, best_score, confidence


# def _detect_priority(text: str) -> str:
#     """
#     Detect ticket priority using weighted keyword scoring.
#     Higher-weight priority keywords override lower ones.

#     Args:
#         text : Normalized lowercase full ticket text

#     Returns:
#         Priority string: 'urgent', 'high', 'medium', or 'low'
#     """
#     priority_scores = {p: 0.0 for p in PRIORITY_RULES}

#     for priority, rules in PRIORITY_RULES.items():
#         weight   = rules.get("weight", 1.0)
#         keywords = rules.get("keywords", [])

#         for keyword in keywords:
#             if keyword.lower() in text:
#                 priority_scores[priority] += weight

#     if priority_scores["urgent"] > 0:
#         return "urgent"
#     elif priority_scores["high"] > 0:
#         return "high"
#     elif priority_scores["low"] > 0 and priority_scores["medium"] == 0:
#         return "low"
#     else:
#         return "medium"


# def _detect_urgency_boost(text: str) -> bool:
#     """
#     Detect if the ticket contains time-sensitive language
#     that should boost priority regardless of category.

#     Args:
#         text : Normalized lowercase full ticket text

#     Returns:
#         True if urgency boost should be applied
#     """
#     time_patterns = [
#         r"in \d+ (minute|hour|min|hr)",
#         r"\d+ (minute|hour|min|hr)s? (left|remaining|away)",
#         r"by (today|tonight|morning|afternoon|eod|eob)",
#         r"(meeting|call|interview|presentation) (at|in|by)",
#         r"deadline (is|at|by|in)",
#         r"client (is|will be) (waiting|here|online)",
#     ]

#     for pattern in time_patterns:
#         if re.search(pattern, text):
#             log.debug(f"Urgency boost triggered by pattern: {pattern}")
#             return True

#     return False


# def _check_escalation_triggers(text: str) -> bool:
#     """
#     Check if the ticket contains any keywords that should
#     force immediate escalation regardless of category or priority.
#     These are critical security/compliance/executive triggers.

#     Args:
#         text : Normalized lowercase full ticket text

#     Returns:
#         True if ticket must be force-escalated
#     """
#     for trigger in ESCALATION_TRIGGERS:
#         if trigger.lower() in text:
#             log.warning(
#                 f"Escalation trigger found in ticket: '{trigger}'"
#             )
#             return True

#     return False


# def _is_after_business_hours() -> bool:
#     """
#     Check if the current time is outside business hours.
#     Used to flag tickets that will not be seen by engineers
#     until the next working day.

#     Returns:
#         True if currently outside business hours
#     """
#     now     = datetime.utcnow()
#     ist_now = now.replace(hour=(now.hour + 5) % 24)

#     is_workday   = ist_now.weekday() in BUSINESS_HOURS["workdays"]
#     is_work_hour = (
#         BUSINESS_HOURS["start_hour"]
#         <= ist_now.hour
#         < BUSINESS_HOURS["end_hour"]
#     )

#     return not (is_workday and is_work_hour)


# def _normalize_text(text: str) -> str:
#     """
#     Normalize ticket text for consistent keyword matching.
#     Lowercases, removes special chars, normalizes whitespace.

#     Args:
#         text : Raw ticket text

#     Returns:
#         Normalized text string
#     """
#     text = text.lower()
#     text = re.sub(r'[^\w\s\-\.]', ' ', text)
#     text = re.sub(r'\s+', ' ', text)
#     text = text.strip()

#     contractions = {
#         "can't"    : "cannot",
#         "won't"    : "will not",
#         "don't"    : "do not",
#         "doesn't"  : "does not",
#         "isn't"    : "is not",
#         "aren't"   : "are not",
#         "couldn't" : "could not",
#         "didn't"   : "did not",
#         "haven't"  : "have not",
#         "hasn't"   : "has not",
#         "i'm"      : "i am",
#         "i've"     : "i have",
#         "it's"     : "it is",
#     }

#     for contraction, expansion in contractions.items():
#         text = text.replace(contraction, expansion)

#     return text


# def _get_suggested_action(category: str, text: str) -> str:
#     """
#     Return a specific suggested action string based on category
#     and any additional context found in the ticket text.

#     Args:
#         category : Detected ticket category
#         text     : Full normalized ticket text

#     Returns:
#         Suggested action string
#     """
#     actions = {
#         "app_install": _suggest_app_install_action,
#         "antivirus"  : _suggest_antivirus_action,
#         "os_issue"   : _suggest_os_action,
#         "other"      : lambda t: "Assign to engineer for manual investigation.",
#     }

#     specific_fn = actions.get(category)
#     if specific_fn:
#         return specific_fn(text)

#     generic_actions = {
#         "password_reset"   : "Reset user password via Active Directory and notify user with temp credentials.",
#         "network"          : "Check VPN config and network adapter. Run ipconfig/release and renew on user machine.",
#         "printer"          : "Restart print spooler service and clear print queue on user machine remotely.",
#         "email_issue"      : "Rebuild Outlook profile or repair PST file using scanpst.exe remotely.",
#         "hardware"         : "Schedule on-site engineer visit for physical hardware inspection and repair.",
#         "access_permission": "Review Active Directory group memberships and update folder/share permissions.",
#     }

#     return generic_actions.get(
#         category,
#         "Assign to engineer for manual investigation and resolution."
#     )


# def _suggest_app_install_action(text: str) -> str:
#     """Suggest specific app install action based on detected app name."""
#     app_actions = {
#         "zoom"             : "Install Zoom via winget: winget install Zoom.Zoom",
#         "teams"            : "Install Microsoft Teams via Intune or winget install Microsoft.Teams",
#         "chrome"           : "Install Google Chrome via winget: winget install Google.Chrome",
#         "office"           : "Deploy Microsoft Office via Intune or SCCM software center.",
#         "outlook"          : "Install Microsoft Outlook as part of Office 365 suite via Intune.",
#         "adobe"            : "Deploy Adobe Acrobat via Intune app catalog.",
#         "acrobat"          : "Deploy Adobe Acrobat via Intune app catalog.",
#         "anyconnect"       : "Install Cisco AnyConnect VPN client via Intune.",
#         "vpn"              : "Install and configure VPN client via Intune.",
#         "7zip"             : "Install 7-Zip via winget: winget install 7zip.7zip",
#         "notepad++"        : "Install Notepad++ via winget: winget install Notepad++.Notepad++",
#         "putty"            : "Install PuTTY via winget: winget install PuTTY.PuTTY",
#         "vlc"              : "Install VLC via winget: winget install VideoLAN.VLC",
#     }

#     for app, action in app_actions.items():
#         if app in text:
#             return action

#     return (
#         "Push software installation remotely via SCCM or Intune. "
#         "Check Intune app catalog for the requested application."
#     )


# def _suggest_antivirus_action(text: str) -> str:
#     """Suggest specific antivirus action based on detected AV product."""
#     if "symantec" in text or "sep" in text:
#         return (
#             "Update Symantec Endpoint Protection definitions remotely "
#             "via SEPM console and run full scan."
#         )
#     if "mcafee" in text:
#         return (
#             "Update McAfee DAT files remotely via ePolicy Orchestrator "
#             "and trigger full scan."
#         )
#     if "kaspersky" in text:
#         return (
#             "Update Kaspersky definitions via Kaspersky Security Center "
#             "and run full scan remotely."
#         )
#     if "sophos" in text:
#         return (
#             "Update Sophos definitions via Sophos Central "
#             "and run full scan remotely."
#         )

#     return (
#         "Update Windows Defender definitions via "
#         "Update-MpSignature PowerShell cmdlet and trigger full scan remotely."
#     )


# def _suggest_os_action(text: str) -> str:
#     """Suggest specific OS repair action based on issue keywords."""
#     if "blue screen" in text or "bsod" in text:
#         return (
#             "Check Windows Event Viewer for crash dump. "
#             "Run sfc /scannow and DISM /RestoreHealth remotely. "
#             "Check recently installed drivers/updates."
#         )
#     if "update" in text and ("fail" in text or "error" in text):
#         return (
#             "Clear Windows Update cache remotely: "
#             "stop wuauserv, delete SoftwareDistribution folder, restart. "
#             "Run Windows Update troubleshooter."
#         )
#     if "slow" in text or "performance" in text:
#         return (
#             "Run disk cleanup remotely — delete temp files and clear recycle bin. "
#             "Check startup programs and disable unnecessary ones. "
#             "Run sfc /scannow to check for corrupt system files."
#         )
#     if "disk" in text or "storage" in text or "space" in text:
#         return (
#             "Run disk cleanup remotely — delete temp files, "
#             "Windows Update cache, and recycle bin. "
#             "Check for large files using WinDirStat."
#         )

#     return (
#         "Run sfc /scannow and DISM /Online /Cleanup-Image /RestoreHealth remotely. "
#         "Clear temp files and check Event Viewer for errors."
#     )


# def _default_result() -> dict:
#     """
#     Return safe default classification result when
#     input is empty or classification completely fails.
#     """
#     return {
#         "category"        : "other",
#         "priority"        : "medium",
#         "can_auto_resolve": False,
#         "suggested_action": "Assign to engineer for manual investigation.",
#         "confidence"      : "low",
#         "scores"          : {},
#         "force_escalate"  : False,
#         "after_hours"     : _is_after_business_hours(),
#         "classified_by"   : "rules",
#     }


# def validate_ai_result(
#     ai_result    : dict,
#     subject      : str,
#     description  : str,
#     threshold    : float = 0.4,
# ) -> dict:
#     """
#     Cross-validate an AI classification result using rule-based scoring.
#     If the AI result conflicts strongly with keyword evidence,
#     the rule-based result is returned instead.

#     This function is called by ai_classifier.py to add a safety layer
#     on top of Claude's response.

#     Args:
#         ai_result   : Classification dict returned by Claude API
#         subject     : Ticket subject text
#         description : Ticket description text
#         threshold   : Minimum agreement score (0.0 to 1.0) below which
#                       the rules-based result overrides the AI result

#     Returns:
#         Final validated classification dict
#         (either the original AI result or the rules-based override)
#     """
#     rule_result = classify_by_rules(subject, description)

#     ai_category   = ai_result.get("category",  "other")
#     rule_category = rule_result.get("category", "other")

#     log.info(
#         f"Validation — AI: '{ai_category}', "
#         f"Rules: '{rule_category}'"
#     )

#     if ai_category == rule_category:
#         log.info("AI and rules agree — using AI result.")
#         return ai_result

#     scores       = rule_result.get("scores", {})
#     total_score  = sum(scores.values())
#     ai_score     = scores.get(ai_category, 0.0)
#     rule_score   = scores.get(rule_category, 0.0)

#     if total_score == 0:
#         log.info("No rule scores — keeping AI result.")
#         return ai_result

#     agreement = ai_score / total_score if total_score > 0 else 0.0

#     if (
#         rule_result.get("confidence") == "high"
#         and rule_score > ai_score * 2
#         and ai_result.get("confidence") in ["low", "medium"]
#     ):
#         log.warning(
#             f"Rules override AI — "
#             f"rule confidence HIGH with score {rule_score:.1f} "
#             f"vs AI score {ai_score:.1f}. "
#             f"Switching from '{ai_category}' to '{rule_category}'."
#         )
#         return rule_result

#     if rule_result.get("force_escalate"):
#         log.warning(
#             "Escalation trigger detected by rules — "
#             "forcing can_auto_resolve=False."
#         )
#         ai_result["can_auto_resolve"] = False
#         ai_result["force_escalate"]   = True

#     if rule_result.get("after_hours"):
#         ai_result["after_hours"] = True

#     log.info(
#         f"Keeping AI result '{ai_category}' "
#         f"(agreement score: {agreement:.2f})"
#     )
#     return ai_result


# def get_all_categories() -> list:
#     """
#     Return list of all supported ticket categories.

#     Returns:
#         List of category name strings
#     """
#     return list(CATEGORY_RULES.keys()) + ["other"]


# def get_auto_resolvable_categories() -> list:
#     """
#     Return categories that can be auto-resolved by scripts.

#     Returns:
#         List of category name strings where can_auto_resolve is True
#     """
#     return [
#         cat for cat, rules in CATEGORY_RULES.items()
#         if rules.get("can_auto_resolve", False)
#     ]


# def get_category_keywords(category: str) -> dict:
#     """
#     Return all keywords and phrases for a specific category.
#     Useful for debugging why a ticket was or was not matched.

#     Args:
#         category : Category name string

#     Returns:
#         Dict with 'keywords' and 'phrases' lists
#     """
#     rules = CATEGORY_RULES.get(category, {})
#     return {
#         "keywords" : rules.get("keywords", []),
#         "phrases"  : rules.get("phrases",  []),
#     }


# if __name__ == "__main__":
#     logging.basicConfig(
#         level  = logging.INFO,
#         format = "%(asctime)s [%(levelname)s] %(message)s"
#     )

#     print("\n" + "=" * 65)
#     print("CATEGORY RULES CLASSIFIER — TEST RUN")
#     print("=" * 65 + "\n")

#     test_tickets = [
#         {
#             "label"      : "App install — Zoom",
#             "subject"    : "Please install Zoom on my laptop urgently",
#             "description": (
#                 "Hi team, I need Zoom installed on PC-ICICI-0042. "
#                 "I have a client call in 2 hours and it is not installed. "
#                 "Please help asap."
#             ),
#         },
#         {
#             "label"      : "Antivirus — Symantec update",
#             "subject"    : "Symantec antivirus showing red error",
#             "description": (
#                 "My Symantec antivirus is showing a red warning. "
#                 "The virus definitions are out of date. "
#                 "I tried updating manually but it fails every time. "
#                 "Machine: LAPTOP-ICICI-115"
#             ),
#         },
#         {
#             "label"      : "Password reset",
#             "subject"    : "Cannot login — account locked out",
#             "description": (
#                 "I forgot my password and now my account is locked. "
#                 "I tried 5 times and it says account is locked. "
#                 "Please reset my password urgently — I cannot work."
#             ),
#         },
#         {
#             "label"      : "Network — VPN issue",
#             "subject"    : "VPN not connecting from home",
#             "description": (
#                 "Since this morning I am unable to connect to VPN. "
#                 "Cisco AnyConnect shows connection timed out. "
#                 "My colleagues are able to connect fine."
#             ),
#         },
#         {
#             "label"      : "Hardware issue",
#             "subject"    : "Laptop screen is flickering badly",
#             "description": (
#                 "My laptop screen has been flickering since morning. "
#                 "Sometimes it goes completely blank. "
#                 "I think the display is physically damaged."
#             ),
#         },
#         {
#             "label"      : "OS issue — BSOD",
#             "subject"    : "Blue screen of death — Windows crashing",
#             "description": (
#                 "My computer is getting blue screen error repeatedly. "
#                 "It crashes and restarts automatically every 30 minutes. "
#                 "Windows 10 system. Machine WS-ICICI-202."
#             ),
#         },
#         {
#             "label"      : "Email — Outlook not working",
#             "subject"    : "Outlook not opening this morning",
#             "description": (
#                 "Outlook is not opening. It shows an error about "
#                 "a corrupt PST file. I cannot send or receive emails. "
#                 "This is very urgent as I have client emails."
#             ),
#         },
#         {
#             "label"      : "Security escalation trigger",
#             "subject"    : "Ransomware detected on my computer",
#             "description": (
#                 "I think my computer has ransomware. "
#                 "Files are being encrypted and I can see a ransom note. "
#                 "This is a data breach emergency. "
#                 "Please help immediately."
#             ),
#         },
#         {
#             "label"      : "After hours — low priority",
#             "subject"    : "Minor display issue — no rush",
#             "description": (
#                 "When possible, can you look at the font size in my "
#                 "taskbar? It is a bit small. Not urgent at all. "
#                 "Please check whenever you get a chance."
#             ),
#         },
#     ]

#     print(f"{'LABEL':<35} {'CATEGORY':<20} {'PRIORITY':<10} "
#           f"{'AUTO':<7} {'CONF':<8} {'ESCALATE'}")
#     print("-" * 95)

#     for t in test_tickets:
#         result = classify_by_rules(t["subject"], t["description"])
#         print(
#             f"{t['label']:<35} "
#             f"{result['category']:<20} "
#             f"{result['priority']:<10} "
#             f"{str(result['can_auto_resolve']):<7} "
#             f"{result['confidence']:<8} "
#             f"{str(result['force_escalate'])}"
#         )

#     print("\n" + "-" * 65)
#     print("Auto-resolvable categories:")
#     for cat in get_auto_resolvable_categories():
#         print(f"  {cat}")

#     print("\nAll categories:")
#     for cat in get_all_categories():
#         print(f"  {cat}")

#     print("\nKeywords for 'app_install' category:")
#     kw = get_category_keywords("app_install")
#     print(f"  Keywords : {len(kw['keywords'])} defined")
#     print(f"  Phrases  : {len(kw['phrases'])} defined")

#     print("\nAll tests complete.")


# import os
# import logging
# from datetime import datetime, timezone
# from dotenv   import load_dotenv

# load_dotenv("config/.env")

# log = logging.getLogger(__name__)

# DEMO_MODE           = os.getenv("DEMO_MODE",           "false").strip().lower() == "true"
# DRY_RUN_MODE        = os.getenv("DRY_RUN_MODE",        "false").strip().lower() == "true"
# ESCALATION_AGENT_ID = int(os.getenv("ESCALATION_AGENT_ID", 0))
# COMPANY_NAME        = os.getenv("COMPANY_NAME",        "ICICI Bank")
# FEATURE_KB_SEARCH   = os.getenv("FEATURE_KB_SEARCH",   "true").strip().lower() == "true"

# from automation.runner      import run_automation
# from knowledge_base.kb_search import (
#     search_knowledge_base,
#     is_kb_available,
# )
# from agent.escalation import escalate_ticket
# from agent.notifier   import notify_user
# from database.db_logger import log_ticket_action
# from ingestion.freshdesk_client import (
#     close_ticket,
#     update_ticket_status,
#     add_internal_note,
#     add_public_reply,
#     add_tag_to_ticket,
#     set_ticket_priority,
# )


# def _now() -> str:
#     """
#     Return current UTC time as a formatted string.
#     Uses timezone-aware datetime to avoid deprecation warning.

#     Returns:
#         Formatted datetime string e.g. '17 May 2026 10:30 UTC'
#     """
#     return datetime.now(timezone.utc).strftime(
#         "%d %b %Y %H:%M UTC"
#     )


# def orchestrate(ticket: dict, classification: dict) -> bool:
#     """
#     Main orchestrator called by main.py for every ticket.
#     Decides the full resolution path and executes it end to end.
#     In demo mode uses real logic but with simulated API calls.

#     Decision flow:
#         1. Validate ticket has minimum required data
#         2. Update Freshdesk priority to match AI classification
#         3. Tag ticket with AI classification metadata
#         4. If can_auto_resolve → try automation scripts
#            a. Success  → close ticket + notify user
#            b. Failure  → search KB → send guide or escalate
#         5. If cannot auto_resolve → search KB → send guide + escalate
#         6. Log all actions to database

#     Args:
#         ticket         : Clean parsed ticket dict from ticket_parser
#         classification : Classification dict from ai_classifier

#     Returns:
#         True if ticket was fully auto-resolved
#         False if ticket was escalated or resolution failed
#     """
#     ticket_id      = ticket.get("id",              0)
#     subject        = ticket.get("subject",         "No subject")
#     requester      = ticket.get("requester_email", "")
#     requester_name = ticket.get("requester_name",  "User")
#     machine        = ticket.get("machine_name",    "UNKNOWN")
#     category       = classification.get("category",         "other")
#     priority       = classification.get("priority",         "medium")
#     can_auto       = classification.get("can_auto_resolve", False)
#     action         = classification.get(
#         "suggested_action", "Manual review required."
#     )
#     confidence     = classification.get("confidence", "low")

#     mode = "[DEMO] " if DEMO_MODE else ""

#     log.info("")
#     log.info("=" * 55)
#     log.info(
#         f"{mode}ORCHESTRATING TICKET #{ticket_id}"
#     )
#     log.info(f"  Subject    : {subject[:55]}")
#     log.info(f"  Category   : {category}")
#     log.info(f"  Priority   : {priority}")
#     log.info(f"  Auto       : {can_auto}")
#     log.info(f"  Machine    : {machine}")
#     log.info(f"  Confidence : {confidence}")
#     log.info("=" * 55)

#     if not _validate_ticket(ticket):
#         log.error(
#             f"Ticket #{ticket_id} failed validation. "
#             "Escalating."
#         )
#         _handle_escalation(
#             ticket         = ticket,
#             classification = classification,
#             reason         = (
#                 "Ticket data incomplete — needs manual review."
#             ),
#             tag            = "validation-failed",
#         )
#         return False

#     _sync_priority_to_freshdesk(ticket_id, priority)
#     _tag_ticket(ticket_id, category, confidence)

#     if can_auto:
#         return _handle_auto_resolve(ticket, classification)
#     else:
#         return _handle_manual_escalation(ticket, classification)


# def _handle_auto_resolve(
#     ticket        : dict,
#     classification: dict,
# ) -> bool:
#     """
#     Attempt to auto-resolve via automation scripts.
#     On success → close ticket and notify user.
#     On failure → search KB and escalate.
#     In demo mode uses simulated automation results.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict

#     Returns:
#         True if resolved, False if escalated
#     """
#     ticket_id      = ticket.get("id",              0)
#     subject        = ticket.get("subject",         "")
#     requester      = ticket.get("requester_email", "")
#     requester_name = ticket.get("requester_name",  "User")
#     category       = classification.get("category", "other")
#     priority       = classification.get("priority", "medium")
#     action         = classification.get(
#         "suggested_action", ""
#     )

#     mode = "[DEMO] " if DEMO_MODE else ""
#     log.info(
#         f"{mode}Ticket #{ticket_id}: "
#         "Attempting auto-resolution..."
#     )

#     add_internal_note(
#         ticket_id,
#         f"[AI Orchestrator — {_now()}]\n"
#         f"Auto-resolution started.\n"
#         f"Category : {category}\n"
#         f"Action   : {action}\n"
#         f"Machine  : {ticket.get('machine_name', 'UNKNOWN')}"
#     )

#     success = run_automation(ticket, classification)

#     if success:
#         log.info(
#             f"{mode}Ticket #{ticket_id}: "
#             "Auto-resolution SUCCEEDED ✓"
#         )

#         resolution_message = _build_resolution_message(
#             requester_name = requester_name,
#             subject        = subject,
#             action         = action,
#             category       = category,
#         )

#         if not DRY_RUN_MODE:
#             close_ticket(ticket_id, action)

#         notify_user(
#             email      = requester,
#             ticket_id  = ticket_id,
#             subject    = subject,
#             message    = resolution_message,
#             notif_type = "resolved",
#         )

#         if not DRY_RUN_MODE:
#             add_public_reply(ticket_id, resolution_message)

#         add_tag_to_ticket(
#             ticket_id,
#             ["ai-resolved", f"cat-{category}", "auto-closed"]
#         )

#         try:
#             log_ticket_action(
#                 ticket_id    = ticket_id,
#                 category     = category,
#                 priority     = priority,
#                 action_taken = action,
#                 resolved_by  = "AI_AUTO",
#                 status       = "RESOLVED",
#             )
#         except Exception as e:
#             log.warning(
#                 f"DB log failed for ticket #{ticket_id}: {e}"
#             )

#         log.info(
#             f"{mode}Ticket #{ticket_id}: "
#             "Closed and user notified."
#         )
#         return True

#     else:
#         log.warning(
#             f"{mode}Ticket #{ticket_id}: "
#             "Auto-resolution FAILED — searching KB..."
#         )

#         add_internal_note(
#             ticket_id,
#             f"[AI Orchestrator — {_now()}]\n"
#             f"Auto-resolution FAILED.\n"
#             f"Searching KB for: {subject}"
#         )

#         kb_guide = None
#         if FEATURE_KB_SEARCH and is_kb_available():
#             try:
#                 kb_guide = search_knowledge_base(
#                     ticket.get("description", "")
#                 )
#             except Exception as e:
#                 log.warning(
#                     f"KB search error for ticket #{ticket_id}: {e}"
#                 )

#         if kb_guide:
#             log.info(
#                 f"{mode}Ticket #{ticket_id}: "
#                 "KB guide found — sending to user."
#             )

#             kb_message = _build_kb_message(
#                 requester_name = requester_name,
#                 subject        = subject,
#                 guide          = kb_guide,
#             )

#             if not DRY_RUN_MODE:
#                 add_public_reply(ticket_id, kb_message)

#             notify_user(
#                 email      = requester,
#                 ticket_id  = ticket_id,
#                 subject    = subject,
#                 message    = kb_message,
#                 notif_type = "kb_guide_sent",
#             )

#             _handle_escalation(
#                 ticket         = ticket,
#                 classification = classification,
#                 reason         = (
#                     f"Auto-resolution failed. "
#                     f"KB guide sent to user.\n"
#                     f"Engineer — please verify fix applied.\n"
#                     f"Suggested: {action}"
#                 ),
#                 tag            = "auto-failed-kb-sent",
#             )

#             try:
#                 log_ticket_action(
#                     ticket_id    = ticket_id,
#                     category     = category,
#                     priority     = priority,
#                     action_taken = "Auto-resolve failed. KB guide sent.",
#                     resolved_by  = "KB+ESCALATION",
#                     status       = "ESCALATED",
#                 )
#             except Exception as e:
#                 log.warning(
#                     f"DB log failed for ticket #{ticket_id}: {e}"
#                 )

#         else:
#             log.warning(
#                 f"{mode}Ticket #{ticket_id}: "
#                 "No KB guide found — escalating."
#             )

#             _handle_escalation(
#                 ticket         = ticket,
#                 classification = classification,
#                 reason         = (
#                     f"Auto-resolution failed. "
#                     f"No KB guide found.\n"
#                     f"Suggested: {action}"
#                 ),
#                 tag            = "auto-failed-no-kb",
#             )

#             try:
#                 log_ticket_action(
#                     ticket_id    = ticket_id,
#                     category     = category,
#                     priority     = priority,
#                     action_taken = "Auto-resolve failed. Escalated.",
#                     resolved_by  = "ESCALATION",
#                     status       = "ESCALATED",
#                 )
#             except Exception as e:
#                 log.warning(
#                     f"DB log failed for ticket #{ticket_id}: {e}"
#                 )

#         return False


# def _handle_manual_escalation(
#     ticket        : dict,
#     classification: dict,
# ) -> bool:
#     """
#     Handle tickets that cannot be auto-resolved.
#     Searches KB first to send self-help guide, then escalates.
#     In demo mode uses real KB index if available.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict

#     Returns:
#         Always False — ticket is not auto-resolved
#     """
#     ticket_id      = ticket.get("id",              0)
#     subject        = ticket.get("subject",         "")
#     requester      = ticket.get("requester_email", "")
#     requester_name = ticket.get("requester_name",  "User")
#     category       = classification.get("category", "other")
#     priority       = classification.get("priority", "medium")
#     action         = classification.get(
#         "suggested_action", ""
#     )

#     mode = "[DEMO] " if DEMO_MODE else ""
#     log.info(
#         f"{mode}Ticket #{ticket_id}: "
#         "Cannot auto-resolve — searching KB..."
#     )

#     add_internal_note(
#         ticket_id,
#         f"[AI Orchestrator — {_now()}]\n"
#         f"Cannot auto-resolve — routing to engineer.\n"
#         f"Category : {category}\n"
#         f"Action   : {action}"
#     )

#     kb_guide = None
#     if FEATURE_KB_SEARCH and is_kb_available():
#         try:
#             kb_guide = search_knowledge_base(
#                 ticket.get("description", "")
#             )
#         except Exception as e:
#             log.warning(
#                 f"KB search error for ticket #{ticket_id}: {e}"
#             )

#     if kb_guide:
#         log.info(
#             f"{mode}Ticket #{ticket_id}: "
#             "KB guide found — sending to user."
#         )

#         kb_message = _build_kb_message(
#             requester_name = requester_name,
#             subject        = subject,
#             guide          = kb_guide,
#         )

#         if not DRY_RUN_MODE:
#             add_public_reply(ticket_id, kb_message)

#         notify_user(
#             email      = requester,
#             ticket_id  = ticket_id,
#             subject    = subject,
#             message    = kb_message,
#             notif_type = "kb_guide_sent",
#         )

#         escalation_note = (
#             f"KB self-help guide sent to user.\n"
#             f"Engineer — please verify issue resolved.\n"
#             f"Category : {category}\n"
#             f"Suggested: {action}"
#         )
#         resolved_by = "KB+ESCALATION"

#     else:
#         log.info(
#             f"{mode}Ticket #{ticket_id}: "
#             "No KB guide — escalating directly."
#         )
#         escalation_note = (
#             f"No KB guide found for this issue.\n"
#             f"Category : {category}\n"
#             f"Suggested: {action}"
#         )
#         resolved_by = "ENGINEER_QUEUE"

#     _handle_escalation(
#         ticket         = ticket,
#         classification = classification,
#         reason         = escalation_note,
#         tag            = "manual-escalation",
#     )

#     try:
#         log_ticket_action(
#             ticket_id    = ticket_id,
#             category     = category,
#             priority     = priority,
#             action_taken = (
#                 f"KB guide sent + escalated. {action}"
#                 if kb_guide else
#                 f"Escalated — {action}"
#             ),
#             resolved_by  = resolved_by,
#             status       = "ESCALATED",
#         )
#     except Exception as e:
#         log.warning(
#             f"DB log failed for ticket #{ticket_id}: {e}"
#         )

#     return False


# def _handle_escalation(
#     ticket        : dict,
#     classification: dict,
#     reason        : str,
#     tag           : str = "escalated",
# ) -> None:
#     """
#     Escalate a ticket to the engineer queue.
#     Updates status, adds internal note, assigns agent, tags ticket.
#     In demo mode simulates all Freshdesk API calls.

#     Args:
#         ticket         : Parsed ticket dict
#         classification : Classification result dict
#         reason         : Why escalation is happening
#         tag            : Freshdesk tag to apply
#     """
#     ticket_id = ticket.get("id", 0)
#     category  = classification.get("category", "other")

#     mode = "[DEMO] " if DEMO_MODE else ""

#     try:
#         escalate_ticket(
#             ticket_id = ticket_id,
#             note      = reason,
#             agent_id  = (
#                 ESCALATION_AGENT_ID
#                 if ESCALATION_AGENT_ID and ESCALATION_AGENT_ID != 0
#                 else None
#             ),
#         )
#     except Exception as e:
#         log.warning(
#             f"Escalation API call failed for "
#             f"ticket #{ticket_id}: {e}"
#         )

#     try:
#         add_tag_to_ticket(
#             ticket_id,
#             [tag, f"cat-{category}", "ai-processed"]
#         )
#     except Exception as e:
#         log.warning(
#             f"Tag failed for ticket #{ticket_id}: {e}"
#         )

#     log.info(
#         f"{mode}Ticket #{ticket_id}: "
#         f"Escalated — {reason[:80]}"
#     )


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
#         log.error("Ticket has no ID — cannot process.")
#         return False

#     if not ticket.get("subject", "").strip():
#         log.warning(
#             f"Ticket #{ticket_id} has no subject."
#         )

#     if not ticket.get("description", "").strip():
#         log.warning(
#             f"Ticket #{ticket_id} has no description."
#         )

#     if not ticket.get("requester_email", "").strip():
#         log.error(
#             f"Ticket #{ticket_id} has no requester email. "
#             "Cannot notify user."
#         )
#         return False

#     return True


# def _sync_priority_to_freshdesk(
#     ticket_id  : int,
#     ai_priority: str,
# ) -> None:
#     """
#     Update Freshdesk ticket priority to match AI classification.
#     In demo mode simulates the update without real API call.

#     Args:
#         ticket_id   : Freshdesk ticket ID
#         ai_priority : Priority from classifier — low/medium/high/urgent
#     """
#     valid_priorities = {"low", "medium", "high", "urgent"}
#     fd_priority      = (
#         ai_priority if ai_priority in valid_priorities
#         else "medium"
#     )

#     try:
#         set_ticket_priority(ticket_id, fd_priority)
#         log.info(
#             f"Ticket #{ticket_id}: Priority set to "
#             f"'{fd_priority}' in Freshdesk."
#         )
#     except Exception as e:
#         log.warning(
#             f"Priority sync failed for ticket #{ticket_id}: {e}"
#         )


# def _tag_ticket(
#     ticket_id : int,
#     category  : str,
#     confidence: str,
# ) -> None:
#     """
#     Add AI-generated tags to the ticket in Freshdesk.
#     Tags help with filtering and reporting.
#     In demo mode stores tags in the demo tag store.

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

#     try:
#         add_tag_to_ticket(ticket_id, tags)
#         log.debug(
#             f"Ticket #{ticket_id}: Tagged with {tags}"
#         )
#     except Exception as e:
#         log.warning(
#             f"Tagging failed for ticket #{ticket_id}: {e}"
#         )


# def _build_resolution_message(
#     requester_name: str,
#     subject       : str,
#     action        : str,
#     category      : str,
# ) -> str:
#     """
#     Build the email/reply message sent to the user when
#     their ticket is auto-resolved.

#     Args:
#         requester_name : Name of the user
#         subject        : Ticket subject
#         action         : What action was taken
#         category       : Ticket category

#     Returns:
#         Formatted message string
#     """
#     category_labels = {
#         "app_install"    : "software installation",
#         "antivirus"      : "antivirus update",
#         "password_reset" : "password reset",
#         "os_issue"       : "system repair",
#         "printer"        : "printer fix",
#         "email_issue"    : "email repair",
#         "network"        : "network fix",
#         "other"          : "issue resolution",
#     }

#     label = category_labels.get(category, "issue resolution")

#     message = (
#         f"Dear {requester_name},\n\n"
#         f"Your ticket '{subject}' has been automatically "
#         f"resolved by our AI support system.\n\n"
#         f"Action taken: {action}\n\n"
#         f"Your {label} has been completed remotely on your "
#         f"machine. Please restart your computer if required "
#         f"and verify the issue is resolved.\n\n"
#         f"If you are still facing any issues, please raise "
#         f"a new ticket and our team will assist you promptly.\n\n"
#         f"Resolved by  : AI Auto-Resolver\n"
#         f"Resolved at  : {_now()}\n\n"
#         f"Thank you,\n"
#         f"IT Support Team\n"
#         f"{COMPANY_NAME}"
#     )

#     return message


# def _build_kb_message(
#     requester_name: str,
#     subject       : str,
#     guide         : str,
# ) -> str:
#     """
#     Build the email/reply message sent to the user when
#     a knowledge base guide is found for their issue.

#     Args:
#         requester_name : Name of the user
#         subject        : Ticket subject
#         guide          : KB guide content text

#     Returns:
#         Formatted message string
#     """
#     message = (
#         f"Dear {requester_name},\n\n"
#         f"Thank you for raising a ticket regarding "
#         f"'{subject}'.\n\n"
#         f"We found a self-help guide that may resolve "
#         f"your issue:\n\n"
#         f"{'─' * 50}\n"
#         f"{guide}\n"
#         f"{'─' * 50}\n\n"
#         f"Please follow the steps above and let us know "
#         f"if this resolves the issue.\n\n"
#         f"If the problem persists, an engineer will follow "
#         f"up with you shortly.\n\n"
#         f"Thank you,\n"
#         f"IT Support Team\n"
#         f"{COMPANY_NAME}"
#     )

#     return message


# # if __name__ == "__main__":
# #     import sys
# #     sys.path.insert(
# #         0,
# #         os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# #     )

# #     logging.basicConfig(
# #         level  = logging.INFO,
# #         format = "%(asctime)s [%(levelname)s] %(message)s",
# #     )

# #     print("\n" + "=" * 60)
# #     print("ORCHESTRATOR TEST RUN")
# #     print("=" * 60)
# #     print(
# #         f"  Mode         : "
# #         f"{'DEMO' if DEMO_MODE else 'LIVE'}"
# #     )
# #     print(
# #         f"  Dry run      : "
# #         f"{'YES' if DRY_RUN_MODE else 'NO'}"
# #     )
# #     print(f"  KB search    : {FEATURE_KB_SEARCH}")
# #     print(f"  Company      : {COMPANY_NAME}")
# #     print(f"  Agent ID     : {ESCALATION_AGENT_ID or 'not set'}")
# #     print()

# #     test_cases = [
# #         {
# #             "label"          : "Auto-resolvable — App Install",
# #             "ticket"         : {
# #                 "id"              : 1001,
# #                 "subject"         : "Install Zoom on my laptop",
# #                 "description"     : (
# #                     "I need Zoom installed on PC-ICICI-0042 urgently. "
# #                     "Client call in 2 hours."
# #                 ),
# #                 "requester_email" : "rahul.sharma@icici.com",
# #                 "requester_name"  : "Rahul Sharma",
# #                 "machine_name"    : "PC-ICICI-0042",
# #                 "mentioned_apps"  : ["zoom"],
# #                 "urgency_level"   : "high",
# #             },
# #             "classification" : {
# #                 "category"        : "app_install",
# #                 "priority"        : "high",
# #                 "can_auto_resolve": True,
# #                 "suggested_action": "Push Zoom installation via SCCM.",
# #                 "confidence"      : "high",
# #             },
# #         },
# #         {
# #             "label"          : "Non-auto — Hardware Issue",
# #             "ticket"         : {
# #                 "id"              : 1002,
# #                 "subject"         : "Laptop screen is flickering",
# #                 "description"     : (
# #                     "My laptop screen has been flickering since morning. "
# #                     "I think it might be physical damage."
# #                 ),
# #                 "requester_email" : "priya.mehta@icici.com",
# #                 "requester_name"  : "Priya Mehta",
# #                 "machine_name"    : "LAPTOP-ICICI-115",
# #                 "mentioned_apps"  : [],
# #                 "urgency_level"   : "medium",
# #             },
# #             "classification" : {
# #                 "category"        : "hardware",
# #                 "priority"        : "medium",
# #                 "can_auto_resolve": False,
# #                 "suggested_action": "Schedule on-site hardware inspection.",
# #                 "confidence"      : "high",
# #             },
# #         },
# #         {
# #             "label"          : "Non-auto — VPN (KB guide expected)",
# #             "ticket"         : {
# #                 "id"              : 1003,
# #                 "subject"         : "Cannot connect to VPN from home",
# #                 "description"     : (
# #                     "I cannot connect to VPN. Cisco AnyConnect shows "
# #                     "connection timed out. Please help."
# #                 ),
# #                 "requester_email" : "amit.patel@icici.com",
# #                 "requester_name"  : "Amit Patel",
# #                 "machine_name"    : "LAPTOP-ICICI-088",
# #                 "mentioned_apps"  : ["anyconnect"],
# #                 "urgency_level"   : "high",
# #             },
# #             "classification" : {
# #                 "category"        : "network",
# #                 "priority"        : "high",
# #                 "can_auto_resolve": False,
# #                 "suggested_action": "Check VPN config and escalate.",
# #                 "confidence"      : "high",
# #             },
# #         },
# #         {
# #             "label"          : "Validation fail — Missing email",
# #             "ticket"         : {
# #                 "id"              : 1004,
# #                 "subject"         : "Cannot print documents",
# #                 "description"     : "Printer is showing offline.",
# #                 "requester_email" : "",
# #                 "requester_name"  : "Unknown",
# #                 "machine_name"    : "PC-ICICI-0099",
# #                 "mentioned_apps"  : [],
# #                 "urgency_level"   : "low",
# #             },
# #             "classification" : {
# #                 "category"        : "printer",
# #                 "priority"        : "low",
# #                 "can_auto_resolve": True,
# #                 "suggested_action": "Restart print spooler remotely.",
# #                 "confidence"      : "medium",
# #             },
# #         },
# #     ]

# #     resolved_count  = 0
# #     escalated_count = 0

# #     for tc in test_cases:
# #         print(f"\n--- Test: {tc['label']} ---")
# #         print(
# #             f"  Ticket  : "
# #             f"#{tc['ticket']['id']} — {tc['ticket']['subject']}"
# #         )
# #         print(
# #             f"  Category: "
# #             f"{tc['classification']['category']}"
# #         )
# #         print(
# #             f"  Auto    : "
# #             f"{tc['classification']['can_auto_resolve']}"
# #         )

# #         result = orchestrate(tc["ticket"], tc["classification"])

# #         outcome = "RESOLVED ✓" if result else "ESCALATED →"
# #         print(f"  Result  : {outcome}")
# #         print("-" * 55)

# #         if result:
# #             resolved_count += 1
# #         else:
# #             escalated_count += 1

# #     print(f"\n{'=' * 60}")
# #     print("ORCHESTRATOR TEST SUMMARY")
# #     print(f"{'=' * 60}")
# #     total = len(test_cases)
# #     print(f"  Total    : {total}")
# #     print(f"  Resolved : {resolved_count}")
# #     print(f"  Escalated: {escalated_count}")
# #     rate = round(resolved_count / total * 100, 1)
# #     print(f"  Rate     : {rate}%")
# #     print(f"{'=' * 60}\n")


# if __name__ == "__main__":
#     logging.basicConfig(
#         level  = logging.INFO,
#         format = "%(asctime)s [%(levelname)s] %(message)s",
#     )

#     print("\n" + "=" * 65)
#     print("CATEGORY RULES CLASSIFIER — TEST RUN")
#     print("=" * 65)
#     print(
#         f"  Mode             : "
#         f"{'DEMO' if DEMO_MODE else 'LIVE'}"
#     )
#     print(f"  Business hours   : "
#           f"{BUSINESS_HOURS_START}:00 – "
#           f"{BUSINESS_HOURS_END}:00 IST")
#     print(
#         f"  Currently after hours: "
#         f"{_is_after_business_hours()}"
#     )
#     print(
#         f"  UTC now          : "
#         f"{datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
#     )
#     print()

#     test_tickets = [
#         {
#             "label"      : "App install — Zoom",
#             "subject"    : "Please install Zoom on my laptop urgently",
#             "description": (
#                 "Hi team, I need Zoom installed on PC-ICICI-0042. "
#                 "I have a client call in 2 hours. Please help asap."
#             ),
#         },
#         {
#             "label"      : "Antivirus — Symantec update",
#             "subject"    : "Symantec antivirus showing red error",
#             "description": (
#                 "My Symantec antivirus is showing a red warning. "
#                 "Virus definitions are out of date. "
#                 "Machine: LAPTOP-ICICI-115"
#             ),
#         },
#         {
#             "label"      : "Password reset",
#             "subject"    : "Cannot login — account locked out",
#             "description": (
#                 "I forgot my password and my account is locked. "
#                 "I tried 5 times. Please reset — I cannot work."
#             ),
#         },
#         {
#             "label"      : "Network — VPN issue",
#             "subject"    : "VPN not connecting from home",
#             "description": (
#                 "Since morning I am unable to connect to VPN. "
#                 "Cisco AnyConnect shows connection timed out."
#             ),
#         },
#         {
#             "label"      : "Hardware issue",
#             "subject"    : "Laptop screen is flickering badly",
#             "description": (
#                 "My laptop screen has been flickering since morning. "
#                 "I think the display is physically damaged."
#             ),
#         },
#         {
#             "label"      : "OS issue — BSOD",
#             "subject"    : "Blue screen of death — Windows crashing",
#             "description": (
#                 "My computer is getting blue screen repeatedly. "
#                 "It crashes and restarts every 30 minutes."
#             ),
#         },
#         {
#             "label"      : "Email — Outlook",
#             "subject"    : "Outlook not opening this morning",
#             "description": (
#                 "Outlook shows a corrupt PST file error. "
#                 "I cannot send or receive emails. Very urgent."
#             ),
#         },
#         {
#             "label"      : "Security — Force escalation",
#             "subject"    : "Ransomware detected on my computer",
#             "description": (
#                 "Files are being encrypted. I see a ransom note. "
#                 "This is a data breach emergency."
#             ),
#         },
#         {
#             "label"      : "Low priority — no rush",
#             "subject"    : "Minor display issue — no rush",
#             "description": (
#                 "When possible, can you look at my taskbar font? "
#                 "Not urgent at all. Whenever you get a chance."
#             ),
#         },
#         {
#             "label"      : "Printer offline",
#             "subject"    : "Printer offline — cannot print",
#             "description": (
#                 "My printer is showing as offline. "
#                 "Print queue is stuck. Machine: WS-ICICI-201."
#             ),
#         },
#     ]

#     print(
#         f"{'#':<4} "
#         f"{'LABEL':<30} "
#         f"{'CATEGORY':<20} "
#         f"{'PRI':<10} "
#         f"{'AUTO':<7} "
#         f"{'CONF':<8} "
#         f"{'ESCALATE'}"
#     )
#     print("-" * 95)

#     for i, t in enumerate(test_tickets, start=1):
#         result = classify_by_rules(
#             t["subject"], t["description"]
#         )
#         print(
#             f"{i:<4} "
#             f"{t['label']:<30} "
#             f"{result['category']:<20} "
#             f"{result['priority']:<10} "
#             f"{str(result['can_auto_resolve']):<7} "
#             f"{result['confidence']:<8} "
#             f"{str(result['force_escalate'])}"
#         )

#     print("\n" + "-" * 65)
#     print("Auto-resolvable categories:")
#     for cat in get_auto_resolvable_categories():
#         print(f"  {cat}")

#     print("\nAll categories:")
#     for cat in get_all_categories():
#         print(f"  {cat}")

#     print("\nKeywords for 'app_install':")
#     kw = get_category_keywords("app_install")
#     print(f"  Keywords : {len(kw['keywords'])} defined")
#     print(f"  Phrases  : {len(kw['phrases'])} defined")

#     print("\nEscalation triggers:")
#     for trigger in ESCALATION_TRIGGERS:
#         print(f"  {trigger}")

#     print("\n" + "=" * 65)
#     print("All tests complete.")
#     print("=" * 65 + "\n")



import os
import sys
import logging
from datetime import datetime, timezone
from dotenv   import load_dotenv

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE           = os.getenv("DEMO_MODE",           "false").strip().lower() == "true"
DRY_RUN_MODE        = os.getenv("DRY_RUN_MODE",        "false").strip().lower() == "true"
ESCALATION_AGENT_ID = int(os.getenv("ESCALATION_AGENT_ID", 0))
COMPANY_NAME        = os.getenv("COMPANY_NAME",        "ICICI Bank")
FEATURE_KB_SEARCH   = os.getenv("FEATURE_KB_SEARCH",   "true").strip().lower() == "true"

from automation.runner        import run_automation
from knowledge_base.kb_search import (
    search_knowledge_base,
    is_kb_available,
)
from agent.escalation         import escalate_ticket
from agent.notifier           import notify_user
from database.db_logger       import log_ticket_action
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
    log.info(f"{mode}ORCHESTRATING TICKET #{ticket_id}")
    log.info(f"  Subject    : {subject[:55]}")
    log.info(f"  Category   : {category}")
    log.info(f"  Priority   : {priority}")
    log.info(f"  Auto       : {can_auto}")
    log.info(f"  Machine    : {machine}")
    log.info(f"  Confidence : {confidence}")
    log.info("=" * 55)

    if not _validate_ticket(ticket):
        log.error(
            f"Ticket #{ticket_id} failed validation. Escalating."
        )
        _handle_escalation(
            ticket         = ticket,
            classification = classification,
            reason         = "Ticket data incomplete — needs manual review.",
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
    action         = classification.get("suggested_action", "")

    mode = "[DEMO] " if DEMO_MODE else ""
    log.info(
        f"{mode}Ticket #{ticket_id}: Attempting auto-resolution..."
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
            f"{mode}Ticket #{ticket_id}: Auto-resolution SUCCEEDED ✓"
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
            f"{mode}Ticket #{ticket_id}: Closed and user notified."
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
                    f"Auto-resolution failed. KB guide sent to user.\n"
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
                    f"Auto-resolution failed. No KB guide found.\n"
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
    action         = classification.get("suggested_action", "")

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
    mode      = "[DEMO] " if DEMO_MODE else ""

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
            f"Escalation API call failed for ticket #{ticket_id}: {e}"
        )

    try:
        add_tag_to_ticket(
            ticket_id,
            [tag, f"cat-{category}", "ai-processed"]
        )
    except Exception as e:
        log.warning(f"Tag failed for ticket #{ticket_id}: {e}")

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
        log.warning(f"Ticket #{ticket_id} has no subject.")

    if not ticket.get("description", "").strip():
        log.warning(f"Ticket #{ticket_id} has no description.")

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
        ai_priority : Priority from classifier
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

    Args:
        ticket_id  : Freshdesk ticket ID
        category   : Classified category string
        confidence : Classifier confidence level
    """
    tags = [
        "ai-classified",
        f"cat-{category}",
        f"confidence-{confidence}",
    ]

    try:
        add_tag_to_ticket(ticket_id, tags)
        log.debug(f"Ticket #{ticket_id}: Tagged with {tags}")
    except Exception as e:
        log.warning(f"Tagging failed for ticket #{ticket_id}: {e}")


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

    return (
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


def _build_kb_message(
    requester_name: str,
    subject       : str,
    guide         : str,
) -> str:
    """
    Build the email/reply message sent to the user when
    a KB guide is found for their issue.

    Args:
        requester_name : Name of the user
        subject        : Ticket subject
        guide          : KB guide content text

    Returns:
        Formatted message string
    """
    return (
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


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
    )

    print("\n" + "=" * 60)
    print("ORCHESTRATOR TEST RUN")
    print("=" * 60)
    print(
        f"  Mode     : {'DEMO' if DEMO_MODE else 'LIVE'}"
    )
    print(
        f"  Dry run  : {'YES' if DRY_RUN_MODE else 'NO'}"
    )
    print(f"  KB search: {FEATURE_KB_SEARCH}")
    print(f"  Company  : {COMPANY_NAME}")
    print(f"  Agent ID : {ESCALATION_AGENT_ID or 'not set'}")
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
        print(f"  Category: {tc['classification']['category']}")
        print(f"  Auto    : {tc['classification']['can_auto_resolve']}")

        result  = orchestrate(tc["ticket"], tc["classification"])
        outcome = "RESOLVED ✓" if result else "ESCALATED →"
        print(f"  Result  : {outcome}")
        print("-" * 55)

        if result:
            resolved_count += 1
        else:
            escalated_count += 1

    total = len(test_cases)
    rate  = round(resolved_count / total * 100, 1)

    print(f"\n{'=' * 60}")
    print("ORCHESTRATOR TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total    : {total}")
    print(f"  Resolved : {resolved_count}")
    print(f"  Escalated: {escalated_count}")
    print(f"  Rate     : {rate}%")
    print(f"{'=' * 60}\n")