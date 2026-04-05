import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

FRESHDESK_DOMAIN  = os.getenv("FRESHDESK_DOMAIN")
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")
BASE_URL          = f"https://{FRESHDESK_DOMAIN}/api/v2"

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


def _make_request(method: str, endpoint: str, payload: dict = None) -> dict | list | None:
    """
    Central HTTP request handler for all Freshdesk API calls.
    Handles errors, retries, and logging in one place.

    Args:
        method   : HTTP method — 'GET', 'POST', 'PUT'
        endpoint : API endpoint path e.g. '/tickets'
        payload  : Optional JSON body for POST/PUT requests

    Returns:
        Parsed JSON response or None on failure
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, auth=AUTH, headers=HEADERS, timeout=15)
        elif method == "POST":
            response = requests.post(url, auth=AUTH, headers=HEADERS, json=payload, timeout=15)
        elif method == "PUT":
            response = requests.put(url, auth=AUTH, headers=HEADERS, json=payload, timeout=15)
        else:
            log.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code == 429:
            log.warning("Freshdesk rate limit hit. Wait 60 seconds before retrying.")
            return None

        if response.status_code == 401:
            log.error("Freshdesk authentication failed. Check your API key in .env")
            return None

        if response.status_code == 404:
            log.error(f"Freshdesk resource not found: {url}")
            return None

        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    except requests.exceptions.ConnectionError:
        log.error(f"Cannot connect to Freshdesk. Check your FRESHDESK_DOMAIN in .env")
        return None
    except requests.exceptions.Timeout:
        log.error(f"Freshdesk API request timed out: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        log.error(f"Freshdesk HTTP error: {e} — URL: {url}")
        return None
    except Exception as e:
        log.error(f"Unexpected error calling Freshdesk API: {e}")
        return None


def fetch_new_tickets(page: int = 1, per_page: int = 30) -> list:
    """
    Fetch all open tickets from Freshdesk that have not been processed yet.

    Args:
        page     : Page number for pagination (default 1)
        per_page : Number of tickets per page (max 100)

    Returns:
        List of raw ticket dicts from Freshdesk API
    """
    log.info(f"Fetching open tickets from Freshdesk (page {page})...")

    endpoint = f"/tickets?status=2&page={page}&per_page={per_page}&order_by=created_at&order_type=asc"
    response = _make_request("GET", endpoint)

    if response is None:
        log.error("Failed to fetch tickets from Freshdesk.")
        return []

    if not isinstance(response, list):
        log.error(f"Unexpected response format from Freshdesk: {type(response)}")
        return []

    log.info(f"Fetched {len(response)} open ticket(s).")
    return response


def fetch_ticket_by_id(ticket_id: int) -> dict | None:
    """
    Fetch a single ticket by its ID including all details.

    Args:
        ticket_id : Freshdesk ticket ID

    Returns:
        Ticket dict or None if not found
    """
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
    Freshdesk limits 100 tickets per page — this handles pagination.

    Returns:
        Complete list of all open tickets
    """
    all_tickets = []
    page = 1

    while True:
        log.info(f"Fetching page {page} of open tickets...")
        endpoint  = f"/tickets?status=2&page={page}&per_page=100&order_by=created_at&order_type=asc"
        response  = _make_request("GET", endpoint)

        if not response:
            break

        all_tickets.extend(response)

        if len(response) < 100:
            break

        page += 1

    log.info(f"Total open tickets fetched: {len(all_tickets)}")
    return all_tickets


def update_ticket_status(ticket_id: int, status: str, note: str = None) -> bool:
    """
    Update the status of a ticket in Freshdesk.

    Args:
        ticket_id : Freshdesk ticket ID
        status    : New status — 'open', 'pending', 'resolved', 'closed'
        note      : Optional internal note to add explaining the status change

    Returns:
        True if successful, False otherwise
    """
    status_code = TICKET_STATUS.get(status)

    if status_code is None:
        log.error(f"Invalid status '{status}'. Use: open, pending, resolved, closed.")
        return False

    payload = {"status": status_code}

    log.info(f"Updating ticket #{ticket_id} status to '{status}'...")
    response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

    if response is None:
        log.error(f"Failed to update ticket #{ticket_id} status.")
        return False

    if note:
        add_internal_note(ticket_id, note)

    log.info(f"Ticket #{ticket_id} status updated to '{status}'.")
    return True


def close_ticket(ticket_id: int, resolution_note: str) -> bool:
    """
    Close a ticket and add a resolution note explaining how it was resolved.

    Args:
        ticket_id       : Freshdesk ticket ID
        resolution_note : Text explaining how the ticket was resolved

    Returns:
        True if successful, False otherwise
    """
    log.info(f"Closing ticket #{ticket_id}...")

    payload = {"status": TICKET_STATUS["closed"]}
    response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

    if response is None:
        log.error(f"Failed to close ticket #{ticket_id}.")
        return False

    full_note = f"[AI Auto-Resolved]\n\n{resolution_note}\n\nThis ticket was automatically resolved by the AI Ticket Resolver system."
    add_internal_note(ticket_id, full_note)

    log.info(f"Ticket #{ticket_id} closed successfully.")
    return True


def add_internal_note(ticket_id: int, note_body: str) -> bool:
    """
    Add a private internal note to a ticket (not visible to end user).
    Used by engineers and the AI system to log actions taken.

    Args:
        ticket_id : Freshdesk ticket ID
        note_body : Text content of the note

    Returns:
        True if successful, False otherwise
    """
    payload = {
        "body"   : note_body,
        "private": True
    }

    log.info(f"Adding internal note to ticket #{ticket_id}...")
    response = _make_request("POST", f"/tickets/{ticket_id}/notes", payload)

    if response is None:
        log.error(f"Failed to add note to ticket #{ticket_id}.")
        return False

    log.info(f"Internal note added to ticket #{ticket_id}.")
    return True


def add_public_reply(ticket_id: int, reply_body: str) -> bool:
    """
    Send a public reply to the ticket — the user will receive this by email.

    Args:
        ticket_id  : Freshdesk ticket ID
        reply_body : Message text sent to the user

    Returns:
        True if successful, False otherwise
    """
    payload = {"body": reply_body}

    log.info(f"Sending public reply to ticket #{ticket_id}...")
    response = _make_request("POST", f"/tickets/{ticket_id}/reply", payload)

    if response is None:
        log.error(f"Failed to send reply on ticket #{ticket_id}.")
        return False

    log.info(f"Public reply sent on ticket #{ticket_id}.")
    return True


def assign_ticket_to_agent(ticket_id: int, agent_id: int) -> bool:
    """
    Assign a ticket to a specific engineer/agent in Freshdesk.

    Args:
        ticket_id : Freshdesk ticket ID
        agent_id  : Freshdesk agent ID of the engineer to assign to

    Returns:
        True if successful, False otherwise
    """
    payload = {"responder_id": agent_id}

    log.info(f"Assigning ticket #{ticket_id} to agent #{agent_id}...")
    response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

    if response is None:
        log.error(f"Failed to assign ticket #{ticket_id}.")
        return False

    log.info(f"Ticket #{ticket_id} assigned to agent #{agent_id}.")
    return True


def set_ticket_priority(ticket_id: int, priority: str) -> bool:
    """
    Update the priority level of a ticket.

    Args:
        ticket_id : Freshdesk ticket ID
        priority  : Priority level — 'low', 'medium', 'high', 'urgent'

    Returns:
        True if successful, False otherwise
    """
    priority_code = TICKET_PRIORITY.get(priority)

    if priority_code is None:
        log.error(f"Invalid priority '{priority}'. Use: low, medium, high, urgent.")
        return False

    payload = {"priority": priority_code}

    log.info(f"Setting ticket #{ticket_id} priority to '{priority}'...")
    response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

    if response is None:
        log.error(f"Failed to set priority on ticket #{ticket_id}.")
        return False

    log.info(f"Ticket #{ticket_id} priority set to '{priority}'.")
    return True


def add_tag_to_ticket(ticket_id: int, tags: list) -> bool:
    """
    Add tags to a ticket for filtering and reporting in Freshdesk.

    Args:
        ticket_id : Freshdesk ticket ID
        tags      : List of tag strings e.g. ["ai-resolved", "app_install"]

    Returns:
        True if successful, False otherwise
    """
    ticket = fetch_ticket_by_id(ticket_id)
    if not ticket:
        return False

    existing_tags = ticket.get("tags", [])
    merged_tags   = list(set(existing_tags + tags))
    payload       = {"tags": merged_tags}

    log.info(f"Adding tags {tags} to ticket #{ticket_id}...")
    response = _make_request("PUT", f"/tickets/{ticket_id}", payload)

    if response is None:
        log.error(f"Failed to add tags to ticket #{ticket_id}.")
        return False

    log.info(f"Tags added to ticket #{ticket_id}: {merged_tags}")
    return True


def fetch_agent_list() -> list:
    """
    Fetch all agents/engineers in your Freshdesk account.
    Useful to get agent IDs for ticket assignment.

    Returns:
        List of agent dicts with id, name, email
    """
    log.info("Fetching agent list from Freshdesk...")
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
    Run this first when setting up the project.

    Returns:
        True if connected, False if credentials are wrong
    """
    log.info("Testing Freshdesk API connection...")
    response = _make_request("GET", "/tickets?per_page=1")

    if response is None:
        log.error("Freshdesk connection test FAILED. Check FRESHDESK_DOMAIN and FRESHDESK_API_KEY in .env")
        return False

    log.info("Freshdesk connection test PASSED.")
    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "="*60)
    print("FRESHDESK CLIENT TEST RUN")
    print("="*60 + "\n")

    if not FRESHDESK_DOMAIN or not FRESHDESK_API_KEY:
        print("ERROR: FRESHDESK_DOMAIN or FRESHDESK_API_KEY missing in .env file")
        print("Add these to your config/.env file and try again.")
        exit(1)

    connected = test_connection()
    if not connected:
        exit(1)

    print("\n--- Fetching open tickets ---")
    tickets = fetch_new_tickets()
    print(f"Total open tickets: {len(tickets)}")

    if tickets:
        first = tickets[0]
        print(f"\nFirst ticket details:")
        print(f"  ID       : {first.get('id')}")
        print(f"  Subject  : {first.get('subject')}")
        print(f"  Status   : {first.get('status')}")
        print(f"  Priority : {first.get('priority')}")
        print(f"  Email    : {first.get('requester_id')}")

    print("\n--- Fetching agents ---")
    agents = fetch_agent_list()
    for agent in agents:
        print(f"  Agent: {agent['name']} ({agent['email']}) — ID: {agent['id']}")

    print("\nAll tests complete.")