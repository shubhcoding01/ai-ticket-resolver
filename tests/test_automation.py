import os
import sys
import json
import unittest
import subprocess
from unittest.mock import patch, MagicMock, call
from pathlib       import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.runner import (
    run_automation,
    _build_script_params,
    _execute_powershell,
    _pick_app_name,
    _extract_username_from_email,
    get_supported_categories,
    get_unsupported_categories,
    run_manual_test,
    AUTOMATION_MAP,
    SCRIPTS_DIR,
)


class TestRunAutomation(unittest.TestCase):
    """
    Tests for the main run_automation() entry point.
    Covers all ticket categories, missing machine names,
    missing scripts, and unsupported categories.
    """

    def _make_ticket(
        self,
        ticket_id    = 1001,
        machine_name = "PC-ICICI-0042",
        apps         = None,
        email        = "rahul.sharma@icici.com",
    ):
        return {
            "id"              : ticket_id,
            "subject"         : "Test ticket",
            "machine_name"    : machine_name,
            "mentioned_apps"  : apps or [],
            "requester_email" : email,
        }

    def _make_classification(
        self,
        category         = "app_install",
        priority         = "high",
        can_auto_resolve = True,
        suggested_action = "Install the app remotely.",
    ):
        return {
            "category"        : category,
            "priority"        : priority,
            "can_auto_resolve": can_auto_resolve,
            "suggested_action": suggested_action,
        }

    @patch("automation.runner._execute_powershell")
    def test_app_install_success(self, mock_exec):
        """App install with Zoom and valid machine should succeed."""
        mock_exec.return_value = True

        ticket         = self._make_ticket(apps=["zoom"])
        classification = self._make_classification(category="app_install")

        result = run_automation(ticket, classification)

        self.assertTrue(result)
        mock_exec.assert_called_once()

        call_args = mock_exec.call_args
        params    = call_args[0][1]
        self.assertEqual(params["MachineName"], "PC-ICICI-0042")
        self.assertEqual(params["AppName"],     "zoom")

    @patch("automation.runner._execute_powershell")
    def test_antivirus_update_success(self, mock_exec):
        """Antivirus update on a valid machine should succeed."""
        mock_exec.return_value = True

        ticket         = self._make_ticket()
        classification = self._make_classification(category="antivirus")

        result = run_automation(ticket, classification)

        self.assertTrue(result)
        call_args = mock_exec.call_args
        params    = call_args[0][1]
        self.assertEqual(params["MachineName"], "PC-ICICI-0042")
        self.assertEqual(params["ScanType"],    "full")

    @patch("automation.runner._execute_powershell")
    def test_password_reset_success(self, mock_exec):
        """Password reset should extract AD username from email."""
        mock_exec.return_value = True

        ticket         = self._make_ticket(
            machine_name = "UNKNOWN",
            email        = "priya.mehta@icici.com",
        )
        classification = self._make_classification(category="password_reset")

        result = run_automation(ticket, classification)

        self.assertTrue(result)
        call_args = mock_exec.call_args
        params    = call_args[0][1]
        self.assertEqual(params["Username"], "priya.mehta")

    @patch("automation.runner._execute_powershell")
    def test_printer_fix_success(self, mock_exec):
        """Printer fix on valid machine should run spooler script."""
        mock_exec.return_value = True

        ticket         = self._make_ticket()
        classification = self._make_classification(category="printer")

        result = run_automation(ticket, classification)

        self.assertTrue(result)
        call_args   = mock_exec.call_args
        script_path = call_args[0][0]
        self.assertIn("restart_print_spooler", str(script_path))

    @patch("automation.runner._execute_powershell")
    def test_os_issue_success(self, mock_exec):
        """OS issue repair on valid machine should succeed."""
        mock_exec.return_value = True

        ticket         = self._make_ticket()
        classification = self._make_classification(category="os_issue")

        result = run_automation(ticket, classification)

        self.assertTrue(result)

    @patch("automation.runner._execute_powershell")
    def test_email_issue_success(self, mock_exec):
        """Email issue repair should extract username from email."""
        mock_exec.return_value = True

        ticket         = self._make_ticket(
            email="amit.patel@icici.com"
        )
        classification = self._make_classification(category="email_issue")

        result = run_automation(ticket, classification)

        self.assertTrue(result)
        call_args = mock_exec.call_args
        params    = call_args[0][1]
        self.assertEqual(params["Username"], "amit.patel")

    def test_unknown_machine_returns_false(self):
        """
        Tickets with machine UNKNOWN cannot run remote scripts.
        Should return False without calling execute_
        powershell at all.
        """
        ticket         = self._make_ticket(machine_name="UNKNOWN")
        classification = self._make_classification(category="app_install")

        result = run_automation(ticket, classification)

        self.assertFalse(result)

    def test_hardware_category_returns_false(self):
        """
        Hardware issues have no automation script.
        Should return False immediately.
        """
        ticket         = self._make_ticket()
        classification = self._make_classification(category="hardware")

        result = run_automation(ticket, classification)

        self.assertFalse(result)

    def test_access_permission_returns_false(self):
        """
        Access permission issues have no automation script.
        Should return False immediately.
        """
        ticket         = self._make_ticket()
        classification = self._make_classification(
            category="access_permission"
        )

        result = run_automation(ticket, classification)

        self.assertFalse(result)

    def test_other_category_returns_false(self):
        """
        Other category has no automation script.
        Should return False immediately.
        """
        ticket         = self._make_ticket()
        classification = self._make_classification(category="other")

        result = run_automation(ticket, classification)

        self.assertFalse(result)

    @patch("automation.runner._execute_powershell")
    def test_script_execution_failure_returns_false(self, mock_exec):
        """
        When the PowerShell script exits with non-zero code,
        run_automation should return False.
        """
        mock_exec.return_value = False

        ticket         = self._make_ticket(apps=["zoom"])
        classification = self._make_classification(category="app_install")

        result = run_automation(ticket, classification)

        self.assertFalse(result)

    @patch("automation.runner.os.path.exists")
    def test_missing_script_file_returns_false(self, mock_exists):
        """
        If the automation script file does not exist on disk,
        run_automation should return False without crashing.
        """
        mock_exists.return_value = False

        ticket         = self._make_ticket(apps=["zoom"])
        classification = self._make_classification(category="app_install")

        result = run_automation(ticket, classification)

        self.assertFalse(result)

    def test_empty_ticket_dict_returns_false(self):
        """Empty ticket dict should not crash — return False."""
        result = run_automation({}, {"category": "app_install"})
        self.assertFalse(result)

    def test_none_classification_handled(self):
        """None classification should not crash — return False."""
        ticket = self._make_ticket()
        result = run_automation(ticket, {})
        self.assertFalse(result)


class TestBuildScriptParams(unittest.TestCase):
    """
    Tests for _build_script_params().
    Verifies correct parameter sets are built for each category.
    """

    def test_app_install_params_contain_app_name(self):
        """App install params must include AppName."""
        params = _build_script_params(
            category        = "app_install",
            machine_name    = "PC-0042",
            apps            = ["zoom"],
            requester_email = "user@icici.com",
            ticket_id       = 1001,
        )
        self.assertIn("AppName",     params)
        self.assertIn("MachineName", params)
        self.assertEqual(params["AppName"],     "zoom")
        self.assertEqual(params["MachineName"], "PC-0042")

    def test_antivirus_params_contain_scan_type(self):
        """Antivirus params must include ScanType."""
        params = _build_script_params(
            category        = "antivirus",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1002,
        )
        self.assertIn("ScanType", params)
        self.assertEqual(params["ScanType"], "full")

    def test_password_reset_params_contain_username(self):
        """Password reset params must include Username."""
        params = _build_script_params(
            category        = "password_reset",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "rahul.sharma@icici.com",
            ticket_id       = 1003,
        )
        self.assertIn("Username", params)
        self.assertEqual(params["Username"], "rahul.sharma")

    def test_os_issue_params_contain_action(self):
        """OS issue params must include Action field."""
        params = _build_script_params(
            category        = "os_issue",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1004,
        )
        self.assertIn("Action", params)
        self.assertEqual(params["Action"], "repair")

    def test_printer_params_contain_action(self):
        """Printer params must include Action field."""
        params = _build_script_params(
            category        = "printer",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1005,
        )
        self.assertIn("Action", params)
        self.assertEqual(params["Action"], "restart_spooler")

    def test_email_issue_params_contain_username(self):
        """Email issue params must include Username."""
        params = _build_script_params(
            category        = "email_issue",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "priya.mehta@icici.com",
            ticket_id       = 1006,
        )
        self.assertIn("Username", params)
        self.assertIn("Action",   params)
        self.assertEqual(params["Username"], "priya.mehta")
        self.assertEqual(params["Action"],   "rebuild_profile")

    def test_base_params_always_present(self):
        """MachineName, TicketId, RequesterEmail always in params."""
        params = _build_script_params(
            category        = "antivirus",
            machine_name    = "PC-TEST-001",
            apps            = [],
            requester_email = "test@icici.com",
            ticket_id       = 9999,
        )
        self.assertIn("MachineName",    params)
        self.assertIn("TicketId",       params)
        self.assertIn("RequesterEmail", params)
        self.assertEqual(params["MachineName"],    "PC-TEST-001")
        self.assertEqual(params["TicketId"],       "9999")
        self.assertEqual(params["RequesterEmail"], "test@icici.com")


class TestExecutePowershell(unittest.TestCase):
    """
    Tests for _execute_powershell().
    Uses subprocess mocking to simulate script execution
    without actually running PowerShell.
    """

    @patch("automation.runner.subprocess.run")
    def test_successful_exit_returns_true(self, mock_run):
        """Script that exits with code 0 should return True."""
        mock_result            = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "Script completed successfully."
        mock_result.stderr     = ""
        mock_run.return_value  = mock_result

        result = _execute_powershell(
            script_path = "/fake/path/install_app.ps1",
            params      = {"MachineName": "PC-0042", "AppName": "zoom"},
        )

        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("automation.runner.subprocess.run")
    def test_nonzero_exit_returns_false(self, mock_run):
        """Script that exits with non-zero code should return False."""
        mock_result            = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout     = ""
        mock_result.stderr     = "ERROR: Cannot connect to machine."
        mock_run.return_value  = mock_result

        result = _execute_powershell(
            script_path = "/fake/path/install_app.ps1",
            params      = {"MachineName": "PC-0042"},
        )

        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_timeout_returns_false(self, mock_run):
        """Script that times out should return False gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd     = "powershell",
            timeout = 120,
        )

        result = _execute_powershell(
            script_path = "/fake/path/update_antivirus.ps1",
            params      = {"MachineName": "PC-0042"},
        )

        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_powershell_not_found_returns_false(self, mock_run):
        """Missing PowerShell executable should return False."""
        mock_run.side_effect = FileNotFoundError(
            "powershell.exe not found"
        )

        result = _execute_powershell(
            script_path = "/fake/path/reset_password.ps1",
            params      = {"MachineName": "PC-0042"},
        )

        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_permission_error_returns_false(self, mock_run):
        """Permission denied on script file should return False."""
        mock_run.side_effect = PermissionError(
            "Permission denied: /fake/script.ps1"
        )

        result = _execute_powershell(
            script_path = "/fake/path/script.ps1",
            params      = {"MachineName": "PC-0042"},
        )

        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_params_correctly_passed_to_subprocess(self, mock_run):
        """
        Parameters should be converted to -Key Value pairs
        and passed to the PowerShell command.
        """
        mock_result            = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = ""
        mock_result.stderr     = ""
        mock_run.return_value  = mock_result

        _execute_powershell(
            script_path = "/fake/install.ps1",
            params      = {
                "MachineName" : "PC-0042",
                "AppName"     : "zoom",
                "TicketId"    : "1001",
            },
        )

        call_args = mock_run.call_args[0][0]
        cmd_str   = " ".join(call_args)

        self.assertIn("-MachineName", cmd_str)
        self.assertIn("PC-0042",      cmd_str)
        self.assertIn("-AppName",     cmd_str)
        self.assertIn("zoom",         cmd_str)
        self.assertIn("-TicketId",    cmd_str)
        self.assertIn("1001",         cmd_str)

    @patch("automation.runner.subprocess.run")
    def test_stderr_output_is_logged_but_not_fatal(self, mock_run):
        """
        Script that exits 0 but writes to stderr should still
        return True — stderr alone is not a failure.
        """
        mock_result            = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "Done."
        mock_result.stderr     = "WARNING: Deprecated parameter used."
        mock_run.return_value  = mock_result

        result = _execute_powershell(
            script_path = "/fake/script.ps1",
            params      = {"MachineName": "PC-0042"},
        )

        self.assertTrue(result)

    @patch("automation.runner.subprocess.run")
    def test_unexpected_exception_returns_false(self, mock_run):
        """Unexpected exceptions should be caught and return False."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        result = _execute_powershell(
            script_path = "/fake/script.ps1",
            params      = {"MachineName": "PC-0042"},
        )

        self.assertFalse(result)


class TestPickAppName(unittest.TestCase):
    """
    Tests for _pick_app_name().
    Verifies correct app is selected from a list
    based on priority order.
    """

    def test_zoom_selected_from_list(self):
        """Zoom should be selected when in apps list."""
        result = _pick_app_name(["zoom", "chrome", "teams"])
        self.assertEqual(result, "zoom")

    def test_teams_selected_when_zoom_absent(self):
        """Teams should be selected when Zoom is not present."""
        result = _pick_app_name(["teams", "chrome"])
        self.assertIn(result, ["teams", "microsoft teams"])

    def test_chrome_selected_when_only_option(self):
        """Chrome selected when it is the only app."""
        result = _pick_app_name(["chrome"])
        self.assertEqual(result, "chrome")

    def test_first_app_returned_when_no_priority_match(self):
        """
        When no priority apps match, first app in list is returned.
        """
        result = _pick_app_name(["notepad++", "7zip"])
        self.assertEqual(result, "notepad++")

    def test_empty_list_returns_unknown(self):
        """Empty apps list returns 'unknown_app'."""
        result = _pick_app_name([])
        self.assertEqual(result, "unknown_app")

    def test_priority_order_respected(self):
        """
        Zoom beats Teams beats Chrome in priority.
        """
        result = _pick_app_name(["chrome", "teams", "zoom"])
        self.assertEqual(result, "zoom")

    def test_anyconnect_selected(self):
        """AnyConnect VPN should be selectable."""
        result = _pick_app_name(["anyconnect"])
        self.assertEqual(result, "anyconnect")

    def test_office_selected(self):
        """Microsoft Office should be selectable."""
        result = _pick_app_name(["ms office", "7zip"])
        self.assertIn(result, ["ms office", "microsoft office", "office"])


class TestExtractUsername(unittest.TestCase):
    """
    Tests for _extract_username_from_email().
    Verifies correct AD username extraction from email.
    """

    def test_standard_email(self):
        """Standard email returns part before @."""
        result = _extract_username_from_email("rahul.sharma@icici.com")
        self.assertEqual(result, "rahul.sharma")

    def test_email_lowercased(self):
        """Username should always be returned in lowercase."""
        result = _extract_username_from_email("Rahul.SHARMA@icici.com")
        self.assertEqual(result, "rahul.sharma")

    def test_empty_email_returns_unknown(self):
        """Empty string returns 'unknown_user'."""
        result = _extract_username_from_email("")
        self.assertEqual(result, "unknown_user")

    def test_none_email_returns_unknown(self):
        """None returns 'unknown_user'."""
        result = _extract_username_from_email(None)
        self.assertEqual(result, "unknown_user")

    def test_email_without_at_sign_returns_unknown(self):
        """Invalid email without @ returns 'unknown_user'."""
        result = _extract_username_from_email("notanemail")
        self.assertEqual(result, "unknown_user")

    def test_numeric_username(self):
        """Numeric usernames should work correctly."""
        result = _extract_username_from_email("emp12345@icici.com")
        self.assertEqual(result, "emp12345")

    def test_complex_username(self):
        """Complex usernames with dots and numbers should work."""
        result = _extract_username_from_email(
            "priya.mehta.123@icici.bank.com"
        )
        self.assertEqual(result, "priya.mehta.123")

    def test_whitespace_stripped(self):
        """Leading and trailing whitespace should be stripped."""
        result = _extract_username_from_email(
            "  amit.patel@icici.com  "
        )
        self.assertEqual(result, "amit.patel")


class TestAutomationMap(unittest.TestCase):
    """
    Tests for the AUTOMATION_MAP configuration.
    Verifies correct script assignments for all categories.
    """

    def test_all_categories_present_in_map(self):
        """All expected categories should be in AUTOMATION_MAP."""
        expected = [
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
        for cat in expected:
            self.assertIn(
                cat,
                AUTOMATION_MAP,
                f"Category '{cat}' missing from AUTOMATION_MAP"
            )

    def test_hardware_has_no_script(self):
        """Hardware category must have None as script (no automation)."""
        self.assertIsNone(AUTOMATION_MAP.get("hardware"))

    def test_access_permission_has_no_script(self):
        """Access permission must have None (no automation)."""
        self.assertIsNone(AUTOMATION_MAP.get("access_permission"))

    def test_other_has_no_script(self):
        """Other category must have None (no automation)."""
        self.assertIsNone(AUTOMATION_MAP.get("other"))

    def test_app_install_has_script(self):
        """App install must have a script filename assigned."""
        script = AUTOMATION_MAP.get("app_install")
        self.assertIsNotNone(script)
        self.assertIsInstance(script, str)
        self.assertTrue(script.endswith(".ps1"))

    def test_antivirus_has_script(self):
        """Antivirus must have a script filename assigned."""
        script = AUTOMATION_MAP.get("antivirus")
        self.assertIsNotNone(script)
        self.assertTrue(script.endswith(".ps1"))

    def test_password_reset_has_script(self):
        """Password reset must have a script filename assigned."""
        script = AUTOMATION_MAP.get("password_reset")
        self.assertIsNotNone(script)
        self.assertTrue(script.endswith(".ps1"))


class TestSupportedCategories(unittest.TestCase):
    """
    Tests for get_supported_categories()
    and get_unsupported_categories().
    """

    def test_supported_categories_not_empty(self):
        """Supported categories list should not be empty."""
        cats = get_supported_categories()
        self.assertGreater(len(cats), 0)

    def test_unsupported_categories_not_empty(self):
        """Unsupported categories list should not be empty."""
        cats = get_unsupported_categories()
        self.assertGreater(len(cats), 0)

    def test_hardware_in_unsupported(self):
        """Hardware must be in unsupported categories."""
        self.assertIn("hardware", get_unsupported_categories())

    def test_app_install_in_supported(self):
        """app_install must be in supported categories."""
        self.assertIn("app_install", get_supported_categories())

    def test_no_overlap_between_supported_and_unsupported(self):
        """No category should appear in both lists."""
        supported   = set(get_supported_categories())
        unsupported = set(get_unsupported_categories())
        overlap     = supported & unsupported
        self.assertEqual(
            len(overlap),
            0,
            f"Categories in both lists: {overlap}"
        )

    def test_supported_plus_unsupported_covers_all(self):
        """
        Union of supported and unsupported should equal
        all keys in AUTOMATION_MAP.
        """
        supported   = set(get_supported_categories())
        unsupported = set(get_unsupported_categories())
        all_cats    = set(AUTOMATION_MAP.keys())
        self.assertEqual(supported | unsupported, all_cats)


class TestRunManualTest(unittest.TestCase):
    """
    Tests for run_manual_test() helper function.
    Verifies it builds correct fake ticket and classification.
    """

    @patch("automation.runner._execute_powershell")
    def test_manual_test_app_install(self, mock_exec):
        """Manual test for app_install should call execute."""
        mock_exec.return_value = True

        result = run_manual_test(
            category     = "app_install",
            machine_name = "PC-TEST-001",
            app_name     = "zoom",
            email        = "test@icici.com",
        )

        self.assertTrue(result)
        mock_exec.assert_called_once()

    @patch("automation.runner._execute_powershell")
    def test_manual_test_antivirus(self, mock_exec):
        """Manual test for antivirus should call execute."""
        mock_exec.return_value = True

        result = run_manual_test(
            category     = "antivirus",
            machine_name = "PC-TEST-002",
        )

        self.assertTrue(result)

    def test_manual_test_hardware_returns_false(self):
        """
        Manual test for hardware should return False
        as there is no script for it.
        """
        result = run_manual_test(
            category     = "hardware",
            machine_name = "PC-TEST-003",
        )
        self.assertFalse(result)

    def test_manual_test_unknown_machine_returns_false(self):
        """
        Manual test with UNKNOWN machine should return False
        since remote scripts need a target machine.
        """
        result = run_manual_test(
            category     = "app_install",
            machine_name = "UNKNOWN",
            app_name     = "zoom",
        )
        self.assertFalse(result)


class TestScriptFilesExist(unittest.TestCase):
    """
    Tests that verify the PowerShell script files actually
    exist on disk in the scripts/ directory.
    Warns when expected scripts are missing.
    """

    def test_scripts_directory_exists(self):
        """The automation/scripts/ directory must exist."""
        self.assertTrue(
            os.path.isdir(SCRIPTS_DIR),
            f"Scripts directory not found: {SCRIPTS_DIR}"
        )

    def test_expected_scripts_exist(self):
        """
        Each category in AUTOMATION_MAP that has a script
        should have the corresponding .ps1 file on disk.
        """
        missing = []

        for category, script_name in AUTOMATION_MAP.items():
            if script_name is None:
                continue

            script_path = os.path.join(SCRIPTS_DIR, script_name)
            if not os.path.exists(script_path):
                missing.append(f"{category} → {script_name}")

        if missing:
            missing_str = "\n  ".join(missing)
            self.fail(
                f"Missing PowerShell script files:\n  {missing_str}\n"
                "Create these .ps1 files in automation/scripts/"
            )

    def test_all_scripts_are_ps1_files(self):
        """All scripts in AUTOMATION_MAP must end in .ps1."""
        for category, script_name in AUTOMATION_MAP.items():
            if script_name is not None:
                self.assertTrue(
                    script_name.endswith(".ps1"),
                    f"Script for '{category}' does not end in .ps1: "
                    f"'{script_name}'"
                )

    def test_script_files_not_empty(self):
        """
        PowerShell scripts that exist on disk should
        not be empty files.
        """
        for category, script_name in AUTOMATION_MAP.items():
            if script_name is None:
                continue

            script_path = os.path.join(SCRIPTS_DIR, script_name)
            if os.path.exists(script_path):
                size = os.path.getsize(script_path)
                self.assertGreater(
                    size,
                    0,
                    f"Script file is empty: {script_name}"
                )


class TestEdgeCases(unittest.TestCase):
    """
    Tests for edge cases and boundary conditions
    across all automation functions.
    """

    @patch("automation.runner._execute_powershell")
    def test_multiple_apps_picks_best(self, mock_exec):
        """
        When ticket mentions multiple apps, runner should
        pick the highest priority one (Zoom over Chrome).
        """
        mock_exec.return_value = True

        ticket = {
            "id"              : 5001,
            "machine_name"    : "PC-0001",
            "mentioned_apps"  : ["chrome", "zoom", "7zip"],
            "requester_email" : "user@icici.com",
        }
        classification = {
            "category"        : "app_install",
            "priority"        : "high",
            "can_auto_resolve": True,
            "suggested_action": "Install app.",
        }

        run_automation(ticket, classification)

        call_args = mock_exec.call_args[0][1]
        self.assertEqual(call_args["AppName"], "zoom")

    @patch("automation.runner._execute_powershell")
    def test_ticket_id_passed_to_script(self, mock_exec):
        """Ticket ID must always be passed to the script."""
        mock_exec.return_value = True

        ticket = {
            "id"              : 9876,
            "machine_name"    : "PC-0001",
            "mentioned_apps"  : [],
            "requester_email" : "user@icici.com",
        }
        classification = {
            "category"        : "antivirus",
            "priority"        : "medium",
            "can_auto_resolve": True,
            "suggested_action": "Update AV.",
        }

        run_automation(ticket, classification)

        call_args = mock_exec.call_args[0][1]
        self.assertEqual(call_args["TicketId"], "9876")

    @patch("automation.runner._execute_powershell")
    def test_special_chars_in_machine_name_handled(self, mock_exec):
        """Machine names with hyphens should be handled fine."""
        mock_exec.return_value = True

        ticket = {
            "id"              : 1001,
            "machine_name"    : "PC-ICICI-DESK-0042",
            "mentioned_apps"  : ["zoom"],
            "requester_email" : "user@icici.com",
        }
        classification = {
            "category"        : "app_install",
            "priority"        : "high",
            "can_auto_resolve": True,
            "suggested_action": "Install Zoom.",
        }

        result = run_automation(ticket, classification)

        self.assertTrue(result)
        call_args = mock_exec.call_args[0][1]
        self.assertEqual(
            call_args["MachineName"],
            "PC-ICICI-DESK-0042"
        )

    def test_unknown_category_returns_false(self):
        """Completely unknown category returns False gracefully."""
        ticket = {
            "id"              : 1001,
            "machine_name"    : "PC-0042",
            "mentioned_apps"  : [],
            "requester_email" : "user@icici.com",
        }
        classification = {
            "category"        : "totally_unknown_cat",
            "priority"        : "low",
            "can_auto_resolve": True,
            "suggested_action": "Unknown action.",
        }

        result = run_automation(ticket, classification)
        self.assertFalse(result)


def run_all_tests():
    """
    Run the complete test suite and print a formatted summary.
    Called when running this file directly.
    """
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestRunAutomation,
        TestBuildScriptParams,
        TestExecutePowershell,
        TestPickAppName,
        TestExtractUsername,
        TestAutomationMap,
        TestSupportedCategories,
        TestRunManualTest,
        TestScriptFilesExist,
        TestEdgeCases,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(
        verbosity = 2,
        stream    = sys.stdout,
    )

    print("\n" + "=" * 65)
    print("AUTOMATION TEST SUITE")
    print("=" * 65 + "\n")

    result = runner.run(suite)

    print("\n" + "=" * 65)
    print("TEST SUMMARY")
    print("=" * 65)
    print(f"  Tests run    : {result.testsRun}")
    print(f"  Passed       : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures     : {len(result.failures)}")
    print(f"  Errors       : {len(result.errors)}")
    print(f"  Skipped      : {len(result.skipped)}")
    print(
        f"  Overall      : "
        f"{'PASSED' if result.wasSuccessful() else 'FAILED'}"
    )
    print("=" * 65 + "\n")

    return result.wasSuccessful()


# if __name__ == "__main__":
#     success = run_all_tests()
#     sys.exit(0 if success else 1)


import os
import sys
import json
import unittest
import subprocess
from unittest.mock import patch, MagicMock, call
from pathlib       import Path

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

os.environ.setdefault("DEMO_MODE",    "true")
os.environ.setdefault("DRY_RUN_MODE", "false")

from automation.runner import (
    run_automation,
    _build_script_params,
    _execute_powershell,
    _pick_app_name,
    _extract_username_from_email,
    _run_demo_automation,
    get_supported_categories,
    get_unsupported_categories,
    run_manual_test,
    AUTOMATION_MAP,
    AUTOMATION_MAP,
    SCRIPTS_DIR,
    DEMO_MODE,
    DRY_RUN_MODE,
    MOCK_AUTOMATION_RESULTS,
    MOCK_AUTOMATION_OUTPUT,
)


def _make_ticket(
    ticket_id    : int  = 1001,
    machine_name : str  = "PC-ICICI-0042",
    apps         : list = None,
    email        : str  = "rahul.sharma@icici.com",
) -> dict:
    """Helper — build a minimal valid ticket dict."""
    return {
        "id"              : ticket_id,
        "subject"         : "Test ticket",
        "machine_name"    : machine_name,
        "mentioned_apps"  : apps or [],
        "requester_email" : email,
    }


def _make_classification(
    category         : str  = "app_install",
    priority         : str  = "high",
    can_auto_resolve : bool = True,
    suggested_action : str  = "Install the app remotely.",
) -> dict:
    """Helper — build a minimal valid classification dict."""
    return {
        "category"        : category,
        "priority"        : priority,
        "can_auto_resolve": can_auto_resolve,
        "suggested_action": suggested_action,
    }


class TestRunAutomation(unittest.TestCase):
    """
    Tests for the main run_automation() entry point.
    In demo mode _run_demo_automation() is called instead
    of _execute_powershell() so we patch accordingly.
    """

    @patch("automation.runner._run_demo_automation")
    def test_app_install_success(self, mock_demo):
        """App install with valid machine returns True in demo mode."""
        mock_demo.return_value = True

        ticket         = _make_ticket(apps=["zoom"])
        classification = _make_classification(category="app_install")

        result = run_automation(ticket, classification)
        self.assertTrue(result)

    @patch("automation.runner._run_demo_automation")
    def test_antivirus_update_success(self, mock_demo):
        """Antivirus update on valid machine returns True."""
        mock_demo.return_value = True

        ticket         = _make_ticket()
        classification = _make_classification(category="antivirus")

        result = run_automation(ticket, classification)
        self.assertTrue(result)

    @patch("automation.runner._run_demo_automation")
    def test_password_reset_success(self, mock_demo):
        """Password reset returns True in demo mode."""
        mock_demo.return_value = True

        ticket         = _make_ticket(
            machine_name = "PC-ICICI-0099",
            email        = "priya.mehta@icici.com",
        )
        classification = _make_classification(
            category="password_reset"
        )

        result = run_automation(ticket, classification)
        self.assertTrue(result)

    @patch("automation.runner._run_demo_automation")
    def test_printer_fix_success(self, mock_demo):
        """Printer fix on valid machine returns True."""
        mock_demo.return_value = True

        ticket         = _make_ticket()
        classification = _make_classification(category="printer")

        result = run_automation(ticket, classification)
        self.assertTrue(result)

    @patch("automation.runner._run_demo_automation")
    def test_os_issue_success(self, mock_demo):
        """OS issue repair returns True in demo mode."""
        mock_demo.return_value = True

        ticket         = _make_ticket()
        classification = _make_classification(category="os_issue")

        result = run_automation(ticket, classification)
        self.assertTrue(result)

    @patch("automation.runner._run_demo_automation")
    def test_email_issue_success(self, mock_demo):
        """Email issue repair returns True in demo mode."""
        mock_demo.return_value = True

        ticket         = _make_ticket(
            email="amit.patel@icici.com"
        )
        classification = _make_classification(
            category="email_issue"
        )

        result = run_automation(ticket, classification)
        self.assertTrue(result)

    def test_unknown_machine_returns_false(self):
        """
        Machine UNKNOWN cannot run remote automation.
        Must return False without calling any script.
        """
        ticket         = _make_ticket(machine_name="UNKNOWN")
        classification = _make_classification(
            category="app_install"
        )

        result = run_automation(ticket, classification)
        self.assertFalse(result)

    def test_hardware_category_returns_false(self):
        """Hardware has no automation script — returns False."""
        ticket         = _make_ticket()
        classification = _make_classification(
            category="hardware"
        )

        result = run_automation(ticket, classification)
        self.assertFalse(result)

    def test_access_permission_returns_false(self):
        """Access permission has no script — returns False."""
        ticket         = _make_ticket()
        classification = _make_classification(
            category="access_permission"
        )

        result = run_automation(ticket, classification)
        self.assertFalse(result)

    def test_other_category_returns_false(self):
        """Other category has no script — returns False."""
        ticket         = _make_ticket()
        classification = _make_classification(category="other")

        result = run_automation(ticket, classification)
        self.assertFalse(result)

    @patch("automation.runner._run_demo_automation")
    def test_script_failure_returns_false(self, mock_demo):
        """When demo automation returns False, result is False."""
        mock_demo.return_value = False

        ticket         = _make_ticket(apps=["zoom"])
        classification = _make_classification(
            category="app_install"
        )

        result = run_automation(ticket, classification)
        self.assertFalse(result)

    def test_empty_ticket_dict_returns_false(self):
        """Empty ticket dict must not crash — returns False."""
        result = run_automation(
            {}, {"category": "app_install"}
        )
        self.assertFalse(result)

    def test_empty_classification_returns_false(self):
        """Empty classification dict must not crash — returns False."""
        result = run_automation(_make_ticket(), {})
        self.assertFalse(result)

    def test_unknown_category_returns_false(self):
        """Completely unknown category returns False gracefully."""
        ticket = _make_ticket()
        classification = _make_classification(
            category="totally_made_up_category"
        )
        result = run_automation(ticket, classification)
        self.assertFalse(result)

    @patch("automation.runner._run_demo_automation")
    def test_demo_automation_called_with_correct_args(
        self, mock_demo
    ):
        """
        In demo mode _run_demo_automation must be called
        with the correct ticket_id, category, script_name,
        machine_name, and params.
        """
        mock_demo.return_value = True

        ticket         = _make_ticket(
            ticket_id    = 9001,
            machine_name = "PC-TEST-001",
            apps         = ["zoom"],
        )
        classification = _make_classification(
            category="app_install"
        )

        run_automation(ticket, classification)

        mock_demo.assert_called_once()
        call_kwargs = mock_demo.call_args[1]

        self.assertEqual(call_kwargs["ticket_id"],    9001)
        self.assertEqual(call_kwargs["category"],     "app_install")
        self.assertEqual(
            call_kwargs["script_name"], "install_app.ps1"
        )
        self.assertEqual(
            call_kwargs["machine_name"], "PC-TEST-001"
        )
        self.assertIn("MachineName", call_kwargs["params"])


class TestRunDemoAutomation(unittest.TestCase):
    """
    Tests for _run_demo_automation().
    Verifies correct simulation behavior per category.
    """

    def test_app_install_demo_succeeds(self):
        """app_install should succeed in demo mode."""
        result = _run_demo_automation(
            ticket_id    = 1001,
            category     = "app_install",
            script_name  = "install_app.ps1",
            machine_name = "PC-ICICI-0042",
            params       = {"MachineName": "PC-ICICI-0042"},
        )
        self.assertTrue(result)

    def test_antivirus_demo_succeeds(self):
        """antivirus should succeed in demo mode."""
        result = _run_demo_automation(
            ticket_id    = 1002,
            category     = "antivirus",
            script_name  = "update_antivirus.ps1",
            machine_name = "LAPTOP-ICICI-115",
            params       = {"MachineName": "LAPTOP-ICICI-115"},
        )
        self.assertTrue(result)

    def test_password_reset_demo_succeeds(self):
        """password_reset should succeed in demo mode."""
        result = _run_demo_automation(
            ticket_id    = 1003,
            category     = "password_reset",
            script_name  = "reset_password.ps1",
            machine_name = "PC-ICICI-0099",
            params       = {
                "MachineName": "PC-ICICI-0099",
                "Username"   : "rahul.sharma",
            },
        )
        self.assertTrue(result)

    def test_hardware_demo_fails(self):
        """hardware should fail in demo mode — no script."""
        result = _run_demo_automation(
            ticket_id    = 1007,
            category     = "hardware",
            script_name  = "no_script.ps1",
            machine_name = "LAPTOP-ICICI-220",
            params       = {"MachineName": "LAPTOP-ICICI-220"},
        )
        self.assertFalse(result)

    def test_network_demo_fails(self):
        """network should fail in demo mode."""
        result = _run_demo_automation(
            ticket_id    = 1004,
            category     = "network",
            script_name  = "fix_network_adapter.ps1",
            machine_name = "LAPTOP-ICICI-088",
            params       = {"MachineName": "LAPTOP-ICICI-088"},
        )
        self.assertFalse(result)

    def test_all_auto_resolvable_categories_succeed(self):
        """All categories in MOCK_AUTOMATION_RESULTS=True succeed."""
        success_cats = [
            cat for cat, ok in MOCK_AUTOMATION_RESULTS.items()
            if ok is True
        ]
        for cat in success_cats:
            script = AUTOMATION_MAP.get(cat, "no_script.ps1")
            result = _run_demo_automation(
                ticket_id    = 9999,
                category     = cat,
                script_name  = script or "no_script.ps1",
                machine_name = "PC-TEST-001",
                params       = {"MachineName": "PC-TEST-001"},
            )
            self.assertTrue(
                result,
                f"Category '{cat}' should succeed in demo mode"
            )

    def test_all_non_auto_resolvable_categories_fail(self):
        """All categories in MOCK_AUTOMATION_RESULTS=False fail."""
        fail_cats = [
            cat for cat, ok in MOCK_AUTOMATION_RESULTS.items()
            if ok is False
        ]
        for cat in fail_cats:
            script = AUTOMATION_MAP.get(cat, "no_script.ps1")
            result = _run_demo_automation(
                ticket_id    = 9999,
                category     = cat,
                script_name  = script or "no_script.ps1",
                machine_name = "PC-TEST-001",
                params       = {"MachineName": "PC-TEST-001"},
            )
            self.assertFalse(
                result,
                f"Category '{cat}' should fail in demo mode"
            )

    def test_returns_bool(self):
        """_run_demo_automation must always return a bool."""
        result = _run_demo_automation(
            ticket_id    = 1001,
            category     = "app_install",
            script_name  = "install_app.ps1",
            machine_name = "PC-TEST-001",
            params       = {},
        )
        self.assertIsInstance(result, bool)


class TestBuildScriptParams(unittest.TestCase):
    """
    Tests for _build_script_params().
    Verifies correct parameter sets built for each category.
    """

    def test_app_install_contains_app_name(self):
        """App install params must include AppName."""
        params = _build_script_params(
            category        = "app_install",
            machine_name    = "PC-0042",
            apps            = ["zoom"],
            requester_email = "user@icici.com",
            ticket_id       = 1001,
        )
        self.assertIn("AppName",     params)
        self.assertIn("MachineName", params)
        self.assertEqual(params["AppName"],     "zoom")
        self.assertEqual(params["MachineName"], "PC-0042")

    def test_antivirus_contains_scan_type(self):
        """Antivirus params must include ScanType=full."""
        params = _build_script_params(
            category        = "antivirus",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1002,
        )
        self.assertIn("ScanType", params)
        self.assertEqual(params["ScanType"], "full")

    def test_password_reset_contains_username(self):
        """Password reset params must include Username."""
        params = _build_script_params(
            category        = "password_reset",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "rahul.sharma@icici.com",
            ticket_id       = 1003,
        )
        self.assertIn("Username", params)
        self.assertEqual(params["Username"], "rahul.sharma")

    def test_os_issue_contains_action_repair(self):
        """OS issue params must include Action=repair."""
        params = _build_script_params(
            category        = "os_issue",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1004,
        )
        self.assertIn("Action", params)
        self.assertEqual(params["Action"], "repair")

    def test_printer_contains_action_spooler(self):
        """Printer params must include Action=restart_spooler."""
        params = _build_script_params(
            category        = "printer",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1005,
        )
        self.assertIn("Action", params)
        self.assertEqual(params["Action"], "restart_spooler")

    def test_email_issue_contains_username_and_action(self):
        """Email issue params must include Username and Action."""
        params = _build_script_params(
            category        = "email_issue",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "priya.mehta@icici.com",
            ticket_id       = 1006,
        )
        self.assertIn("Username", params)
        self.assertIn("Action",   params)
        self.assertEqual(params["Username"], "priya.mehta")
        self.assertEqual(params["Action"],   "rebuild_profile")

    def test_base_params_always_present(self):
        """MachineName, TicketId, RequesterEmail always present."""
        params = _build_script_params(
            category        = "antivirus",
            machine_name    = "PC-TEST-001",
            apps            = [],
            requester_email = "test@icici.com",
            ticket_id       = 9999,
        )
        self.assertIn("MachineName",    params)
        self.assertIn("TicketId",       params)
        self.assertIn("RequesterEmail", params)
        self.assertEqual(params["MachineName"],    "PC-TEST-001")
        self.assertEqual(params["TicketId"],       "9999")
        self.assertEqual(params["RequesterEmail"], "test@icici.com")

    def test_network_contains_action_reset(self):
        """Network params must include Action=reset_adapter."""
        params = _build_script_params(
            category        = "network",
            machine_name    = "PC-0042",
            apps            = [],
            requester_email = "user@icici.com",
            ticket_id       = 1007,
        )
        self.assertIn("Action", params)
        self.assertEqual(params["Action"], "reset_adapter")


class TestExecutePowershell(unittest.TestCase):
    """
    Tests for _execute_powershell().
    Mocks subprocess.run — no real PowerShell executed.
    These tests verify live-mode script execution behavior.
    """

    @patch("automation.runner.subprocess.run")
    def test_exit_zero_returns_true(self, mock_run):
        """Exit code 0 means success — returns True."""
        mock_result            = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "Script completed."
        mock_result.stderr     = ""
        mock_run.return_value  = mock_result

        result = _execute_powershell(
            script_path = "/fake/install_app.ps1",
            params      = {
                "MachineName": "PC-0042",
                "AppName"    : "zoom",
            },
        )
        self.assertTrue(result)

    @patch("automation.runner.subprocess.run")
    def test_nonzero_exit_returns_false(self, mock_run):
        """Non-zero exit code means failure — returns False."""
        mock_result            = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout     = ""
        mock_result.stderr     = "ERROR: Cannot connect."
        mock_run.return_value  = mock_result

        result = _execute_powershell(
            script_path = "/fake/install_app.ps1",
            params      = {"MachineName": "PC-0042"},
        )
        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_timeout_returns_false(self, mock_run):
        """Script timeout returns False without crashing."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="powershell", timeout=120
        )
        result = _execute_powershell(
            script_path = "/fake/update_antivirus.ps1",
            params      = {"MachineName": "PC-0042"},
        )
        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_powershell_not_found_returns_false(self, mock_run):
        """Missing PowerShell executable returns False."""
        mock_run.side_effect = FileNotFoundError(
            "powershell.exe not found"
        )
        result = _execute_powershell(
            script_path = "/fake/reset_password.ps1",
            params      = {"MachineName": "PC-0042"},
        )
        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_permission_error_returns_false(self, mock_run):
        """Permission denied on script returns False."""
        mock_run.side_effect = PermissionError(
            "Permission denied"
        )
        result = _execute_powershell(
            script_path = "/fake/script.ps1",
            params      = {"MachineName": "PC-0042"},
        )
        self.assertFalse(result)

    @patch("automation.runner.subprocess.run")
    def test_params_passed_as_key_value_pairs(self, mock_run):
        """Parameters must be passed as -Key Value pairs."""
        mock_result            = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = ""
        mock_result.stderr     = ""
        mock_run.return_value  = mock_result

        _execute_powershell(
            script_path = "/fake/install.ps1",
            params      = {
                "MachineName" : "PC-0042",
                "AppName"     : "zoom",
                "TicketId"    : "1001",
            },
        )

        cmd_str = " ".join(mock_run.call_args[0][0])
        self.assertIn("-MachineName", cmd_str)
        self.assertIn("PC-0042",      cmd_str)
        self.assertIn("-AppName",     cmd_str)
        self.assertIn("zoom",         cmd_str)
        self.assertIn("-TicketId",    cmd_str)
        self.assertIn("1001",         cmd_str)

    @patch("automation.runner.subprocess.run")
    def test_stderr_with_zero_exit_still_true(self, mock_run):
        """Exit 0 with stderr output is still a success."""
        mock_result            = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "Done."
        mock_result.stderr     = "WARNING: Deprecated parameter."
        mock_run.return_value  = mock_result

        result = _execute_powershell(
            script_path = "/fake/script.ps1",
            params      = {"MachineName": "PC-0042"},
        )
        self.assertTrue(result)

    @patch("automation.runner.subprocess.run")
    def test_unexpected_exception_returns_false(self, mock_run):
        """Any unexpected exception returns False."""
        mock_run.side_effect = RuntimeError("Unexpected")
        result = _execute_powershell(
            script_path = "/fake/script.ps1",
            params      = {"MachineName": "PC-0042"},
        )
        self.assertFalse(result)


class TestPickAppName(unittest.TestCase):
    """Tests for _pick_app_name()."""

    def test_zoom_selected_from_mixed_list(self):
        """Zoom beats other apps in priority order."""
        result = _pick_app_name(["chrome", "zoom", "teams"])
        self.assertEqual(result, "zoom")

    def test_teams_selected_when_zoom_absent(self):
        """Teams selected when Zoom not present."""
        result = _pick_app_name(["teams", "chrome"])
        self.assertIn(result, ["teams", "microsoft teams"])

    def test_chrome_only(self):
        """Chrome returned when it is the only app."""
        result = _pick_app_name(["chrome"])
        self.assertEqual(result, "chrome")

    def test_no_priority_match_returns_first(self):
        """No priority match — first app in list returned."""
        result = _pick_app_name(["notepad++", "7zip"])
        self.assertEqual(result, "notepad++")

    def test_empty_list_returns_unknown_app(self):
        """Empty list returns 'unknown_app'."""
        result = _pick_app_name([])
        self.assertEqual(result, "unknown_app")

    def test_zoom_beats_chrome_and_teams(self):
        """Zoom always wins over Chrome and Teams."""
        result = _pick_app_name(["chrome", "teams", "zoom"])
        self.assertEqual(result, "zoom")

    def test_anyconnect_selectable(self):
        """AnyConnect VPN can be selected."""
        result = _pick_app_name(["anyconnect"])
        self.assertEqual(result, "anyconnect")

    def test_office_selectable(self):
        """Microsoft Office can be selected."""
        result = _pick_app_name(["ms office", "7zip"])
        self.assertIn(
            result,
            ["ms office", "microsoft office", "office"]
        )

    def test_outlook_selectable(self):
        """Outlook can be selected from apps list."""
        result = _pick_app_name(["outlook"])
        self.assertEqual(result, "outlook")


class TestExtractUsername(unittest.TestCase):
    """Tests for _extract_username_from_email()."""

    def test_standard_icici_email(self):
        """Standard email extracts part before @."""
        result = _extract_username_from_email(
            "rahul.sharma@icici.com"
        )
        self.assertEqual(result, "rahul.sharma")

    def test_uppercase_email_lowercased(self):
        """Result is always lowercase."""
        result = _extract_username_from_email(
            "Rahul.SHARMA@icici.com"
        )
        self.assertEqual(result, "rahul.sharma")

    def test_empty_string_returns_unknown(self):
        """Empty string returns 'unknown_user'."""
        result = _extract_username_from_email("")
        self.assertEqual(result, "unknown_user")

    def test_none_returns_unknown(self):
        """None returns 'unknown_user'."""
        result = _extract_username_from_email(None)
        self.assertEqual(result, "unknown_user")

    def test_no_at_sign_returns_unknown(self):
        """String without @ returns 'unknown_user'."""
        result = _extract_username_from_email("notanemail")
        self.assertEqual(result, "unknown_user")

    def test_numeric_username(self):
        """Numeric prefix works correctly."""
        result = _extract_username_from_email(
            "emp12345@icici.com"
        )
        self.assertEqual(result, "emp12345")

    def test_complex_dotted_username(self):
        """Complex dotted username works correctly."""
        result = _extract_username_from_email(
            "priya.mehta.123@icici.bank.com"
        )
        self.assertEqual(result, "priya.mehta.123")

    def test_whitespace_stripped(self):
        """Leading and trailing whitespace is stripped."""
        result = _extract_username_from_email(
            "  amit.patel@icici.com  "
        )
        self.assertEqual(result, "amit.patel")


class TestAutomationMap(unittest.TestCase):
    """Tests for the AUTOMATION_MAP configuration dict."""

    def test_all_required_categories_present(self):
        """All 10 expected categories must be in AUTOMATION_MAP."""
        expected = [
            "app_install",    "antivirus",
            "password_reset", "network",
            "printer",        "email_issue",
            "hardware",       "os_issue",
            "access_permission", "other",
        ]
        for cat in expected:
            self.assertIn(
                cat, AUTOMATION_MAP,
                f"'{cat}' missing from AUTOMATION_MAP"
            )

    def test_hardware_maps_to_none(self):
        """Hardware has no script — must be None."""
        self.assertIsNone(AUTOMATION_MAP.get("hardware"))

    def test_access_permission_maps_to_none(self):
        """Access permission has no script — must be None."""
        self.assertIsNone(
            AUTOMATION_MAP.get("access_permission")
        )

    def test_other_maps_to_none(self):
        """Other category has no script — must be None."""
        self.assertIsNone(AUTOMATION_MAP.get("other"))

    def test_app_install_script_is_ps1(self):
        """App install script must exist and end in .ps1."""
        script = AUTOMATION_MAP.get("app_install")
        self.assertIsNotNone(script)
        self.assertIsInstance(script, str)
        self.assertTrue(script.endswith(".ps1"))

    def test_antivirus_script_is_ps1(self):
        """Antivirus script must end in .ps1."""
        self.assertTrue(
            AUTOMATION_MAP.get("antivirus", "").endswith(".ps1")
        )

    def test_password_reset_script_is_ps1(self):
        """Password reset script must end in .ps1."""
        self.assertTrue(
            AUTOMATION_MAP.get(
                "password_reset", ""
            ).endswith(".ps1")
        )

    def test_printer_script_is_ps1(self):
        """Printer script must end in .ps1."""
        self.assertTrue(
            AUTOMATION_MAP.get("printer", "").endswith(".ps1")
        )

    def test_os_issue_script_is_ps1(self):
        """OS issue script must end in .ps1."""
        self.assertTrue(
            AUTOMATION_MAP.get("os_issue", "").endswith(".ps1")
        )

    def test_email_issue_script_is_ps1(self):
        """Email issue script must end in .ps1."""
        self.assertTrue(
            AUTOMATION_MAP.get(
                "email_issue", ""
            ).endswith(".ps1")
        )


class TestMockAutomationData(unittest.TestCase):
    """
    Tests for MOCK_AUTOMATION_RESULTS and MOCK_AUTOMATION_OUTPUT.
    Verifies demo data is complete and consistent.
    """

    def test_all_categories_in_mock_results(self):
        """MOCK_AUTOMATION_RESULTS must cover all categories."""
        all_cats = set(AUTOMATION_MAP.keys())
        mock_cats = set(MOCK_AUTOMATION_RESULTS.keys())
        missing = all_cats - mock_cats
        self.assertEqual(
            len(missing), 0,
            f"Missing from MOCK_AUTOMATION_RESULTS: {missing}"
        )

    def test_all_categories_in_mock_output(self):
        """MOCK_AUTOMATION_OUTPUT must cover all categories."""
        all_cats  = set(AUTOMATION_MAP.keys())
        mock_cats = set(MOCK_AUTOMATION_OUTPUT.keys())
        missing   = all_cats - mock_cats
        self.assertEqual(
            len(missing), 0,
            f"Missing from MOCK_AUTOMATION_OUTPUT: {missing}"
        )

    def test_mock_results_are_booleans(self):
        """All values in MOCK_AUTOMATION_RESULTS must be bool."""
        for cat, val in MOCK_AUTOMATION_RESULTS.items():
            self.assertIsInstance(
                val, bool,
                f"MOCK_AUTOMATION_RESULTS['{cat}'] is not bool"
            )

    def test_mock_output_are_strings(self):
        """All values in MOCK_AUTOMATION_OUTPUT must be str."""
        for cat, val in MOCK_AUTOMATION_OUTPUT.items():
            self.assertIsInstance(
                val, str,
                f"MOCK_AUTOMATION_OUTPUT['{cat}'] is not str"
            )
            self.assertGreater(
                len(val), 5,
                f"MOCK_AUTOMATION_OUTPUT['{cat}'] too short"
            )

    def test_auto_resolvable_categories_succeed_in_mock(self):
        """Categories with scripts should succeed in mock."""
        for cat in get_supported_categories():
            self.assertTrue(
                MOCK_AUTOMATION_RESULTS.get(cat, False),
                f"Category '{cat}' should be True in mock results"
            )

    def test_non_auto_resolvable_categories_fail_in_mock(self):
        """Categories without scripts should fail in mock."""
        for cat in get_unsupported_categories():
            self.assertFalse(
                MOCK_AUTOMATION_RESULTS.get(cat, False),
                f"Category '{cat}' should be False in mock results"
            )


class TestSupportedCategories(unittest.TestCase):
    """Tests for get_supported_categories() and get_unsupported_categories()."""

    def test_supported_not_empty(self):
        """Supported list must not be empty."""
        self.assertGreater(len(get_supported_categories()), 0)

    def test_unsupported_not_empty(self):
        """Unsupported list must not be empty."""
        self.assertGreater(len(get_unsupported_categories()), 0)

    def test_hardware_in_unsupported(self):
        """Hardware must be in unsupported."""
        self.assertIn("hardware", get_unsupported_categories())

    def test_app_install_in_supported(self):
        """app_install must be in supported."""
        self.assertIn("app_install", get_supported_categories())

    def test_antivirus_in_supported(self):
        """antivirus must be in supported."""
        self.assertIn("antivirus", get_supported_categories())

    def test_password_reset_in_supported(self):
        """password_reset must be in supported."""
        self.assertIn(
            "password_reset", get_supported_categories()
        )

    def test_access_permission_in_unsupported(self):
        """access_permission must be in unsupported."""
        self.assertIn(
            "access_permission", get_unsupported_categories()
        )

    def test_no_overlap(self):
        """No category in both lists."""
        supported   = set(get_supported_categories())
        unsupported = set(get_unsupported_categories())
        overlap     = supported & unsupported
        self.assertEqual(
            len(overlap), 0,
            f"Overlap found: {overlap}"
        )

    def test_union_covers_all_map_keys(self):
        """Supported + Unsupported = all AUTOMATION_MAP keys."""
        union   = (
            set(get_supported_categories())
            | set(get_unsupported_categories())
        )
        all_cats = set(AUTOMATION_MAP.keys())
        self.assertEqual(union, all_cats)


class TestRunManualTest(unittest.TestCase):
    """Tests for run_manual_test() developer helper."""

    @patch("automation.runner._run_demo_automation")
    def test_app_install_manual_test(self, mock_demo):
        """Manual app_install test calls demo automation."""
        mock_demo.return_value = True

        result = run_manual_test(
            category     = "app_install",
            machine_name = "PC-TEST-001",
            app_name     = "zoom",
            email        = "test@icici.com",
        )
        self.assertTrue(result)
        mock_demo.assert_called_once()

    @patch("automation.runner._run_demo_automation")
    def test_antivirus_manual_test(self, mock_demo):
        """Manual antivirus test calls demo automation."""
        mock_demo.return_value = True

        result = run_manual_test(
            category     = "antivirus",
            machine_name = "PC-TEST-002",
        )
        self.assertTrue(result)

    def test_hardware_manual_returns_false(self):
        """Hardware manual test returns False — no script."""
        result = run_manual_test(
            category     = "hardware",
            machine_name = "PC-TEST-003",
        )
        self.assertFalse(result)

    def test_unknown_machine_returns_false(self):
        """UNKNOWN machine returns False in manual test."""
        result = run_manual_test(
            category     = "app_install",
            machine_name = "UNKNOWN",
            app_name     = "zoom",
        )
        self.assertFalse(result)


class TestScriptFilesExist(unittest.TestCase):
    """Tests that PowerShell scripts exist on disk."""

    def test_scripts_directory_exists(self):
        """automation/scripts/ directory must exist."""
        self.assertTrue(
            os.path.isdir(SCRIPTS_DIR),
            f"Scripts directory missing: {SCRIPTS_DIR}"
        )

    def test_all_mapped_scripts_are_ps1(self):
        """All scripts in AUTOMATION_MAP must end in .ps1."""
        for cat, script in AUTOMATION_MAP.items():
            if script is not None:
                self.assertTrue(
                    script.endswith(".ps1"),
                    f"Script for '{cat}' must end in .ps1"
                )

    def test_expected_scripts_exist_on_disk(self):
        """Each mapped script must exist on disk."""
        missing = []
        for cat, script_name in AUTOMATION_MAP.items():
            if script_name is None:
                continue
            path = os.path.join(SCRIPTS_DIR, script_name)
            if not os.path.exists(path):
                missing.append(f"{cat} → {script_name}")

        if missing:
            self.fail(
                f"Missing script files:\n  "
                + "\n  ".join(missing)
                + "\nCreate these in automation/scripts/"
            )

    def test_existing_scripts_not_empty(self):
        """Scripts that exist on disk must not be empty."""
        for cat, script_name in AUTOMATION_MAP.items():
            if script_name is None:
                continue
            path = os.path.join(SCRIPTS_DIR, script_name)
            if os.path.exists(path):
                size = os.path.getsize(path)
                self.assertGreater(
                    size, 0,
                    f"Script file is empty: {script_name}"
                )


class TestEdgeCases(unittest.TestCase):
    """Edge case and boundary condition tests."""

    @patch("automation.runner._run_demo_automation")
    def test_multiple_apps_picks_zoom_first(self, mock_demo):
        """Zoom beats Chrome and 7zip in priority selection."""
        mock_demo.return_value = True

        ticket = _make_ticket(
            machine_name = "PC-0001",
            apps         = ["chrome", "zoom", "7zip"],
        )
        classification = _make_classification(
            category="app_install"
        )

        run_automation(ticket, classification)

        params = mock_demo.call_args[1]["params"]
        self.assertEqual(params["AppName"], "zoom")

    @patch("automation.runner._run_demo_automation")
    def test_ticket_id_in_params(self, mock_demo):
        """Ticket ID must always be in script params."""
        mock_demo.return_value = True

        ticket = _make_ticket(ticket_id=9876)
        classification = _make_classification(
            category="antivirus"
        )

        run_automation(ticket, classification)

        params = mock_demo.call_args[1]["params"]
        self.assertEqual(params["TicketId"], "9876")

    @patch("automation.runner._run_demo_automation")
    def test_hyphenated_machine_name_passed_correctly(
        self, mock_demo
    ):
        """Machine names with hyphens work correctly."""
        mock_demo.return_value = True

        ticket = _make_ticket(
            machine_name = "PC-ICICI-DESK-0042",
            apps         = ["zoom"],
        )
        classification = _make_classification(
            category="app_install"
        )

        run_automation(ticket, classification)

        params = mock_demo.call_args[1]["params"]
        self.assertEqual(
            params["MachineName"], "PC-ICICI-DESK-0042"
        )

    def test_demo_mode_flag_is_true(self):
        """DEMO_MODE must be True in test environment."""
        self.assertTrue(DEMO_MODE)

    def test_dry_run_mode_flag_is_false(self):
        """DRY_RUN_MODE must be False in test environment."""
        self.assertFalse(DRY_RUN_MODE)


def run_all_tests() -> bool:
    """
    Run the complete test suite and print a formatted summary.
    Called when running this file directly.

    Returns:
        True if all tests passed, False otherwise
    """
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestRunAutomation,
        TestRunDemoAutomation,
        TestBuildScriptParams,
        TestExecutePowershell,
        TestPickAppName,
        TestExtractUsername,
        TestAutomationMap,
        TestMockAutomationData,
        TestSupportedCategories,
        TestRunManualTest,
        TestScriptFilesExist,
        TestEdgeCases,
    ]

    for cls in test_classes:
        suite.addTests(
            loader.loadTestsFromTestCase(cls)
        )

    runner = unittest.TextTestRunner(
        verbosity = 2,
        stream    = sys.stdout,
    )

    print("\n" + "=" * 65)
    print("AUTOMATION TEST SUITE")
    print("=" * 65)
    print(
        f"  Mode     : "
        f"{'DEMO' if DEMO_MODE else 'LIVE'}"
    )
    print(
        f"  Dry run  : "
        f"{'YES' if DRY_RUN_MODE else 'NO'}"
    )
    print(
        f"  Supported categories   : "
        f"{len(get_supported_categories())}"
    )
    print(
        f"  Unsupported categories : "
        f"{len(get_unsupported_categories())}"
    )
    print()

    result = runner.run(suite)

    print("\n" + "=" * 65)
    print("TEST SUMMARY")
    print("=" * 65)
    passed = (
        result.testsRun
        - len(result.failures)
        - len(result.errors)
    )
    print(f"  Tests run  : {result.testsRun}")
    print(f"  Passed     : {passed}")
    print(f"  Failures   : {len(result.failures)}")
    print(f"  Errors     : {len(result.errors)}")
    print(f"  Skipped    : {len(result.skipped)}")
    print(
        f"  Overall    : "
        f"{'PASSED ✓' if result.wasSuccessful() else 'FAILED ✗'}"
    )
    print("=" * 65 + "\n")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)