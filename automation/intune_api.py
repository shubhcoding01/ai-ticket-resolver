import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TENANT_ID     = os.getenv("AZURE_TENANT_ID",     "")
CLIENT_ID     = os.getenv("AZURE_CLIENT_ID",     "")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")

GRAPH_BASE_URL  = "https://graph.microsoft.com/v1.0"
TOKEN_URL       = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
GRAPH_SCOPE     = "https://graph.microsoft.com/.default"

_token_cache = {
    "access_token" : None,
    "expires_at"   : 0,
}


def _get_access_token() -> str | None:
    """
    Get a valid Microsoft Graph API access token.
    Uses cached token if still valid, fetches a new one if expired.
    Token is cached in memory for the duration of the script run.

    Returns:
        Access token string or None if authentication fails
    """
    now = time.time()

    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        log.debug("Using cached access token.")
        return _token_cache["access_token"]

    log.info("Fetching new Microsoft Graph API access token...")

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        log.error(
            "Azure credentials missing in .env — "
            "AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET required."
        )
        return None

    payload = {
        "grant_type"    : "client_credentials",
        "client_id"     : CLIENT_ID,
        "client_secret" : CLIENT_SECRET,
        "scope"         : GRAPH_SCOPE,
    }

    try:
        response = requests.post(TOKEN_URL, data=payload, timeout=15)
        response.raise_for_status()
        token_data = response.json()

        _token_cache["access_token"] = token_data["access_token"]
        _token_cache["expires_at"]   = now + token_data.get("expires_in", 3600)

        log.info("Access token fetched successfully.")
        return _token_cache["access_token"]

    except requests.exceptions.HTTPError as e:
        log.error(f"Token fetch failed — HTTP error: {e}")
        log.error(f"Response: {response.text}")
        return None

    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to Microsoft login endpoint. Check internet/VPN.")
        return None

    except Exception as e:
        log.error(f"Unexpected error fetching token: {e}")
        return None


def _graph_request(
    method  : str,
    endpoint: str,
    payload : dict = None,
    params  : dict = None,
) -> dict | list | None:
    """
    Central Microsoft Graph API request handler.
    Handles auth token injection, error handling,
    rate limiting, and response parsing.

    Args:
        method   : HTTP method — GET, POST, PUT, PATCH, DELETE
        endpoint : Graph API endpoint path e.g. /deviceManagement/managedDevices
        payload  : Optional JSON body for POST/PUT/PATCH
        params   : Optional URL query parameters

    Returns:
        Parsed JSON response dict/list or None on failure
    """
    token = _get_access_token()
    if not token:
        log.error("Cannot make Graph API request — no valid token.")
        return None

    url     = f"{GRAPH_BASE_URL}{endpoint}"
    headers = {
        "Authorization" : f"Bearer {token}",
        "Content-Type"  : "application/json",
        "Accept"        : "application/json",
    }

    try:
        if method == "GET":
            response = requests.get(
                url, headers=headers, params=params, timeout=30
            )
        elif method == "POST":
            response = requests.post(
                url, headers=headers, json=payload, timeout=30
            )
        elif method == "PUT":
            response = requests.put(
                url, headers=headers, json=payload, timeout=30
            )
        elif method == "PATCH":
            response = requests.patch(
                url, headers=headers, json=payload, timeout=30
            )
        elif method == "DELETE":
            response = requests.delete(
                url, headers=headers, timeout=30
            )
        else:
            log.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code == 401:
            log.warning("Token expired mid-session. Clearing cache and retrying...")
            _token_cache["access_token"] = None
            _token_cache["expires_at"]   = 0
            return _graph_request(method, endpoint, payload, params)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 30))
            log.warning(
                f"Graph API rate limited. "
                f"Waiting {retry_after}s before retry..."
            )
            time.sleep(retry_after)
            return _graph_request(method, endpoint, payload, params)

        if response.status_code == 404:
            log.error(f"Graph API resource not found: {url}")
            return None

        if response.status_code == 403:
            log.error(
                f"Graph API permission denied: {url}\n"
                "Check Azure app has required API permissions."
            )
            return None

        if response.status_code in [200, 201, 204]:
            if response.content:
                return response.json()
            return {}

        response.raise_for_status()
        return {}

    except requests.exceptions.Timeout:
        log.error(f"Graph API request timed out: {url}")
        return None

    except requests.exceptions.ConnectionError:
        log.error(f"Cannot connect to Microsoft Graph API: {url}")
        return None

    except requests.exceptions.HTTPError as e:
        log.error(f"Graph API HTTP error: {e}")
        return None

    except Exception as e:
        log.error(f"Unexpected error calling Graph API: {e}")
        return None


def get_device_by_name(device_name: str) -> dict | None:
    """
    Look up a managed device in Intune by its hostname/computer name.

    Args:
        device_name : Computer name e.g. 'PC-ICICI-0042'

    Returns:
        Device dict with id, deviceName, userPrincipalName,
        operatingSystem etc. or None if not found
    """
    log.info(f"Looking up device in Intune: {device_name}")

    response = _graph_request(
        method   = "GET",
        endpoint = "/deviceManagement/managedDevices",
        params   = {
            "$filter" : f"deviceName eq '{device_name}'",
            "$select" : (
                "id,deviceName,userPrincipalName,operatingSystem,"
                "osVersion,complianceState,managementState,"
                "lastSyncDateTime,manufacturer,model"
            ),
        }
    )

    if response is None:
        log.error(f"Failed to query Intune for device: {device_name}")
        return None

    devices = response.get("value", [])

    if not devices:
        log.warning(f"No Intune device found with name: {device_name}")
        return None

    device = devices[0]
    log.info(
        f"Device found: {device.get('deviceName')} "
        f"(ID: {device.get('id')}) "
        f"OS: {device.get('operatingSystem')} {device.get('osVersion')}"
    )
    return device


def get_device_by_user_email(email: str) -> list:
    """
    Find all Intune managed devices belonging to a specific user.

    Args:
        email : User's email / UPN e.g. 'rahul.sharma@icici.com'

    Returns:
        List of device dicts belonging to that user
    """
    log.info(f"Looking up Intune devices for user: {email}")

    response = _graph_request(
        method   = "GET",
        endpoint = "/deviceManagement/managedDevices",
        params   = {
            "$filter" : f"userPrincipalName eq '{email}'",
            "$select" : (
                "id,deviceName,userPrincipalName,operatingSystem,"
                "osVersion,complianceState,lastSyncDateTime"
            ),
        }
    )

    if response is None:
        log.error(f"Failed to query Intune for user: {email}")
        return []

    devices = response.get("value", [])
    log.info(f"Found {len(devices)} device(s) for {email}")
    return devices


def sync_device(device_name: str) -> bool:
    """
    Force an immediate Intune sync on a managed device.
    This makes the device check in and pull latest policies
    and app assignments right away without waiting.

    Args:
        device_name : Computer name to sync

    Returns:
        True if sync triggered successfully, False otherwise
    """
    log.info(f"Triggering Intune sync for device: {device_name}")

    device = get_device_by_name(device_name)
    if not device:
        log.error(f"Cannot sync — device not found in Intune: {device_name}")
        return False

    device_id = device["id"]

    response = _graph_request(
        method   = "POST",
        endpoint = (
            f"/deviceManagement/managedDevices/{device_id}"
            f"/syncDevice"
        ),
    )

    if response is None:
        log.error(f"Sync failed for device: {device_name}")
        return False

    log.info(f"Sync triggered successfully for {device_name} (ID: {device_id})")
    return True


def install_app_via_intune(
    device_name : str,
    app_name    : str,
    ticket_id   : int = 0,
) -> bool:
    """
    Assign a managed app to a specific device via Intune.
    The app must already exist in your Intune app catalog.

    Flow:
        1. Find device ID from device name
        2. Find app ID from app name in Intune catalog
        3. Create device app assignment
        4. Force sync so device picks it up immediately

    Args:
        device_name : Target computer name e.g. 'PC-ICICI-0042'
        app_name    : App display name as it appears in Intune catalog
        ticket_id   : Freshdesk ticket ID for logging

    Returns:
        True if app assignment created and sync triggered
    """
    log.info(
        f"Installing '{app_name}' on '{device_name}' "
        f"via Intune (ticket #{ticket_id})..."
    )

    device = get_device_by_name(device_name)
    if not device:
        log.error(f"Device not found in Intune: {device_name}")
        return False

    device_id = device["id"]

    app = get_app_from_catalog(app_name)
    if not app:
        log.error(
            f"App '{app_name}' not found in Intune catalog. "
            "Please add it to Intune before assigning."
        )
        return False

    app_id   = app["id"]
    app_type = app.get("@odata.type", "")

    log.info(
        f"Assigning app '{app_name}' (ID: {app_id}) "
        f"to device '{device_name}' (ID: {device_id})..."
    )

    assignment_payload = {
        "mobileAppAssignments": [
            {
                "@odata.type" : "#microsoft.graph.mobileAppAssignment",
                "target"      : {
                    "@odata.type": "#microsoft.graph.deviceAndAppManagementAssignmentTarget",
                    "deviceId"   : device_id,
                },
                "intent"      : "required",
                "settings"    : {
                    "@odata.type"              : "#microsoft.graph.mobileAppAssignmentSettings",
                    "useDeviceContext"          : True,
                    "vpnConfigurationId"        : None,
                    "uninstallOnDeviceRemoval"  : False,
                    "isRemovable"               : True,
                },
            }
        ]
    }

    response = _graph_request(
        method   = "POST",
        endpoint = f"/deviceAppManagement/mobileApps/{app_id}/assign",
        payload  = assignment_payload,
    )

    if response is None:
        log.error(
            f"Failed to assign '{app_name}' to '{device_name}'. "
            "Check Intune app permissions."
        )
        return False

    log.info(f"App '{app_name}' assigned to '{device_name}' successfully.")

    time.sleep(2)
    synced = sync_device(device_name)

    if synced:
        log.info(
            f"Device synced. '{app_name}' will install "
            f"on '{device_name}' within 15 minutes."
        )
    else:
        log.warning(
            f"App assigned but sync failed. "
            f"'{app_name}' will install at next scheduled check-in."
        )

    return True


def get_app_from_catalog(app_name: str) -> dict | None:
    """
    Search the Intune app catalog for an app by display name.
    Searches all app types — Win32, MSI, store apps, web apps.

    Args:
        app_name : Display name to search for (case-insensitive partial match)

    Returns:
        App dict with id, displayName, odata.type or None if not found
    """
    log.info(f"Searching Intune app catalog for: {app_name}")

    response = _graph_request(
        method   = "GET",
        endpoint = "/deviceAppManagement/mobileApps",
        params   = {
            "$filter" : (
                f"contains(tolower(displayName), "
                f"'{app_name.lower()}')"
            ),
            "$select" : "id,displayName,@odata.type,publisher,version",
            "$top"    : 5,
        }
    )

    if response is None:
        log.error(f"Failed to search Intune app catalog for: {app_name}")
        return None

    apps = response.get("value", [])

    if not apps:
        log.warning(f"No app found in Intune catalog matching: {app_name}")
        return None

    app = apps[0]
    log.info(
        f"App found in catalog: '{app.get('displayName')}' "
        f"(ID: {app.get('id')})"
    )
    return app


def get_all_apps_in_catalog() -> list:
    """
    Fetch the complete list of apps in your Intune catalog.
    Useful for seeing what apps are available to assign.

    Returns:
        List of app dicts with id, displayName, type, publisher
    """
    log.info("Fetching all apps from Intune catalog...")

    response = _graph_request(
        method   = "GET",
        endpoint = "/deviceAppManagement/mobileApps",
        params   = {
            "$select" : "id,displayName,@odata.type,publisher,version",
            "$top"    : 100,
        }
    )

    if response is None:
        log.error("Failed to fetch Intune app catalog.")
        return []

    apps = response.get("value", [])
    log.info(f"Found {len(apps)} apps in Intune catalog.")
    return apps


def run_device_action(
    device_name : str,
    action      : str,
) -> bool:
    """
    Run a remote device action on an Intune managed device.

    Supported actions:
        reboot          — Restart the device remotely
        scan            — Trigger Windows Defender quick scan
        wipe            — Factory reset (USE WITH EXTREME CAUTION)
        retire          — Remove corporate data
        collect_logs    — Collect diagnostic logs from device

    Args:
        device_name : Target computer name
        action      : Action name string from supported list above

    Returns:
        True if action triggered successfully
    """
    action_endpoint_map = {
        "reboot"       : "rebootNow",
        "scan"         : "windowsDefenderScan",
        "wipe"         : "wipe",
        "retire"       : "retire",
        "collect_logs" : "createDeviceLogCollectionRequest",
    }

    if action not in action_endpoint_map:
        log.error(
            f"Unsupported device action: '{action}'. "
            f"Supported: {list(action_endpoint_map.keys())}"
        )
        return False

    if action in ["wipe", "retire"]:
        log.critical(
            f"DESTRUCTIVE ACTION '{action}' requested on {device_name}! "
            "This action is blocked in automated mode for safety. "
            "Run manually from Intune portal."
        )
        return False

    log.info(f"Running action '{action}' on device: {device_name}")

    device = get_device_by_name(device_name)
    if not device:
        log.error(f"Device not found: {device_name}")
        return False

    device_id    = device["id"]
    action_path  = action_endpoint_map[action]

    payload = {}
    if action == "scan":
        payload = {"quickScan": True}

    response = _graph_request(
        method   = "POST",
        endpoint = (
            f"/deviceManagement/managedDevices/{device_id}"
            f"/{action_path}"
        ),
        payload  = payload,
    )

    if response is None:
        log.error(f"Action '{action}' failed on {device_name}")
        return False

    log.info(f"Action '{action}' triggered on {device_name} successfully.")
    return True


def get_device_compliance_status(device_name: str) -> dict | None:
    """
    Check if a device is compliant with Intune policies.
    Non-compliant devices may be causing app install failures.

    Args:
        device_name : Computer name to check

    Returns:
        Dict with compliance status details or None if not found
    """
    log.info(f"Checking compliance status for: {device_name}")

    device = get_device_by_name(device_name)
    if not device:
        return None

    device_id = device["id"]

    response = _graph_request(
        method   = "GET",
        endpoint = (
            f"/deviceManagement/managedDevices/{device_id}"
            f"?$select=id,deviceName,complianceState,"
            f"complianceGracePeriodExpirationDateTime,"
            f"lastSyncDateTime,jailBroken,managementState"
        ),
    )

    if response is None:
        log.error(f"Failed to fetch compliance for {device_name}")
        return None

    compliance = {
        "device_name"     : response.get("deviceName"),
        "compliance_state": response.get("complianceState"),
        "management_state": response.get("managementState"),
        "last_sync"       : response.get("lastSyncDateTime"),
        "jailbroken"      : response.get("jailBroken"),
        "is_compliant"    : response.get("complianceState") == "compliant",
    }

    log.info(
        f"Device {device_name} compliance: "
        f"{compliance['compliance_state']}"
    )
    return compliance


def get_installed_apps_on_device(device_name: str) -> list:
    """
    Get the list of apps currently installed on a managed device.
    Useful to verify if an app install was successful.

    Args:
        device_name : Computer name to check

    Returns:
        List of installed app dicts with displayName, version, id
    """
    log.info(f"Fetching installed apps on device: {device_name}")

    device = get_device_by_name(device_name)
    if not device:
        return []

    device_id = device["id"]

    response = _graph_request(
        method   = "GET",
        endpoint = (
            f"/deviceManagement/managedDevices/{device_id}"
            f"/detectedApps"
        ),
        params   = {
            "$select" : "displayName,version,sizeInByte",
            "$top"    : 100,
        }
    )

    if response is None:
        log.error(f"Failed to fetch installed apps for {device_name}")
        return []

    apps = response.get("value", [])
    log.info(f"Found {len(apps)} installed apps on {device_name}")
    return apps


def verify_app_installed(device_name: str, app_name: str) -> bool:
    """
    Check if a specific app is currently installed on a device.
    Called after install_app_via_intune() to verify success.

    Args:
        device_name : Computer name to check
        app_name    : App display name to look for

    Returns:
        True if app is found installed, False otherwise
    """
    log.info(
        f"Verifying '{app_name}' is installed on '{device_name}'..."
    )

    installed_apps = get_installed_apps_on_device(device_name)

    if not installed_apps:
        log.warning(f"Could not retrieve installed apps for {device_name}")
        return False

    app_name_lower = app_name.lower()

    for app in installed_apps:
        if app_name_lower in app.get("displayName", "").lower():
            log.info(
                f"Verified: '{app.get('displayName')}' "
                f"v{app.get('version', 'unknown')} "
                f"is installed on {device_name}."
            )
            return True

    log.warning(
        f"'{app_name}' NOT found in installed apps on {device_name}. "
        "It may still be installing — check again in 15 minutes."
    )
    return False


def get_all_managed_devices(
    filter_str: str = None,
    limit      : int = 100,
) -> list:
    """
    Fetch all managed devices from Intune.
    Optionally filter by OS, compliance state, etc.

    Args:
        filter_str : Optional OData filter string
                     e.g. "operatingSystem eq 'Windows'"
        limit      : Maximum number of devices to return

    Returns:
        List of device dicts
    """
    log.info("Fetching all managed devices from Intune...")

    params = {
        "$select" : (
            "id,deviceName,userPrincipalName,operatingSystem,"
            "osVersion,complianceState,lastSyncDateTime,"
            "manufacturer,model"
        ),
        "$top"    : limit,
    }

    if filter_str:
        params["$filter"] = filter_str

    response = _graph_request(
        method   = "GET",
        endpoint = "/deviceManagement/managedDevices",
        params   = params,
    )

    if response is None:
        log.error("Failed to fetch managed devices.")
        return []

    devices = response.get("value", [])
    log.info(f"Fetched {len(devices)} managed device(s) from Intune.")
    return devices


def test_intune_connection() -> bool:
    """
    Test if Microsoft Graph API credentials are working correctly.
    Run this first when setting up the project to verify config.

    Returns:
        True if connected and authenticated, False otherwise
    """
    log.info("Testing Intune / Microsoft Graph API connection...")

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        log.error(
            "Azure credentials not set in .env file.\n"
            "Required variables:\n"
            "  AZURE_TENANT_ID\n"
            "  AZURE_CLIENT_ID\n"
            "  AZURE_CLIENT_SECRET"
        )
        return False

    token = _get_access_token()
    if not token:
        log.error("Failed to get access token. Check Azure credentials.")
        return False

    response = _graph_request(
        method   = "GET",
        endpoint = "/deviceManagement/managedDevices",
        params   = {"$top": 1, "$select": "id,deviceName"},
    )

    if response is None:
        log.error(
            "Graph API call failed. Check Azure app permissions:\n"
            "  DeviceManagementManagedDevices.Read.All\n"
            "  DeviceManagementApps.ReadWrite.All\n"
            "  DeviceManagementConfiguration.ReadWrite.All"
        )
        return False

    log.info("Intune connection test PASSED — credentials working.")
    return True


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("INTUNE API MODULE TEST")
    print("=" * 60 + "\n")

    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: Azure credentials not found in .env file.")
        print("\nAdd these to your config/.env file:\n")
        print("  AZURE_TENANT_ID=your-tenant-id")
        print("  AZURE_CLIENT_ID=your-app-client-id")
        print("  AZURE_CLIENT_SECRET=your-app-client-secret")
        print("\nHow to get these:")
        print("  1. Go to portal.azure.com")
        print("  2. Azure Active Directory → App registrations")
        print("  3. New registration → name: 'AI Ticket Resolver'")
        print("  4. Copy the Application (client) ID → AZURE_CLIENT_ID")
        print("  5. Copy the Directory (tenant) ID  → AZURE_TENANT_ID")
        print("  6. Certificates & secrets → New secret → copy → AZURE_CLIENT_SECRET")
        print("  7. API permissions → Add:")
        print("       DeviceManagementManagedDevices.Read.All")
        print("       DeviceManagementApps.ReadWrite.All")
        print("       DeviceManagementConfiguration.ReadWrite.All")
        print("  8. Grant admin consent for your organization")
        exit(1)

    print("--- Test 1: Connection test ---")
    connected = test_intune_connection()
    print(f"Connection: {'PASSED' if connected else 'FAILED'}")

    if not connected:
        print("Fix credentials and try again.")
        exit(1)

    print("\n--- Test 2: Fetch all managed devices ---")
    devices = get_all_managed_devices(
        filter_str = "operatingSystem eq 'Windows'",
        limit      = 5
    )
    print(f"Windows devices found: {len(devices)}")
    for d in devices:
        print(
            f"  {d.get('deviceName'):<25} "
            f"| OS: {d.get('osVersion'):<15} "
            f"| Compliance: {d.get('complianceState')}"
        )

    print("\n--- Test 3: Fetch all apps in catalog ---")
    apps = get_all_apps_in_catalog()
    print(f"Apps in Intune catalog: {len(apps)}")
    for app in apps[:5]:
        print(
            f"  {app.get('displayName'):<30} "
            f"| Type: {app.get('@odata.type', '').split('.')[-1]}"
        )

    if devices:
        test_device = devices[0]["deviceName"]

        print(f"\n--- Test 4: Get device by name ({test_device}) ---")
        device = get_device_by_name(test_device)
        if device:
            print(f"  Name       : {device.get('deviceName')}")
            print(f"  OS         : {device.get('operatingSystem')} {device.get('osVersion')}")
            print(f"  Compliance : {device.get('complianceState')}")
            print(f"  Last Sync  : {device.get('lastSyncDateTime')}")
            print(f"  Model      : {device.get('manufacturer')} {device.get('model')}")

        print(f"\n--- Test 5: Compliance status ({test_device}) ---")
        compliance = get_device_compliance_status(test_device)
        if compliance:
            print(f"  Compliance State : {compliance['compliance_state']}")
            print(f"  Is Compliant     : {compliance['is_compliant']}")
            print(f"  Management State : {compliance['management_state']}")
            print(f"  Last Sync        : {compliance['last_sync']}")

        print(f"\n--- Test 6: Installed apps on ({test_device}) ---")
        installed = get_installed_apps_on_device(test_device)
        print(f"  Installed apps count: {len(installed)}")
        for app in installed[:5]:
            print(
                f"  {app.get('displayName', 'Unknown'):<35} "
                f"v{app.get('version', 'N/A')}"
            )

        print(f"\n--- Test 7: Sync device ({test_device}) ---")
        synced = sync_device(test_device)
        print(f"  Sync triggered: {'YES' if synced else 'NO'}")

    print("\n" + "=" * 60)
    print("All Intune API tests complete.")
    print("=" * 60)