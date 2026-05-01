import os
import logging
import subprocess
import platform
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

POWERSHELL_PATH = os.getenv(
    "POWERSHELL_PATH",
    "powershell.exe" if platform.system() == "Windows" else "pwsh"
)

AUTOMATION_MAP = {
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


def run_automation(ticket: dict, classification: dict) -> bool:
    """
    Main entry point called by orchestrator.
    Reads the ticket and classification, picks the right
    automation script, and runs it.

    Args:
        ticket         : Parsed ticket dict from ticket_parser.py
        classification : Classification dict from ai_classifier.py

    Returns:
        True if automation ran successfully, False otherwise
    """
    category     = classification.get("category", "other")
    machine_name = ticket.get("machine_name", "UNKNOWN")
    apps         = ticket.get("mentioned_apps", [])
    requester    = ticket.get("requester_email", "")
    ticket_id    = ticket.get("id", 0)

    log.info(f"Running automation for ticket #{ticket_id}")
    log.info(f"  Category     : {category}")
    log.info(f"  Machine      : {machine_name}")
    log.info(f"  Apps found   : {apps}")
    log.info(f"  Requester    : {requester}")

    if machine_name == "UNKNOWN":
        log.warning(
            f"Ticket #{ticket_id}: Machine name not found. "
            "Cannot run remote automation without a target machine."
        )
        return False

    script_name = AUTOMATION_MAP.get(category)

    if script_name is None:
        log.warning(
            f"Ticket #{ticket_id}: Category '{category}' "
            "has no automation script. Needs manual handling."
        )
        return False

    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        log.error(
            f"Script not found: {script_path}. "
            "Please create this PowerShell script first."
        )
        return False

    params = _build_script_params(
        category=category,
        machine_name=machine_name,
        apps=apps,
        requester_email=requester,
        ticket_id=ticket_id,
    )

    log.info(f"Executing script: {script_name} with params: {params}")
    success = _execute_powershell(script_path, params)

    if success:
        log.info(
            f"Automation SUCCESS for ticket #{ticket_id} "
            f"— {script_name} ran on {machine_name}"
        )
    else:
        log.error(
            f"Automation FAILED for ticket #{ticket_id} "
            f"— {script_name} on {machine_name}"
        )

    return success


def _build_script_params(
    category       : str,
    machine_name   : str,
    apps           : list,
    requester_email: str,
    ticket_id      : int,
) -> dict:
    """
    Build the parameters dictionary to pass to the PowerShell script.
    Each script receives different parameters depending on category.

    Args:
        category        : Ticket category from classifier
        machine_name    : Target machine hostname
        apps            : List of app names mentioned in ticket
        requester_email : Email of user who raised the ticket
        ticket_id       : Freshdesk ticket ID

    Returns:
        Dict of parameter name → value pairs for the PS script
    """
    base_params = {
        "MachineName"   : machine_name,
        "TicketId"      : str(ticket_id),
        "RequesterEmail": requester_email,
    }

    if category == "app_install":
        app_name = _pick_app_name(apps)
        base_params["AppName"] = app_name
        log.info(f"App to install: {app_name}")

    elif category == "antivirus":
        base_params["ScanType"] = "full"

    elif category == "password_reset":
        username = _extract_username_from_email(requester_email)
        base_params["Username"] = username
        log.info(f"AD username for reset: {username}")

    elif category == "os_issue":
        base_params["Action"] = "repair"

    elif category == "printer":
        base_params["Action"] = "restart_spooler"

    elif category == "email_issue":
        username = _extract_username_from_email(requester_email)
        base_params["Username"] = username
        base_params["Action"]   = "rebuild_profile"

    elif category == "network":
        base_params["Action"] = "reset_adapter"

    return base_params


def _execute_powershell(script_path: str, params: dict) -> bool:
    """
    Execute a PowerShell script with the given parameters.
    Works on both Windows (powershell.exe) and Linux/Mac (pwsh).

    Args:
        script_path : Full absolute path to the .ps1 script file
        params      : Dict of parameter name → value pairs

    Returns:
        True if script exited with code 0, False otherwise
    """
    param_args = []
    for key, value in params.items():
        param_args.extend([f"-{key}", str(value)])

    command = [
        POWERSHELL_PATH,
        "-ExecutionPolicy", "Bypass",
        "-NonInteractive",
        "-NoProfile",
        "-File", script_path,
    ] + param_args

    log.info(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.stdout:
            log.info(f"Script stdout:\n{result.stdout.strip()}")

        if result.stderr:
            log.warning(f"Script stderr:\n{result.stderr.strip()}")

        if result.returncode == 0:
            log.info(f"Script exited successfully (return code 0).")
            return True
        else:
            log.error(
                f"Script exited with error code {result.returncode}."
            )
            return False

    except subprocess.TimeoutExpired:
        log.error(
            f"Script timed out after 120 seconds: {script_path}"
        )
        return False

    except FileNotFoundError:
        log.error(
            f"PowerShell not found at '{POWERSHELL_PATH}'. "
            "Install PowerShell or set POWERSHELL_PATH in .env"
        )
        return False

    except PermissionError:
        log.error(
            f"Permission denied running script: {script_path}. "
            "Check file permissions."
        )
        return False

    except Exception as e:
        log.error(f"Unexpected error running PowerShell script: {e}")
        return False


def _pick_app_name(apps: list) -> str:
    """
    Pick the most relevant app name from the list of apps
    detected in the ticket text.

    Args:
        apps : List of detected app name strings

    Returns:
        Single app name string to install
    """
    priority_apps = [
        "zoom", "microsoft teams", "ms teams", "teams",
        "chrome", "google chrome",
        "ms office", "microsoft office", "office",
        "outlook",
        "adobe acrobat", "acrobat",
        "vpn", "cisco vpn", "anyconnect",
    ]

    for app in priority_apps:
        if app in apps:
            return app

    if apps:
        return apps[0]

    return "unknown_app"


def _extract_username_from_email(email: str) -> str:
    """
    Extract the Active Directory username from an email address.
    Example: rahul.sharma@icici.com → rahul.sharma

    Args:
        email : User's email address

    Returns:
        Username string (part before the @ symbol)
    """
    if not email or "@" not in email:
        return "unknown_user"

    username = email.split("@")[0].strip().lower()
    return username


def run_manual_test(
    category    : str,
    machine_name: str,
    app_name    : str = "",
    email       : str = "test.user@icici.com",
) -> bool:
    """
    Test a specific automation script manually without needing
    a real Freshdesk ticket. Useful during development.

    Args:
        category     : Ticket category to test
        machine_name : Target machine name
        app_name     : App name (only needed for app_install)
        email        : Requester email (used for password reset)

    Returns:
        True if automation ran successfully, False otherwise
    """
    log.info(f"Manual test run — category: {category}, machine: {machine_name}")

    fake_ticket = {
        "id"             : 9999,
        "machine_name"   : machine_name,
        "mentioned_apps" : [app_name] if app_name else [],
        "requester_email": email,
    }

    fake_classification = {
        "category"        : category,
        "priority"        : "medium",
        "can_auto_resolve": True,
        "suggested_action": f"Test run for {category}",
    }

    return run_automation(fake_ticket, fake_classification)


def get_supported_categories() -> list:
    """
    Return list of all categories that have automation scripts.

    Returns:
        List of category name strings
    """
    return [
        cat for cat, script in AUTOMATION_MAP.items()
        if script is not None
    ]


def get_unsupported_categories() -> list:
    """
    Return list of categories that require manual handling.

    Returns:
        List of category name strings
    """
    return [
        cat for cat, script in AUTOMATION_MAP.items()
        if script is None
    ]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("AUTOMATION RUNNER INFO")
    print("=" * 60 + "\n")

    print("Categories with automation scripts:")
    for cat in get_supported_categories():
        script = AUTOMATION_MAP[cat]
        script_path = os.path.join(SCRIPTS_DIR, script)
        exists = os.path.exists(script_path)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {cat:<20} → {script:<35} [{status}]")

    print("\nCategories requiring manual handling:")
    for cat in get_unsupported_categories():
        print(f"  {cat}")

    print("\n" + "=" * 60)
    print("SAMPLE TEST RUN (dry run — no real machine needed)")
    print("=" * 60 + "\n")

    test_cases = [
        {
            "ticket": {
                "id"             : 1001,
                "subject"        : "Install Zoom on my laptop",
                "machine_name"   : "PC-ICICI-0042",
                "mentioned_apps" : ["zoom"],
                "requester_email": "rahul.sharma@icici.com",
            },
            "classification": {
                "category"        : "app_install",
                "priority"        : "high",
                "can_auto_resolve": True,
                "suggested_action": "Push Zoom installation via SCCM",
            }
        },
        {
            "ticket": {
                "id"             : 1002,
                "subject"        : "Antivirus not updating",
                "machine_name"   : "LAPTOP-ICICI-115",
                "mentioned_apps" : ["symantec"],
                "requester_email": "priya.mehta@icici.com",
            },
            "classification": {
                "category"        : "antivirus",
                "priority"        : "medium",
                "can_auto_resolve": True,
                "suggested_action": "Trigger remote AV update and scan",
            }
        },
        {
            "ticket": {
                "id"             : 1003,
                "subject"        : "Forgot my password",
                "machine_name"   : "UNKNOWN",
                "mentioned_apps" : [],
                "requester_email": "amit.patel@icici.com",
            },
            "classification": {
                "category"        : "password_reset",
                "priority"        : "high",
                "can_auto_resolve": True,
                "suggested_action": "Reset AD password and notify user",
            }
        },
    ]

    for tc in test_cases:
        ticket = tc["ticket"]
        classification = tc["classification"]
        print(f"Testing ticket #{ticket['id']}: {ticket['subject']}")
        print(f"  Machine  : {ticket['machine_name']}")
        print(f"  Category : {classification['category']}")
        result = run_automation(ticket, classification)
        print(f"  Result   : {'SUCCESS' if result else 'FAILED/SKIPPED'}")
        print("-" * 50)
        