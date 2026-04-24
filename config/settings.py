import os
import logging
from pathlib import Path
from dotenv  import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_env(key: str, default=None, required: bool = False):
    """
    Safely read an environment variable.
    Logs a warning if a required variable is missing.

    Args:
        key      : Environment variable name
        default  : Default value if not set
        required : If True logs warning when missing

    Returns:
        Value string or default
    """
    value = os.getenv(key, default)
    if required and not value:
        log.warning(
            f"Required setting '{key}' is not set in .env file. "
            f"Using default: '{default}'"
        )
    return value


def _get_int(key: str, default: int) -> int:
    """
    Read an environment variable as integer.
    Falls back to default if value is missing or not a valid int.

    Args:
        key     : Environment variable name
        default : Default integer value

    Returns:
        Integer value
    """
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        log.warning(
            f"Invalid integer value for '{key}'. "
            f"Using default: {default}"
        )
        return default


def _get_float(key: str, default: float) -> float:
    """
    Read an environment variable as float.
    Falls back to default if value is missing or not valid.

    Args:
        key     : Environment variable name
        default : Default float value

    Returns:
        Float value
    """
    try:
        return float(os.getenv(key, default))
    except (ValueError, TypeError):
        log.warning(
            f"Invalid float value for '{key}'. "
            f"Using default: {default}"
        )
        return default


def _get_bool(key: str, default: bool) -> bool:
    """
    Read an environment variable as boolean.
    Accepts: true/false, yes/no, 1/0 (case-insensitive).

    Args:
        key     : Environment variable name
        default : Default boolean value

    Returns:
        Boolean value
    """
    value = os.getenv(key, "").strip().lower()
    if not value:
        return default
    if value in ("true", "yes", "1", "on"):
        return True
    if value in ("false", "no", "0", "off"):
        return False
    log.warning(
        f"Invalid boolean value for '{key}': '{value}'. "
        f"Using default: {default}"
    )
    return default


def _get_list(key: str, default: list, sep: str = ",") -> list:
    """
    Read an environment variable as a comma-separated list.
    Strips whitespace from each item.

    Args:
        key     : Environment variable name
        default : Default list value
        sep     : Separator character (default comma)

    Returns:
        List of stripped strings
    """
    value = os.getenv(key, "").strip()
    if not value:
        return default
    return [item.strip() for item in value.split(sep) if item.strip()]


# ================================================================
# COMPANY SETTINGS
# ================================================================

COMPANY_NAME   = _get_env("COMPANY_NAME",   "ICICI Bank",     required=True)
SUPPORT_NAME   = _get_env("SUPPORT_NAME",   "IT Support Team")
COMPANY_DOMAIN = _get_env("COMPANY_DOMAIN", "icici.com")
SUPPORT_EMAIL  = _get_env("SUPPORT_EMAIL",  "itsupport@icici.com")
SUPPORT_PHONE  = _get_env("SUPPORT_PHONE",  "1800-XXX-XXXX")
TIMEZONE       = _get_env("TIMEZONE",       "Asia/Kolkata")

BUSINESS_HOURS_START = _get_int("BUSINESS_HOURS_START", 9)
BUSINESS_HOURS_END   = _get_int("BUSINESS_HOURS_END",   18)
BUSINESS_DAYS        = _get_list(
    "BUSINESS_DAYS",
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
)


# ================================================================
# FRESHDESK SETTINGS
# ================================================================

FRESHDESK_DOMAIN  = _get_env(
    "FRESHDESK_DOMAIN",
    required=True,
    default=""
)
FRESHDESK_API_KEY = _get_env(
    "FRESHDESK_API_KEY",
    required=True,
    default=""
)
FRESHDESK_BASE_URL = (
    f"https://{FRESHDESK_DOMAIN}/api/v2"
    if FRESHDESK_DOMAIN
    else ""
)

FRESHDESK_TICKET_STATUS = {
    "open"     : 2,
    "pending"  : 3,
    "resolved" : 4,
    "closed"   : 5,
}

FRESHDESK_TICKET_PRIORITY = {
    "low"    : 1,
    "medium" : 2,
    "high"   : 3,
    "urgent" : 4,
}

FRESHDESK_SOURCE = {
    "email"           : 1,
    "portal"          : 2,
    "phone"           : 3,
    "chat"            : 7,
    "feedback_widget" : 9,
    "outbound_email"  : 10,
}

FRESHDESK_POLL_INTERVAL_MINUTES = _get_int(
    "POLL_INTERVAL_MINUTES", 5
)
FRESHDESK_TICKETS_PER_PAGE      = _get_int(
    "FRESHDESK_TICKETS_PER_PAGE", 30
)
FRESHDESK_MAX_PAGES             = _get_int(
    "FRESHDESK_MAX_PAGES", 10
)
FRESHDESK_REQUEST_TIMEOUT       = _get_int(
    "FRESHDESK_REQUEST_TIMEOUT", 15
)

ESCALATION_AGENT_ID = _get_int("ESCALATION_AGENT_ID", 0)
ESCALATION_GROUP_ID = _get_int("ESCALATION_GROUP_ID", 0)
ENGINEER_EMAIL      = _get_env("ENGINEER_EMAIL", "")


# ================================================================
# AI / CLAUDE API SETTINGS
# ================================================================

ANTHROPIC_API_KEY  = _get_env(
    "ANTHROPIC_API_KEY",
    required=True,
    default=""
)
CLAUDE_MODEL       = _get_env(
    "CLAUDE_MODEL",
    "claude-sonnet-4-20250514"
)
CLAUDE_MAX_TOKENS  = _get_int("CLAUDE_MAX_TOKENS",  500)
CLAUDE_TEMPERATURE = _get_float("CLAUDE_TEMPERATURE", 0.0)
CLAUDE_TIMEOUT     = _get_int("CLAUDE_TIMEOUT",     30)

AI_CLASSIFIER_ENABLED  = _get_bool("AI_CLASSIFIER_ENABLED",  True)
FALLBACK_TO_RULES      = _get_bool("FALLBACK_TO_RULES",       True)
VALIDATE_WITH_RULES    = _get_bool("VALIDATE_WITH_RULES",     True)
SENTIMENT_ANALYSIS     = _get_bool("SENTIMENT_ANALYSIS",      False)
QUALITY_CHECK_ENABLED  = _get_bool("QUALITY_CHECK_ENABLED",   False)


# ================================================================
# TICKET CATEGORIES AND ROUTING
# ================================================================

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

AUTO_RESOLVABLE_CATEGORIES = [
    "app_install",
    "antivirus",
    "password_reset",
    "printer",
    "os_issue",
    "email_issue",
]

MANUAL_ONLY_CATEGORIES = [
    "hardware",
    "access_permission",
    "network",
    "other",
]

CATEGORY_DISPLAY_NAMES = {
    "app_install"       : "Software / App Installation",
    "antivirus"         : "Antivirus / Security",
    "password_reset"    : "Password Reset / Account Lockout",
    "network"           : "Network / VPN / Connectivity",
    "printer"           : "Printer / Printing Issue",
    "email_issue"       : "Email / Outlook Issue",
    "hardware"          : "Hardware / Physical Device",
    "os_issue"          : "Windows OS / System Issue",
    "access_permission" : "Access / Permission Issue",
    "other"             : "Other / Uncategorized",
}

CATEGORY_RESOLUTION_TIME_MINUTES = {
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

FORCE_ESCALATION_KEYWORDS = [
    "ransomware",
    "data breach",
    "security breach",
    "hacked",
    "all users affected",
    "production is down",
    "system is down",
    "server is down",
    "ceo",
    "managing director",
    "rbi audit",
    "regulatory",
    "compliance issue",
    "legal",
    "data loss",
]


# ================================================================
# AUTOMATION SETTINGS
# ================================================================

AUTOMATION_ENABLED = _get_bool("AUTOMATION_ENABLED", True)
POWERSHELL_PATH    = _get_env(
    "POWERSHELL_PATH",
    "powershell.exe"
)
SCRIPTS_DIR        = str(BASE_DIR / "automation" / "scripts")
SCRIPT_TIMEOUT_SEC = _get_int("SCRIPT_TIMEOUT_SEC", 120)
MAX_RETRY_ATTEMPTS = _get_int("MAX_RETRY_ATTEMPTS",  2)

AUTOMATION_SCRIPT_MAP = {
    "app_install"       : "install_app.ps1",
    "antivirus"         : "update_antivirus.ps1",
    "password_reset"    : "reset_password.ps1",
    "os_issue"          : "clear_disk_space.ps1",
    "printer"           : "restart_print_spooler.ps1",
    "email_issue"       : "repair_outlook.ps1",
    "network"           : "fix_network_adapter.ps1",
    "access_permission" : None,
    "hardware"          : None,
    "other"             : None,
}

DRY_RUN_MODE = _get_bool("DRY_RUN_MODE", False)


# ================================================================
# INTUNE / AZURE SETTINGS
# ================================================================

AZURE_TENANT_ID     = _get_env("AZURE_TENANT_ID",     "")
AZURE_CLIENT_ID     = _get_env("AZURE_CLIENT_ID",     "")
AZURE_CLIENT_SECRET = _get_env("AZURE_CLIENT_SECRET", "")

INTUNE_ENABLED        = _get_bool("INTUNE_ENABLED",        False)
INTUNE_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
INTUNE_TOKEN_URL      = (
    f"https://login.microsoftonline.com/"
    f"{AZURE_TENANT_ID}/oauth2/v2.0/token"
    if AZURE_TENANT_ID else ""
)
INTUNE_SCOPE          = "https://graph.microsoft.com/.default"
INTUNE_REQUEST_TIMEOUT = _get_int("INTUNE_REQUEST_TIMEOUT", 30)

AZURE_GRAPH_PERMISSIONS = [
    "DeviceManagementManagedDevices.Read.All",
    "DeviceManagementApps.ReadWrite.All",
    "DeviceManagementConfiguration.ReadWrite.All",
]


# ================================================================
# EMAIL / SMTP NOTIFICATION SETTINGS
# ================================================================

SMTP_HOST      = _get_env("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT      = _get_int("SMTP_PORT",     587)
SMTP_EMAIL     = _get_env("SMTP_EMAIL",    "")
SMTP_PASSWORD  = _get_env("SMTP_PASSWORD", "")
SMTP_USE_TLS   = _get_bool("SMTP_USE_TLS", True)
SMTP_TIMEOUT   = _get_int("SMTP_TIMEOUT",  15)

EMAIL_NOTIFICATIONS_ENABLED = _get_bool(
    "EMAIL_NOTIFICATIONS_ENABLED", True
)
NOTIFY_USER_ON_RESOLUTION   = _get_bool(
    "NOTIFY_USER_ON_RESOLUTION", True
)
NOTIFY_USER_ON_ESCALATION   = _get_bool(
    "NOTIFY_USER_ON_ESCALATION", True
)
NOTIFY_ENGINEER_ON_ESCALATION = _get_bool(
    "NOTIFY_ENGINEER_ON_ESCALATION", True
)
NOTIFY_ON_KB_GUIDE_SENT     = _get_bool(
    "NOTIFY_ON_KB_GUIDE_SENT", True
)

EMAIL_COLORS = {
    "resolved"      : "#1D9E75",
    "escalated"     : "#E8A838",
    "kb_guide_sent" : "#378ADD",
    "in_progress"   : "#534AB7",
    "password_reset": "#D85A30",
    "general"       : "#5F5E5A",
}


# ================================================================
# KNOWLEDGE BASE SETTINGS
# ================================================================

KB_DOCS_DIR        = _get_env(
    "KB_DOCS_DIR",
    str(BASE_DIR / "knowledge_base" / "docs")
)
KB_CHROMA_DIR      = _get_env(
    "KB_CHROMA_DIR",
    str(BASE_DIR / "knowledge_base" / "chroma_db")
)
KB_METADATA_FILE   = _get_env(
    "KB_METADATA",
    str(BASE_DIR / "knowledge_base" / "index_metadata.json")
)
KB_COLLECTION_NAME = _get_env(
    "KB_COLLECTION_NAME",
    "it_support_kb"
)
KB_EMBED_MODEL     = _get_env(
    "KB_EMBED_MODEL",
    "all-MiniLM-L6-v2"
)
KB_CHUNK_SIZE      = _get_int("KB_CHUNK_SIZE",    500)
KB_CHUNK_OVERLAP   = _get_int("KB_CHUNK_OVERLAP", 50)
KB_MAX_RESULTS     = _get_int("KB_MAX_RESULTS",   3)
KB_MIN_SCORE       = _get_float("KB_MIN_SCORE",   0.3)
KB_AUTO_REBUILD    = _get_bool("KB_AUTO_REBUILD", False)

KB_SUPPORTED_EXTENSIONS = [".txt", ".md", ".rst"]


# ================================================================
# DATABASE SETTINGS
# ================================================================

DB_PATH       = _get_env(
    "DB_PATH",
    str(BASE_DIR / "database" / "tickets.db")
)
DB_ECHO_SQL   = _get_bool("DB_ECHO_SQL",   False)
DB_POOL_SIZE  = _get_int("DB_POOL_SIZE",   5)

DB_TABLE_NAMES = {
    "tickets"        : "ticket_logs",
    "automation"     : "automation_logs",
    "classification" : "classification_logs",
    "notifications"  : "notification_logs",
    "daily_summary"  : "daily_summary",
}


# ================================================================
# LOGGING SETTINGS
# ================================================================

LOG_LEVEL       = _get_env("LOG_LEVEL",      "INFO")
LOG_FILE        = _get_env(
    "LOG_FILE",
    str(BASE_DIR / "ticket_resolver.log")
)
LOG_MAX_BYTES   = _get_int("LOG_MAX_BYTES",  5_000_000)
LOG_BACKUP_COUNT = _get_int("LOG_BACKUP_COUNT", 3)
LOG_FORMAT       = (
    "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
LOG_DATE_FORMAT  = "%Y-%m-%d %H:%M:%S"
LOG_TO_CONSOLE   = _get_bool("LOG_TO_CONSOLE", True)
LOG_TO_FILE      = _get_bool("LOG_TO_FILE",    True)


# ================================================================
# DASHBOARD SETTINGS
# ================================================================

DASHBOARD_TITLE        = _get_env(
    "DASHBOARD_TITLE",
    "AI Ticket Resolver — Dashboard"
)
DASHBOARD_ICON         = _get_env("DASHBOARD_ICON", "🎫")
DASHBOARD_REFRESH_SECS = _get_int("DASHBOARD_REFRESH_SECS", 60)
DASHBOARD_MAX_TICKETS  = _get_int("DASHBOARD_MAX_TICKETS",  100)
DASHBOARD_CHART_DAYS   = _get_int("DASHBOARD_CHART_DAYS",   7)
DASHBOARD_PORT         = _get_int("DASHBOARD_PORT",         8501)


# ================================================================
# FEATURE FLAGS
# ================================================================

FEATURE_AUTO_RESOLVE         = _get_bool(
    "FEATURE_AUTO_RESOLVE", True
)
FEATURE_KB_SEARCH            = _get_bool(
    "FEATURE_KB_SEARCH", True
)
FEATURE_SENTIMENT_ANALYSIS   = _get_bool(
    "FEATURE_SENTIMENT_ANALYSIS", False
)
FEATURE_TICKET_QUALITY_CHECK = _get_bool(
    "FEATURE_TICKET_QUALITY_CHECK", False
)
FEATURE_BATCH_PROCESSING     = _get_bool(
    "FEATURE_BATCH_PROCESSING", False
)
FEATURE_AFTER_HOURS_REPLY    = _get_bool(
    "FEATURE_AFTER_HOURS_REPLY", True
)
FEATURE_INTUNE_INTEGRATION   = _get_bool(
    "FEATURE_INTUNE_INTEGRATION", False
)
FEATURE_DASHBOARD            = _get_bool(
    "FEATURE_DASHBOARD", True
)


# ================================================================
# RATE LIMITING
# ================================================================

RATE_LIMIT_CLAUDE_RPM   = _get_int("RATE_LIMIT_CLAUDE_RPM",  50)
RATE_LIMIT_FRESHDESK_RPM = _get_int(
    "RATE_LIMIT_FRESHDESK_RPM", 100
)
RATE_LIMIT_SMTP_PER_HOUR = _get_int(
    "RATE_LIMIT_SMTP_PER_HOUR", 100
)
RATE_LIMIT_INTUNE_RPM    = _get_int(
    "RATE_LIMIT_INTUNE_RPM", 60
)


# ================================================================
# RETRY AND BACKOFF SETTINGS
# ================================================================

RETRY_MAX_ATTEMPTS   = _get_int("RETRY_MAX_ATTEMPTS",   3)
RETRY_BACKOFF_SEC    = _get_int("RETRY_BACKOFF_SEC",     5)
RETRY_MAX_BACKOFF    = _get_int("RETRY_MAX_BACKOFF",     60)


# ================================================================
# VALIDATION AND HEALTH CHECK
# ================================================================

def validate_settings() -> dict:
    """
    Validate that all required settings are configured.
    Called at startup from main.py to catch missing config
    before the system starts processing tickets.

    Returns:
        Dict with keys:
            valid   : True if all required settings are present
            errors  : List of missing/invalid setting descriptions
            warnings: List of optional settings that are not set
    """
    errors   = []
    warnings = []

    required_settings = [
        ("FRESHDESK_DOMAIN",  FRESHDESK_DOMAIN,  "Freshdesk domain"),
        ("FRESHDESK_API_KEY", FRESHDESK_API_KEY, "Freshdesk API key"),
        ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY, "Anthropic API key"),
    ]

    for env_key, value, description in required_settings:
        if not value or value.strip() == "":
            errors.append(
                f"Missing required setting: {env_key} ({description})"
            )

    if EMAIL_NOTIFICATIONS_ENABLED:
        if not SMTP_EMAIL:
            warnings.append(
                "SMTP_EMAIL not set — email notifications disabled."
            )
        if not SMTP_PASSWORD:
            warnings.append(
                "SMTP_PASSWORD not set — email notifications disabled."
            )

    if INTUNE_ENABLED:
        if not AZURE_TENANT_ID:
            errors.append(
                "AZURE_TENANT_ID required when INTUNE_ENABLED=true"
            )
        if not AZURE_CLIENT_ID:
            errors.append(
                "AZURE_CLIENT_ID required when INTUNE_ENABLED=true"
            )
        if not AZURE_CLIENT_SECRET:
            errors.append(
                "AZURE_CLIENT_SECRET required when INTUNE_ENABLED=true"
            )

    if not os.path.isdir(KB_DOCS_DIR):
        warnings.append(
            f"KB docs directory not found: {KB_DOCS_DIR}. "
            "Run kb_indexer.py to set up the knowledge base."
        )

    if FRESHDESK_POLL_INTERVAL_MINUTES < 1:
        errors.append(
            "POLL_INTERVAL_MINUTES must be at least 1."
        )

    if CLAUDE_MAX_TOKENS < 100:
        errors.append(
            "CLAUDE_MAX_TOKENS must be at least 100."
        )

    if not 0.0 <= KB_MIN_SCORE <= 1.0:
        errors.append(
            f"KB_MIN_SCORE must be between 0.0 and 1.0. "
            f"Got: {KB_MIN_SCORE}"
        )

    return {
        "valid"    : len(errors) == 0,
        "errors"   : errors,
        "warnings" : warnings,
    }


def get_all_settings() -> dict:
    """
    Return all current settings as a dict.
    Useful for logging the active config at startup
    and for the dashboard settings page.
    Masks sensitive values like API keys.

    Returns:
        Dict of setting name -> value
        with sensitive fields masked as '***'
    """
    sensitive_keys = {
        "FRESHDESK_API_KEY",
        "ANTHROPIC_API_KEY",
        "SMTP_PASSWORD",
        "AZURE_CLIENT_SECRET",
    }

    settings = {
        "COMPANY_NAME"                : COMPANY_NAME,
        "SUPPORT_NAME"                : SUPPORT_NAME,
        "COMPANY_DOMAIN"              : COMPANY_DOMAIN,
        "SUPPORT_EMAIL"               : SUPPORT_EMAIL,
        "TIMEZONE"                    : TIMEZONE,
        "BUSINESS_HOURS_START"        : BUSINESS_HOURS_START,
        "BUSINESS_HOURS_END"          : BUSINESS_HOURS_END,
        "FRESHDESK_DOMAIN"            : FRESHDESK_DOMAIN,
        "FRESHDESK_API_KEY"           : "***" if FRESHDESK_API_KEY else "",
        "FRESHDESK_POLL_INTERVAL_MINUTES": FRESHDESK_POLL_INTERVAL_MINUTES,
        "ESCALATION_AGENT_ID"         : ESCALATION_AGENT_ID,
        "ENGINEER_EMAIL"              : ENGINEER_EMAIL,
        "ANTHROPIC_API_KEY"           : "***" if ANTHROPIC_API_KEY else "",
        "CLAUDE_MODEL"                : CLAUDE_MODEL,
        "CLAUDE_MAX_TOKENS"           : CLAUDE_MAX_TOKENS,
        "AI_CLASSIFIER_ENABLED"       : AI_CLASSIFIER_ENABLED,
        "FALLBACK_TO_RULES"           : FALLBACK_TO_RULES,
        "AUTOMATION_ENABLED"          : AUTOMATION_ENABLED,
        "DRY_RUN_MODE"                : DRY_RUN_MODE,
        "SCRIPT_TIMEOUT_SEC"          : SCRIPT_TIMEOUT_SEC,
        "INTUNE_ENABLED"              : INTUNE_ENABLED,
        "SMTP_HOST"                   : SMTP_HOST,
        "SMTP_PORT"                   : SMTP_PORT,
        "SMTP_EMAIL"                  : SMTP_EMAIL,
        "SMTP_PASSWORD"               : "***" if SMTP_PASSWORD else "",
        "EMAIL_NOTIFICATIONS_ENABLED" : EMAIL_NOTIFICATIONS_ENABLED,
        "KB_DOCS_DIR"                 : KB_DOCS_DIR,
        "KB_CHROMA_DIR"               : KB_CHROMA_DIR,
        "KB_EMBED_MODEL"              : KB_EMBED_MODEL,
        "KB_CHUNK_SIZE"               : KB_CHUNK_SIZE,
        "KB_MIN_SCORE"                : KB_MIN_SCORE,
        "DB_PATH"                     : DB_PATH,
        "LOG_LEVEL"                   : LOG_LEVEL,
        "LOG_FILE"                    : LOG_FILE,
        "DASHBOARD_PORT"              : DASHBOARD_PORT,
        "FEATURE_AUTO_RESOLVE"        : FEATURE_AUTO_RESOLVE,
        "FEATURE_KB_SEARCH"           : FEATURE_KB_SEARCH,
        "FEATURE_INTUNE_INTEGRATION"  : FEATURE_INTUNE_INTEGRATION,
        "DRY_RUN_MODE"                : DRY_RUN_MODE,
    }

    return settings


def setup_logging() -> None:
    """
    Configure the Python logging system using settings
    defined above. Called once from main.py at startup.
    Creates rotating file handler and console handler.
    """
    from logging.handlers import RotatingFileHandler

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt     = LOG_FORMAT,
        datefmt = LOG_DATE_FORMAT,
    )

    if LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if LOG_TO_FILE:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        file_handler = RotatingFileHandler(
            filename    = LOG_FILE,
            maxBytes    = LOG_MAX_BYTES,
            backupCount = LOG_BACKUP_COUNT,
            encoding    = "utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)

    log.info(f"Logging configured — level: {LOG_LEVEL}, file: {LOG_FILE}")


if __name__ == "__main__":
    setup_logging()

    print("\n" + "=" * 65)
    print("SETTINGS MODULE — TEST RUN")
    print("=" * 65 + "\n")

    print("--- Validating settings ---")
    result = validate_settings()

    if result["valid"]:
        print("Validation: ALL REQUIRED SETTINGS PRESENT\n")
    else:
        print("Validation: MISSING REQUIRED SETTINGS\n")

    if result["errors"]:
        print("ERRORS (must fix before running):")
        for err in result["errors"]:
            print(f"  ERROR   : {err}")

    if result["warnings"]:
        print("\nWARNINGS (optional but recommended):")
        for warn in result["warnings"]:
            print(f"  WARNING : {warn}")

    print("\n--- Active settings ---")
    all_settings = get_all_settings()
    max_key_len  = max(len(k) for k in all_settings)
    for key, value in all_settings.items():
        print(f"  {key:<{max_key_len}} : {value}")

    print("\n--- Category info ---")
    print(f"Valid categories       : {len(VALID_CATEGORIES)}")
    print(f"Auto-resolvable        : {len(AUTO_RESOLVABLE_CATEGORIES)}")
    print(f"Manual-only            : {len(MANUAL_ONLY_CATEGORIES)}")
    print(f"Force escalation words : {len(FORCE_ESCALATION_KEYWORDS)}")

    print("\n--- Feature flags ---")
    features = {
        "Auto-resolve"        : FEATURE_AUTO_RESOLVE,
        "KB Search"           : FEATURE_KB_SEARCH,
        "Sentiment analysis"  : FEATURE_SENTIMENT_ANALYSIS,
        "Quality check"       : FEATURE_TICKET_QUALITY_CHECK,
        "Intune integration"  : FEATURE_INTUNE_INTEGRATION,
        "Batch processing"    : FEATURE_BATCH_PROCESSING,
        "After-hours reply"   : FEATURE_AFTER_HOURS_REPLY,
        "Dashboard"           : FEATURE_DASHBOARD,
    }
    for feature, enabled in features.items():
        status = "ON" if enabled else "off"
        print(f"  {feature:<22} : {status}")

    print("\n--- Resolution time estimates ---")
    for cat, minutes in CATEGORY_RESOLUTION_TIME_MINUTES.items():
        label = CATEGORY_DISPLAY_NAMES.get(cat, cat)
        print(f"  {label:<35} : {minutes} mins")

    print("\n--- Rate limits ---")
    print(f"  Claude API     : {RATE_LIMIT_CLAUDE_RPM} req/min")
    print(f"  Freshdesk API  : {RATE_LIMIT_FRESHDESK_RPM} req/min")
    print(f"  SMTP emails    : {RATE_LIMIT_SMTP_PER_HOUR} per hour")
    print(f"  Intune API     : {RATE_LIMIT_INTUNE_RPM} req/min")

    print("\nSettings module test complete.")