# import os
# import logging
# import requests
# from requests.auth import HTTPBasicAuth
# from dotenv import load_dotenv

# load_dotenv()

# log = logging.getLogger(__name__)

# FRESHDESK_DOMAIN  = os.getenv("FRESHDESK_DOMAIN")
# FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")
# BASE_URL          = f"https://{FRESHDESK_DOMAIN}/api/v2"

# AUTH = HTTPBasicAuth(FRESHDESK_API_KEY, "X")

# HEADERS = {
#     "Content-Type": "application/json"
# }

# TICKET_STATUS = {
#     "open"     : 2,
#     "pending"  : 3,
#     "resolved" : 4,
#     "closed"   : 5,
# }

# TICKET_PRIORITY = {
#     "low"    : 1,
#     "medium" : 2,
#     "high"   : 3,
#     "urgent" : 4,
# }


# def _make_request(method: str, endpoint: str, payload: dict = None) -> dict | list | None:
#     """
#     Central HTTP request handler for all Freshdesk API calls.
#     Handles errors, retries, and logging in one place.

#     Args:
#         method   : HTTP method — 'GET', 'POST', 'PUT'
#         endpoint : API endpoint path e.g. '/tickets'
#         payload  : Optional JSON body for POST/PUT requests

#     Returns:
#         Parsed JSON response or None on failure
#     """
#     url = f"{BASE_URL}{endpoint}"

#     try:
#         if method == "GET":
#             response = requests.get(url, auth=AUTH, headers=HEADERS, timeout=15)
#         elif method == "POST":
#             response = requests.post(url, auth=AUTH, headers=HEADERS, json=payload, timeout=15)
#         elif method == "PUT":
#             response = requests.put(url, auth=AUTH, headers=HEADERS, json=payload, timeout=15)
#         else:
#             log.error(f"Unsupported HTTP method: {method}")
#             return None

#         if response.status_code == 429:
#             log.warning("Freshdesk rate limit hit. Wait 60 seconds before retrying.")
#             return None

#         if response.status_code == 401:
#             log.error("Freshdesk authentication failed. Check your API key in .env")
#             return None

#         if response.status_code == 404:
#             log.error(f"Freshdesk resource not found: {url}")
#             return None

#         response.raise_for_status()

#         if response.content:
#             return response.json()
#         return {}

#     except requests.exceptions.ConnectionError:
#         log.error(f"Cannot connect to Freshdesk. Check your FRESHDESK_DOMAIN in .env")
#         return None
#     except requests.exceptions.Timeout:
#         log.error(f"Freshdesk API request timed out: {url}")
#         return None
#     except requests.exceptions.HTTPError as e:
#         log.error(f"Freshdesk HTTP error: {e} — URL: {url}")
#         return None
#     except Exception as e:
#         log.error(f"Unexpected error calling Freshdesk API: {e}")
#         return None


# def fetch_new_tickets(page: int = 1, per_page: int = 30) -> list:
#     """
#     Fetch all open tickets from Freshdesk that have not been processed yet.

#     Args:
#         page     : Page number for pagination (default 1)
#         per_page : Number of tickets per page (max 100)

#     Returns:
#         List of raw ticket dicts from Freshdesk API
#     """
#     log.info(f"Fetching open tickets from Freshdesk (page {page})...")

#     endpoint = f"/tickets?status=2&page={page}&per_page={per_page}&order_by=created_at&order_type=asc"
#     response = _make_request("GET", endpoint)

#     if response is None:
#         log.error("Failed to fetch tickets from Freshdesk.")
#         return []

#     if not isinstance(response, list):
#         log.error(f"Unexpected response format from Freshdesk: {type(response)}")
#         return []

#     log.info(f"Fetched {len(response)} open ticket(s).")
#     return response


# def fetch_ticket_by_id(ticket_id: int) -> dict | None:
#     """
#     Fetch a single ticket by its ID including all details.

#     Args:
#         ticket_id : Freshdesk ticket ID

#     Returns:
#         Ticket dict or None if not found
#     """
#     log.info(f"Fetching ticket #{ticket_id}...")
#     endpoint = f"/tickets/{ticket_id}"
#     response = _make_request("GET", endpoint)

#     if response is None:
#         log.error(f"Could not fetch ticket #{ticket_id}")
#         return None

#     return response


# def fetch_all_open_tickets() -> list:
#     """
#     Fetch ALL open tickets across multiple pages automatically.
#     Freshdesk limits 100 tickets per page — this handles pagination.

#     Returns:
#         Complete list of all open tickets
#     """
#     all_tickets = []
#     page = 1

#     while True:
#         log.info(f"Fetching page {page} of open tickets...")
#         endpoint  = f"/tickets?status=2&page={page}&per_page=100&order_by=created_at&order_type=asc"
#         response  = _make_request("GET", endpoint)

#         if not response:
#             break

#         all_tickets.extend(response)

#         if len(response) < 100:
#             break

#         page += 1

#     log.info(f"Total open tickets fetched: {len(all_tickets)}")
#     return all_tickets


# def update_ticket_status(ticket_id: int, status: str, note: str = None) -> bool:
#     """
#     Update the status of a ticket in Freshdesk.

#     Args:
#         ticket_id : Freshdesk ticket ID
#         status    : New status — 'open', 'pending', 'resolved', 'closed'
#         note      : Optional internal note to add explaining the status change

#     Returns:
#         True if successful, False otherwise
#     """
#     status_code = TICKET_STATUS.get(status)

#     if status_code is None:
#         log.error(f"Invalid status '{status}'. Use: open, pending, resolved, closed.")
#         return False

#     payload = {"status": status_code}

#     log.info(f"Updating ticket #{ticket_id} status to '{status}'...")
#     response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

#     if response is None:
#         log.error(f"Failed to update ticket #{ticket_id} status.")
#         return False

#     if note:
#         add_internal_note(ticket_id, note)

#     log.info(f"Ticket #{ticket_id} status updated to '{status}'.")
#     return True


# def close_ticket(ticket_id: int, resolution_note: str) -> bool:
#     """
#     Close a ticket and add a resolution note explaining how it was resolved.

#     Args:
#         ticket_id       : Freshdesk ticket ID
#         resolution_note : Text explaining how the ticket was resolved

#     Returns:
#         True if successful, False otherwise
#     """
#     log.info(f"Closing ticket #{ticket_id}...")

#     payload = {"status": TICKET_STATUS["closed"]}
#     response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

#     if response is None:
#         log.error(f"Failed to close ticket #{ticket_id}.")
#         return False

#     full_note = f"[AI Auto-Resolved]\n\n{resolution_note}\n\nThis ticket was automatically resolved by the AI Ticket Resolver system."
#     add_internal_note(ticket_id, full_note)

#     log.info(f"Ticket #{ticket_id} closed successfully.")
#     return True


# def add_internal_note(ticket_id: int, note_body: str) -> bool:
#     """
#     Add a private internal note to a ticket (not visible to end user).
#     Used by engineers and the AI system to log actions taken.

#     Args:
#         ticket_id : Freshdesk ticket ID
#         note_body : Text content of the note

#     Returns:
#         True if successful, False otherwise
#     """
#     payload = {
#         "body"   : note_body,
#         "private": True
#     }

#     log.info(f"Adding internal note to ticket #{ticket_id}...")
#     response = _make_request("POST", f"/tickets/{ticket_id}/notes", payload)

#     if response is None:
#         log.error(f"Failed to add note to ticket #{ticket_id}.")
#         return False

#     log.info(f"Internal note added to ticket #{ticket_id}.")
#     return True


# def add_public_reply(ticket_id: int, reply_body: str) -> bool:
#     """
#     Send a public reply to the ticket — the user will receive this by email.

#     Args:
#         ticket_id  : Freshdesk ticket ID
#         reply_body : Message text sent to the user

#     Returns:
#         True if successful, False otherwise
#     """
#     payload = {"body": reply_body}

#     log.info(f"Sending public reply to ticket #{ticket_id}...")
#     response = _make_request("POST", f"/tickets/{ticket_id}/reply", payload)

#     if response is None:
#         log.error(f"Failed to send reply on ticket #{ticket_id}.")
#         return False

#     log.info(f"Public reply sent on ticket #{ticket_id}.")
#     return True


# def assign_ticket_to_agent(ticket_id: int, agent_id: int) -> bool:
#     """
#     Assign a ticket to a specific engineer/agent in Freshdesk.

#     Args:
#         ticket_id : Freshdesk ticket ID
#         agent_id  : Freshdesk agent ID of the engineer to assign to

#     Returns:
#         True if successful, False otherwise
#     """
#     payload = {"responder_id": agent_id}

#     log.info(f"Assigning ticket #{ticket_id} to agent #{agent_id}...")
#     response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

#     if response is None:
#         log.error(f"Failed to assign ticket #{ticket_id}.")
#         return False

#     log.info(f"Ticket #{ticket_id} assigned to agent #{agent_id}.")
#     return True


# def set_ticket_priority(ticket_id: int, priority: str) -> bool:
#     """
#     Update the priority level of a ticket.

#     Args:
#         ticket_id : Freshdesk ticket ID
#         priority  : Priority level — 'low', 'medium', 'high', 'urgent'

#     Returns:
#         True if successful, False otherwise
#     """
#     priority_code = TICKET_PRIORITY.get(priority)

#     if priority_code is None:
#         log.error(f"Invalid priority '{priority}'. Use: low, medium, high, urgent.")
#         return False

#     payload = {"priority": priority_code}

#     log.info(f"Setting ticket #{ticket_id} priority to '{priority}'...")
#     response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

#     if response is None:
#         log.error(f"Failed to set priority on ticket #{ticket_id}.")
#         return False

#     log.info(f"Ticket #{ticket_id} priority set to '{priority}'.")
#     return True


# def add_tag_to_ticket(ticket_id: int, tags: list) -> bool:
#     """
#     Add tags to a ticket for filtering and reporting in Freshdesk.

#     Args:
#         ticket_id : Freshdesk ticket ID
#         tags      : List of tag strings e.g. ["ai-resolved", "app_install"]

#     Returns:
#         True if successful, False otherwise
#     """
#     ticket = fetch_ticket_by_id(ticket_id)
#     if not ticket:
#         return False

#     existing_tags = ticket.get("tags", [])
#     merged_tags   = list(set(existing_tags + tags))
#     payload       = {"tags": merged_tags}

#     log.info(f"Adding tags {tags} to ticket #{ticket_id}...")
#     response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

#     if response is None:
#         log.error(f"Failed to add tags to ticket #{ticket_id}.")
#         return False

#     log.info(f"Tags added to ticket #{ticket_id}: {merged_tags}")
#     return True


# def fetch_agent_list() -> list:
#     """
#     Fetch all agents/engineers in your Freshdesk account.
#     Useful to get agent IDs for ticket assignment.

#     Returns:
#         List of agent dicts with id, name, email
#     """
#     log.info("Fetching agent list from Freshdesk...")
#     response = _make_request("GET", "/agents")

#     if response is None:
#         log.error("Failed to fetch agent list.")
#         return []

#     agents = [
#         {
#             "id"   : a.get("id"),
#             "name" : a.get("contact", {}).get("name"),
#             "email": a.get("contact", {}).get("email"),
#         }
#         for a in response
#     ]

#     log.info(f"Fetched {len(agents)} agent(s).")
#     return agents


# def test_connection() -> bool:
#     """
#     Test if Freshdesk API credentials are working correctly.
#     Run this first when setting up the project.

#     Returns:
#         True if connected, False if credentials are wrong
#     """
#     log.info("Testing Freshdesk API connection...")
#     response = _make_request("GET", "/tickets?per_page=1")

#     if response is None:
#         log.error("Freshdesk connection test FAILED. Check FRESHDESK_DOMAIN and FRESHDESK_API_KEY in .env")
#         return False

#     log.info("Freshdesk connection test PASSED.")
#     return True


# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(message)s"
#     )

#     print("\n" + "="*60)
#     print("FRESHDESK CLIENT TEST RUN")
#     print("="*60 + "\n")

#     if not FRESHDESK_DOMAIN or not FRESHDESK_API_KEY:
#         print("ERROR: FRESHDESK_DOMAIN or FRESHDESK_API_KEY missing in .env file")
#         print("Add these to your config/.env file and try again.")
#         exit(1)

#     connected = test_connection()
#     if not connected:
#         exit(1)

#     print("\n--- Fetching open tickets ---")
#     tickets = fetch_new_tickets()
#     print(f"Total open tickets: {len(tickets)}")

#     if tickets:
#         first = tickets[0]
#         print(f"\nFirst ticket details:")
#         print(f"  ID       : {first.get('id')}")
#         print(f"  Subject  : {first.get('subject')}")
#         print(f"  Status   : {first.get('status')}")
#         print(f"  Priority : {first.get('priority')}")
#         print(f"  Email    : {first.get('requester_id')}")

#     print("\n--- Fetching agents ---")
#     agents = fetch_agent_list()
#     for agent in agents:
#         print(f"  Agent: {agent['name']} ({agent['email']}) — ID: {agent['id']}")

#     print("\nAll tests complete.")


import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from dotenv        import load_dotenv

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE         = os.getenv("DEMO_MODE",         "false").strip().lower() == "true"
DRY_RUN_MODE      = os.getenv("DRY_RUN_MODE",      "false").strip().lower() == "true"
FRESHDESK_DOMAIN  = os.getenv("FRESHDESK_DOMAIN",  "")
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY", "")
BASE_URL          = f"https://{FRESHDESK_DOMAIN}/api/v2" if FRESHDESK_DOMAIN else ""

AUTH = HTTPBasicAuth(FRESHDESK_API_KEY, "X")

HEADERS = {
    "Content-Type": "application/json"
}

TICKET_STATUS = {
    "open"     : 2,
    "pending"  : 3,
    "resolved" : 4,
    "closed"   : 5,
}

TICKET_PRIORITY = {
    "low"    : 1,
    "medium" : 2,
    "high"   : 3,
    "urgent" : 4,
}

DEMO_TICKETS_STORE: list = []
DEMO_TICKET_NOTES : dict = {}
DEMO_TICKET_TAGS  : dict = {}


def _is_demo_key() -> bool:
    """
    Check if the API key is a demo placeholder value.
    Returns True if running in demo mode or with a fake key.
    """
    return (
        DEMO_MODE
        or not FRESHDESK_API_KEY
        or FRESHDESK_API_KEY in (
            "DEMO_KEY_NOT_REAL",
            "your_freshdesk_api_key_here",
            "your_freshdesk_api_key",
            "",
        )
        or not FRESHDESK_DOMAIN
        or FRESHDESK_DOMAIN in (
            "demo.freshdesk.com",
            "yourcompany.freshdesk.com",
            "",
        )
    )


def _make_request(
    method  : str,
    endpoint: str,
    payload : dict = None,
) -> dict | list | None:
    """
    Central HTTP request handler for all Freshdesk API calls.
    In demo mode returns simulated responses without making
    any real HTTP requests.

    Args:
        method   : HTTP method — 'GET', 'POST', 'PUT'
        endpoint : API endpoint path e.g. '/tickets'
        payload  : Optional JSON body for POST/PUT requests

    Returns:
        Parsed JSON response or None on failure
    """
    if _is_demo_key():
        return _demo_response(method, endpoint, payload)

    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(
                url, auth=AUTH,
                headers=HEADERS, timeout=15
            )
        elif method == "POST":
            response = requests.post(
                url, auth=AUTH,
                headers=HEADERS, json=payload, timeout=15
            )
        elif method == "PUT":
            response = requests.put(
                url, auth=AUTH,
                headers=HEADERS, json=payload, timeout=15
            )
        else:
            log.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code == 429:
            log.warning(
                "Freshdesk rate limit hit. "
                "Wait 60 seconds before retrying."
            )
            return None

        if response.status_code == 401:
            log.error(
                "Freshdesk authentication failed. "
                "Check your API key in config/.env"
            )
            return None

        if response.status_code == 404:
            log.error(
                f"Freshdesk resource not found: {url}"
            )
            return None

        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    except requests.exceptions.ConnectionError:
        log.error(
            "Cannot connect to Freshdesk. "
            "Check FRESHDESK_DOMAIN in config/.env"
        )
        return None

    except requests.exceptions.Timeout:
        log.error(
            f"Freshdesk API request timed out: {url}"
        )
        return None

    except requests.exceptions.HTTPError as e:
        log.error(f"Freshdesk HTTP error: {e} — URL: {url}")
        return None

    except Exception as e:
        log.error(
            f"Unexpected error calling Freshdesk API: {e}"
        )
        return None


def _demo_response(
    method  : str,
    endpoint: str,
    payload : dict = None,
) -> dict | list | None:
    """
    Return simulated Freshdesk API responses for demo mode.
    Called by _make_request() when DEMO_MODE=true or when
    placeholder credentials are detected.
    No real HTTP requests are made.

    Args:
        method   : HTTP method
        endpoint : Freshdesk API endpoint path
        payload  : Optional request payload

    Returns:
        Simulated response matching real Freshdesk API format
    """
    import time as _time
    import random as _random
    _time.sleep(_random.uniform(0.05, 0.15))

    if "/tickets" in endpoint and method == "GET":

        if "/tickets?" in endpoint and "per_page=1" in endpoint:
            log.debug("[DEMO] Connection test — returning 1 ticket.")
            return [_make_demo_ticket(9000)]

        if "/notes" not in endpoint and "/reply" not in endpoint:
            parts = endpoint.split("/tickets/")
            if len(parts) > 1:
                ticket_id_str = parts[1].split("?")[0].split("/")[0]
                if ticket_id_str.isdigit():
                    ticket_id = int(ticket_id_str)
                    for t in DEMO_TICKETS_STORE:
                        if t.get("id") == ticket_id:
                            log.debug(
                                f"[DEMO] Fetched ticket #{ticket_id}"
                            )
                            return t
                    return None

            log.debug("[DEMO] Returning empty open tickets list.")
            return []

    if "/tickets" in endpoint and method == "PUT":
        parts = endpoint.split("/tickets/")
        if len(parts) > 1:
            ticket_id_str = parts[1].split("?")[0].split("/")[0]
            if ticket_id_str.isdigit():
                ticket_id = int(ticket_id_str)
                log.debug(
                    f"[DEMO] Updated ticket #{ticket_id} "
                    f"with payload: {payload}"
                )
                return {"id": ticket_id, **(payload or {})}
        return {}

    if "/notes" in endpoint and method == "POST":
        parts = endpoint.split("/tickets/")
        if len(parts) > 1:
            ticket_id_str = parts[1].split("/")[0]
            if ticket_id_str.isdigit():
                ticket_id = int(ticket_id_str)
                if ticket_id not in DEMO_TICKET_NOTES:
                    DEMO_TICKET_NOTES[ticket_id] = []
                note_text = (payload or {}).get("body", "")
                DEMO_TICKET_NOTES[ticket_id].append(note_text)
                log.debug(
                    f"[DEMO] Note added to ticket #{ticket_id}"
                )
                return {"id": ticket_id, "body": note_text}
        return {}

    if "/reply" in endpoint and method == "POST":
        parts = endpoint.split("/tickets/")
        if len(parts) > 1:
            ticket_id_str = parts[1].split("/")[0]
            if ticket_id_str.isdigit():
                ticket_id = int(ticket_id_str)
                log.debug(
                    f"[DEMO] Public reply sent to ticket #{ticket_id}"
                )
                return {"id": ticket_id}
        return {}

    if "/agents" in endpoint and method == "GET":
        log.debug("[DEMO] Returning demo agent list.")
        return [
            {
                "id"      : 1001,
                "contact" : {
                    "name"  : "Demo Engineer",
                    "email" : "engineer@icici.com",
                },
            },
            {
                "id"      : 1002,
                "contact" : {
                    "name"  : "IT Support Lead",
                    "email" : "it.lead@icici.com",
                },
            },
        ]

    log.debug(
        f"[DEMO] Unhandled endpoint "
        f"{method} {endpoint} — returning empty dict."
    )
    return {}


def _make_demo_ticket(ticket_id: int) -> dict:
    """
    Build a realistic demo ticket dict matching
    the real Freshdesk API ticket format.

    Args:
        ticket_id : Ticket ID number

    Returns:
        Demo ticket dict
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return {
        "id"             : ticket_id,
        "subject"        : f"Demo ticket #{ticket_id}",
        "description"    : "This is a demo ticket.",
        "description_text": "This is a demo ticket.",
        "status"         : 2,
        "priority"       : 2,
        "requester_id"   : 5001,
        "requester"      : {
            "name" : "Demo User",
            "email": "demo.user@icici.com",
        },
        "responder_id"   : None,
        "group_id"       : None,
        "tags"           : [],
        "custom_fields"  : {},
        "attachments"    : [],
        "created_at"     : now,
        "updated_at"     : now,
        "due_by"         : now,
        "source"         : 2,
        "nr_of_activities": 0,
    }


def fetch_new_tickets(
    page    : int = 1,
    per_page: int = 30,
) -> list:
    """
    Fetch all open tickets from Freshdesk.
    In demo mode returns empty list — demo tickets come
    directly from DEMO_TICKETS in demo_runner.py.

    Args:
        page     : Page number for pagination
        per_page : Number of tickets per page (max 100)

    Returns:
        List of raw ticket dicts from Freshdesk API
    """
    if _is_demo_key():
        log.info(
            "[DEMO] fetch_new_tickets — "
            "returning empty list. "
            "Demo tickets come from demo_runner.py."
        )
        return []

    log.info(
        f"Fetching open tickets from Freshdesk "
        f"(page {page})..."
    )

    endpoint = (
        f"/tickets?status=2&page={page}"
        f"&per_page={per_page}"
        f"&order_by=created_at&order_type=asc"
    )
    response = _make_request("GET", endpoint)

    if response is None:
        log.error("Failed to fetch tickets from Freshdesk.")
        return []

    if not isinstance(response, list):
        log.error(
            f"Unexpected response from Freshdesk: "
            f"{type(response)}"
        )
        return []

    log.info(f"Fetched {len(response)} open ticket(s).")
    return response


def fetch_ticket_by_id(ticket_id: int) -> dict | None:
    """
    Fetch a single ticket by its Freshdesk ID.
    In demo mode returns None (tickets not stored in demo).

    Args:
        ticket_id : Freshdesk ticket ID

    Returns:
        Ticket dict or None if not found
    """
    if _is_demo_key():
        log.debug(
            f"[DEMO] fetch_ticket_by_id #{ticket_id} "
            "— returning None."
        )
        return None

    log.info(f"Fetching ticket #{ticket_id}...")
    endpoint = f"/tickets/{ticket_id}"
    response = _make_request("GET", endpoint)

    if response is None:
        log.error(f"Could not fetch ticket #{ticket_id}")
        return None

    return response


def fetch_all_open_tickets() -> list:
    """
    Fetch ALL open tickets across multiple pages automatically.
    Freshdesk limits 100 per page — this handles pagination.
    In demo mode returns empty list.

    Returns:
        Complete list of all open tickets
    """
    if _is_demo_key():
        log.info("[DEMO] fetch_all_open_tickets — returning [].")
        return []

    all_tickets = []
    page        = 1

    while True:
        log.info(f"Fetching page {page} of open tickets...")
        endpoint = (
            f"/tickets?status=2&page={page}"
            f"&per_page=100"
            f"&order_by=created_at&order_type=asc"
        )
        response = _make_request("GET", endpoint)

        if not response:
            break

        all_tickets.extend(response)

        if len(response) < 100:
            break

        page += 1

    log.info(
        f"Total open tickets fetched: {len(all_tickets)}"
    )
    return all_tickets


def update_ticket_status(
    ticket_id: int,
    status   : str,
    note     : str = None,
) -> bool:
    """
    Update the status of a ticket in Freshdesk.
    In demo mode logs the action without making real API calls.

    Args:
        ticket_id : Freshdesk ticket ID
        status    : New status — open | pending | resolved | closed
        note      : Optional internal note to add

    Returns:
        True if successful, False otherwise
    """
    status_code = TICKET_STATUS.get(status)

    if status_code is None:
        log.error(
            f"Invalid status '{status}'. "
            "Use: open, pending, resolved, closed."
        )
        return False

    if DRY_RUN_MODE and not DEMO_MODE:
        log.warning(
            f"[DRY RUN] Would update ticket #{ticket_id} "
            f"to status '{status}'. Skipping."
        )
        return True

    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(
        f"{mode}Updating ticket #{ticket_id} "
        f"status to '{status}'..."
    )

    payload  = {"status": status_code}
    response = _make_request(
        "PUT", f"/tickets/{ticket_id}", payload
    )

    if response is None:
        log.error(
            f"Failed to update ticket #{ticket_id} status."
        )
        return False

    if note:
        add_internal_note(ticket_id, note)

    log.info(
        f"{mode}Ticket #{ticket_id} "
        f"status updated to '{status}'."
    )
    return True


def close_ticket(ticket_id: int, resolution_note: str) -> bool:
    """
    Close a ticket and add a resolution note.
    In demo mode logs the closure without real API calls.

    Args:
        ticket_id       : Freshdesk ticket ID
        resolution_note : Text explaining how ticket was resolved

    Returns:
        True if successful, False otherwise
    """
    if DRY_RUN_MODE and not DEMO_MODE:
        log.warning(
            f"[DRY RUN] Would close ticket #{ticket_id}. "
            "Skipping."
        )
        return True

    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(f"{mode}Closing ticket #{ticket_id}...")

    payload  = {"status": TICKET_STATUS["closed"]}
    response = _make_request(
        "PUT", f"/tickets/{ticket_id}", payload
    )

    if response is None:
        log.error(f"Failed to close ticket #{ticket_id}.")
        return False

    full_note = (
        f"[AI Auto-Resolved]\n\n"
        f"{resolution_note}\n\n"
        f"This ticket was automatically resolved "
        f"by the AI Ticket Resolver system."
    )
    add_internal_note(ticket_id, full_note)

    log.info(
        f"{mode}Ticket #{ticket_id} closed successfully."
    )
    return True


def add_internal_note(
    ticket_id: int,
    note_body: str,
) -> bool:
    """
    Add a private internal note to a ticket.
    In demo mode stores notes in DEMO_TICKET_NOTES dict.

    Args:
        ticket_id : Freshdesk ticket ID
        note_body : Text content of the note

    Returns:
        True if successful, False otherwise
    """
    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(
        f"{mode}Adding note to ticket #{ticket_id}..."
    )

    payload  = {"body": note_body, "private": True}
    response = _make_request(
        "POST",
        f"/tickets/{ticket_id}/notes",
        payload,
    )

    if response is None:
        log.error(
            f"Failed to add note to ticket #{ticket_id}."
        )
        return False

    log.debug(
        f"{mode}Note added to ticket #{ticket_id}."
    )
    return True


def add_public_reply(
    ticket_id : int,
    reply_body: str,
) -> bool:
    """
    Send a public reply to the ticket user via email.
    In demo mode logs the reply without sending real email.

    Args:
        ticket_id  : Freshdesk ticket ID
        reply_body : Message text sent to the user

    Returns:
        True if successful, False otherwise
    """
    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(
        f"{mode}Sending public reply to "
        f"ticket #{ticket_id}..."
    )

    payload  = {"body": reply_body}
    response = _make_request(
        "POST",
        f"/tickets/{ticket_id}/reply",
        payload,
    )

    if response is None:
        log.error(
            f"Failed to send reply on ticket #{ticket_id}."
        )
        return False

    log.debug(
        f"{mode}Public reply sent on ticket #{ticket_id}."
    )
    return True


def assign_ticket_to_agent(
    ticket_id: int,
    agent_id : int,
) -> bool:
    """
    Assign a ticket to a specific engineer in Freshdesk.
    In demo mode logs assignment without real API call.

    Args:
        ticket_id : Freshdesk ticket ID
        agent_id  : Freshdesk agent ID

    Returns:
        True if successful, False otherwise
    """
    if not agent_id or agent_id == 0:
        log.debug(
            f"No agent ID set — skipping ticket assignment."
        )
        return True

    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(
        f"{mode}Assigning ticket #{ticket_id} "
        f"to agent #{agent_id}..."
    )

    payload  = {"responder_id": agent_id}
    response = _make_request(
        "PUT", f"/tickets/{ticket_id}", payload
    )

    if response is None:
        log.error(
            f"Failed to assign ticket #{ticket_id}."
        )
        return False

    log.info(
        f"{mode}Ticket #{ticket_id} "
        f"assigned to agent #{agent_id}."
    )
    return True


def set_ticket_priority(
    ticket_id: int,
    priority : str,
) -> bool:
    """
    Update the priority level of a ticket in Freshdesk.
    In demo mode logs without real API call.

    Args:
        ticket_id : Freshdesk ticket ID
        priority  : low | medium | high | urgent

    Returns:
        True if successful, False otherwise
    """
    priority_code = TICKET_PRIORITY.get(priority)

    if priority_code is None:
        log.error(
            f"Invalid priority '{priority}'. "
            "Use: low, medium, high, urgent."
        )
        return False

    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(
        f"{mode}Setting ticket #{ticket_id} "
        f"priority to '{priority}'..."
    )

    payload  = {"priority": priority_code}
    response = _make_request(
        "PUT", f"/tickets/{ticket_id}", payload
    )

    if response is None:
        log.error(
            f"Failed to set priority on ticket #{ticket_id}."
        )
        return False

    log.info(
        f"{mode}Ticket #{ticket_id} "
        f"priority set to '{priority}'."
    )
    return True


def add_tag_to_ticket(
    ticket_id: int,
    tags     : list,
) -> bool:
    """
    Add tags to a ticket for filtering and reporting.
    In demo mode stores tags in DEMO_TICKET_TAGS dict.

    Args:
        ticket_id : Freshdesk ticket ID
        tags      : List of tag strings

    Returns:
        True if successful, False otherwise
    """
    if not tags:
        return True

    mode = "[DEMO] " if _is_demo_key() else ""

    if _is_demo_key():
        existing = DEMO_TICKET_TAGS.get(ticket_id, [])
        merged   = list(set(existing + tags))
        DEMO_TICKET_TAGS[ticket_id] = merged
        log.debug(
            f"[DEMO] Tags stored for ticket "
            f"#{ticket_id}: {merged}"
        )
        return True

    ticket = fetch_ticket_by_id(ticket_id)
    if not ticket:
        return False

    existing_tags = ticket.get("tags", [])
    merged_tags   = list(set(existing_tags + tags))
    payload       = {"tags": merged_tags}

    log.info(
        f"{mode}Adding tags {tags} to ticket #{ticket_id}..."
    )
    response = _make_request(
        "PUT", f"/tickets/{ticket_id}", payload
    )

    if response is None:
        log.error(
            f"Failed to add tags to ticket #{ticket_id}."
        )
        return False

    log.info(
        f"{mode}Tags added to ticket "
        f"#{ticket_id}: {merged_tags}"
    )
    return True


def fetch_agent_list() -> list:
    """
    Fetch all agents/engineers in your Freshdesk account.
    In demo mode returns a hardcoded demo agent list.

    Returns:
        List of agent dicts with id, name, email
    """
    mode = "[DEMO] " if _is_demo_key() else ""
    log.info(f"{mode}Fetching agent list...")

    response = _make_request("GET", "/agents")

    if response is None:
        log.error("Failed to fetch agent list.")
        return []

    agents = [
        {
            "id"   : a.get("id"),
            "name" : a.get("contact", {}).get("name"),
            "email": a.get("contact", {}).get("email"),
        }
        for a in response
    ]

    log.info(f"Fetched {len(agents)} agent(s).")
    return agents


def test_connection() -> bool:
    """
    Test if Freshdesk API credentials are working correctly.
    In demo mode always returns True immediately.

    Returns:
        True if connected, False if credentials are wrong
    """
    if _is_demo_key():
        log.info(
            "[DEMO] Freshdesk connection test — "
            "PASSED (demo mode, no real connection)."
        )
        return True

    log.info("Testing Freshdesk API connection...")
    response = _make_request("GET", "/tickets?per_page=1")

    if response is None:
        log.error(
            "Freshdesk connection test FAILED. "
            "Check FRESHDESK_DOMAIN and "
            "FRESHDESK_API_KEY in config/.env"
        )
        return False

    log.info("Freshdesk connection test PASSED.")
    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
    )

    print("\n" + "=" * 60)
    print("FRESHDESK CLIENT TEST RUN")
    print("=" * 60)
    print(
        f"  Mode    : "
        f"{'DEMO' if _is_demo_key() else 'LIVE'}"
    )
    print(f"  Domain  : {FRESHDESK_DOMAIN or 'not set'}")
    print(
        f"  API Key : "
        f"{'set ✓' if FRESHDESK_API_KEY and FRESHDESK_API_KEY not in ('DEMO_KEY_NOT_REAL', '') else 'not set / demo'}"
    )
    print()

    print("--- Test 1: Connection ---")
    connected = test_connection()
    print(
        f"  Result: "
        f"{'PASSED ✓' if connected else 'FAILED ✗'}\n"
    )

    if not connected:
        print(
            "Fix credentials in config/.env and try again.\n"
            "Or set DEMO_MODE=true to run without real keys."
        )
        exit(1)

    print("--- Test 2: Fetch open tickets ---")
    tickets = fetch_new_tickets()
    print(f"  Open tickets: {len(tickets)}")

    if tickets:
        first = tickets[0]
        print(f"\n  First ticket:")
        print(f"    ID       : {first.get('id')}")
        print(f"    Subject  : {first.get('subject')}")
        print(f"    Status   : {first.get('status')}")
        print(f"    Priority : {first.get('priority')}")

    print("\n--- Test 3: Fetch agent list ---")
    agents = fetch_agent_list()
    print(f"  Agents found: {len(agents)}")
    for agent in agents:
        print(
            f"  {agent.get('name', 'N/A'):<25} "
            f"({agent.get('email', 'N/A')}) "
            f"— ID: {agent.get('id')}"
        )

    if _is_demo_key():
        print("\n--- Test 4: Demo write operations ---")

        print(f"  update_ticket_status(9001, 'pending')...")
        ok = update_ticket_status(9001, "pending")
        print(f"  Result: {'OK ✓' if ok else 'FAILED ✗'}")

        print(f"  add_internal_note(9001, 'Test note')...")
        ok = add_internal_note(9001, "Test internal note.")
        print(f"  Result: {'OK ✓' if ok else 'FAILED ✗'}")

        print(f"  add_public_reply(9001, 'Test reply')...")
        ok = add_public_reply(9001, "Test public reply.")
        print(f"  Result: {'OK ✓' if ok else 'FAILED ✗'}")

        print(f"  add_tag_to_ticket(9001, ['demo', 'test'])...")
        ok = add_tag_to_ticket(9001, ["demo", "test"])
        print(
            f"  Result: {'OK ✓' if ok else 'FAILED ✗'}  "
            f"Tags stored: {DEMO_TICKET_TAGS.get(9001, [])}"
        )

        print(f"  close_ticket(9001, 'Test resolved.')...")
        ok = close_ticket(9001, "Test resolved.")
        print(f"  Result: {'OK ✓' if ok else 'FAILED ✗'}")

        print(
            f"\n  Notes stored for ticket #9001: "
            f"{len(DEMO_TICKET_NOTES.get(9001, []))} note(s)"
        )

    print("\n" + "=" * 60)
    print("All Freshdesk client tests complete.")
    print("=" * 60 + "\n")