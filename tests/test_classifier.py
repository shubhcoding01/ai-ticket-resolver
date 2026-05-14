# import os
# import sys
# import json
# import unittest
# from unittest.mock import patch, MagicMock, call

# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from classifier.ai_classifier import (
#     classify_ticket,
#     _parse_response,
#     _validate_result,
#     _fallback_classification,
#     _get_suggested_action,
#     batch_classify,
# )
# from classifier.category_rules import (
#     classify_by_rules,
#     _score_categories,
#     _detect_priority,
#     _detect_urgency_boost,
#     _check_escalation_triggers,
#     _normalize_text,
#     _is_after_business_hours,
#     validate_ai_result,
#     get_all_categories,
#     get_auto_resolvable_categories,
#     get_category_keywords,
# )
# from classifier.prompts import (
#     get_system_prompt,
#     build_classification_prompt,
#     build_batch_classification_prompt,
#     build_sentiment_prompt,
#     build_summary_prompt,
#     build_quality_check_prompt,
#     build_reclassification_prompt,
#     build_ambiguous_ticket_prompt,
#     get_valid_categories,
#     get_valid_priorities,
#     get_valid_confidences,
#     get_category_description,
#     get_estimated_resolution_time,
# )


# VALID_CATEGORIES = [
#     "app_install",
#     "antivirus",
#     "password_reset",
#     "network",
#     "printer",
#     "email_issue",
#     "hardware",
#     "os_issue",
#     "access_permission",
#     "other",
# ]

# VALID_PRIORITIES   = ["low", "medium", "high", "urgent"]
# VALID_CONFIDENCES  = ["low", "medium", "high"]


# def make_valid_classification(
#     category         = "app_install",
#     priority         = "high",
#     can_auto_resolve = True,
#     suggested_action = "Install the application remotely.",
#     confidence       = "high",
# ):
#     """Helper — build a valid classification dict."""
#     return {
#         "category"        : category,
#         "priority"        : priority,
#         "can_auto_resolve": can_auto_resolve,
#         "suggested_action": suggested_action,
#         "confidence"      : confidence,
#     }


# class TestClassifyTicket(unittest.TestCase):
#     """
#     Tests for the main classify_ticket() function.
#     Mocks the Anthropic client so no real API calls are made.
#     """

#     def _mock_claude_response(self, payload: dict):
#         """
#         Build a fake Anthropic API response object
#         containing the given payload as JSON text.
#         """
#         mock_content      = MagicMock()
#         mock_content.text = json.dumps(payload)

#         mock_response         = MagicMock()
#         mock_response.content = [mock_content]
#         return mock_response

#     @patch("classifier.ai_classifier.client")
#     def test_app_install_classified_correctly(self, mock_client):
#         """Zoom install ticket should be classified as app_install."""
#         payload = make_valid_classification(
#             category         = "app_install",
#             priority         = "high",
#             can_auto_resolve = True,
#         )
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(
#             subject     = "Please install Zoom on my laptop",
#             description = (
#                 "I need Zoom installed on PC-ICICI-0042. "
#                 "I have a client call in 2 hours."
#             ),
#         )

#         self.assertEqual(result["category"],         "app_install")
#         self.assertEqual(result["priority"],         "high")
#         self.assertTrue(result["can_auto_resolve"])
#         self.assertIn("suggested_action",            result)
#         self.assertIn("confidence",                  result)

#     @patch("classifier.ai_classifier.client")
#     def test_antivirus_classified_correctly(self, mock_client):
#         """Antivirus update ticket should be classified as antivirus."""
#         payload = make_valid_classification(
#             category         = "antivirus",
#             priority         = "medium",
#             can_auto_resolve = True,
#         )
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(
#             subject     = "Antivirus showing red warning",
#             description = "Symantec definitions are out of date.",
#         )

#         self.assertEqual(result["category"], "antivirus")
#         self.assertTrue(result["can_auto_resolve"])

#     @patch("classifier.ai_classifier.client")
#     def test_password_reset_classified_correctly(self, mock_client):
#         """Password reset ticket classified correctly."""
#         payload = make_valid_classification(
#             category         = "password_reset",
#             priority         = "high",
#             can_auto_resolve = True,
#         )
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(
#             subject     = "Forgot my password — account locked",
#             description = (
#                 "I cannot log in. My account is locked "
#                 "after 5 wrong attempts."
#             ),
#         )

#         self.assertEqual(result["category"],  "password_reset")
#         self.assertEqual(result["priority"],  "high")

#     @patch("classifier.ai_classifier.client")
#     def test_hardware_cannot_auto_resolve(self, mock_client):
#         """Hardware tickets should never be auto-resolvable."""
#         payload = make_valid_classification(
#             category         = "hardware",
#             priority         = "high",
#             can_auto_resolve = False,
#         )
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(
#             subject     = "Laptop screen is flickering",
#             description = "My screen has physical damage.",
#         )

#         self.assertEqual(result["category"],      "hardware")
#         self.assertFalse(result["can_auto_resolve"])

#     @patch("classifier.ai_classifier.client")
#     def test_network_cannot_auto_resolve(self, mock_client):
#         """Network tickets should not be auto-resolvable."""
#         payload = make_valid_classification(
#             category         = "network",
#             priority         = "high",
#             can_auto_resolve = False,
#         )
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(
#             subject     = "Cannot connect to VPN",
#             description = "Cisco AnyConnect times out.",
#         )

#         self.assertEqual(result["category"], "network")
#         self.assertFalse(result["can_auto_resolve"])

#     @patch("classifier.ai_classifier.client")
#     def test_result_has_all_required_keys(self, mock_client):
#         """Result dict must always have all required keys."""
#         payload = make_valid_classification()
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(
#             subject     = "Need help",
#             description = "Something is wrong with my computer.",
#         )

#         required_keys = [
#             "category",
#             "priority",
#             "can_auto_resolve",
#             "suggested_action",
#             "confidence",
#         ]
#         for key in required_keys:
#             self.assertIn(
#                 key, result,
#                 f"Missing key '{key}' in result"
#             )

#     @patch("classifier.ai_classifier.client")
#     def test_api_failure_uses_fallback(self, mock_client):
#         """
#         When the API raises an exception, fallback
#         classifier should be used and still return a
#         valid result dict.
#         """
#         mock_client.messages.create.side_effect = (
#             Exception("API connection error")
#         )

#         result = classify_ticket(
#             subject     = "Install Zoom please",
#             description = "Need Zoom installed on my laptop.",
#         )

#         self.assertIn("category",         result)
#         self.assertIn("priority",         result)
#         self.assertIn("can_auto_resolve", result)
#         self.assertIn("suggested_action", result)
#         self.assertIn(result["category"], VALID_CATEGORIES)
#         self.assertIn(result["priority"], VALID_PRIORITIES)

#     @patch("classifier.ai_classifier.client")
#     def test_empty_subject_handled(self, mock_client):
#         """Empty subject should not crash the classifier."""
#         payload = make_valid_classification(category="other")
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         result = classify_ticket(subject="", description="Some issue.")

#         self.assertIn("category", result)
#         self.assertIn(result["category"], VALID_CATEGORIES)

#     @patch("classifier.ai_classifier.client")
#     def test_very_long_description_handled(self, mock_client):
#         """Very long descriptions should not crash."""
#         payload = make_valid_classification()
#         mock_client.messages.create.return_value = (
#             self._mock_claude_response(payload)
#         )

#         long_desc = "My computer is slow. " * 500

#         result = classify_ticket(
#             subject     = "Performance issue",
#             description = long_desc,
#         )

#         self.assertIn("category", result)


# class TestParseResponse(unittest.TestCase):
#     """
#     Tests for _parse_response().
#     Covers clean JSON, JSON with markdown, and invalid responses.
#     """

#     def test_clean_json_parsed(self):
#         """Clean JSON string should parse correctly."""
#         payload = json.dumps(make_valid_classification())
#         result  = _parse_response(payload)
#         self.assertEqual(result["category"], "app_install")

#     def test_json_with_markdown_backticks_parsed(self):
#         """JSON wrapped in markdown code block should be extracted."""
#         payload = (
#             "```json\n"
#             + json.dumps(make_valid_classification())
#             + "\n```"
#         )
#         result = _parse_response(payload)
#         self.assertEqual(result["category"], "app_install")

#     def test_json_with_preamble_text_parsed(self):
#         """
#         JSON response with extra text before it
#         should still be parsed correctly.
#         """
#         payload = (
#             "Here is my classification:\n"
#             + json.dumps(make_valid_classification())
#             + "\nThank you."
#         )
#         result = _parse_response(payload)
#         self.assertEqual(result["category"], "app_install")

#     def test_invalid_json_raises_value_error(self):
#         """Completely invalid response should raise ValueError."""
#         with self.assertRaises(ValueError):
#             _parse_response("This is not JSON at all.")

#     def test_empty_string_raises_value_error(self):
#         """Empty string response should raise ValueError."""
#         with self.assertRaises(ValueError):
#             _parse_response("")

#     def test_nested_json_parsed(self):
#         """JSON response with extra nested fields should parse."""
#         data = {
#             **make_valid_classification(),
#             "extra_field": "ignored",
#             "nested"     : {"key": "value"},
#         }
#         result = _parse_response(json.dumps(data))
#         self.assertEqual(result["category"], "app_install")

#     def test_json_with_trailing_newlines_parsed(self):
#         """JSON with trailing newlines should parse cleanly."""
#         payload = json.dumps(make_valid_classification()) + "\n\n"
#         result  = _parse_response(payload)
#         self.assertIn("category", result)


# class TestValidateResult(unittest.TestCase):
#     """
#     Tests for _validate_result().
#     Verifies invalid or missing fields get safe defaults.
#     """

#     def test_valid_result_unchanged(self):
#         """A fully valid result should pass through unchanged."""
#         result   = make_valid_classification()
#         validated = _validate_result(result.copy())
#         self.assertEqual(validated["category"],   result["category"])
#         self.assertEqual(validated["priority"],   result["priority"])

#     def test_invalid_category_replaced_with_other(self):
#         """Invalid category value should be replaced with 'other'."""
#         result             = make_valid_classification()
#         result["category"] = "totally_invalid_cat"
#         validated          = _validate_result(result)
#         self.assertEqual(validated["category"], "other")

#     def test_invalid_priority_replaced_with_medium(self):
#         """Invalid priority value should be replaced with 'medium'."""
#         result             = make_valid_classification()
#         result["priority"] = "super_urgent_please"
#         validated          = _validate_result(result)
#         self.assertEqual(validated["priority"], "medium")

#     def test_string_true_for_can_auto_resolve_corrected(self):
#         """
#         String 'true' for can_auto_resolve should be corrected
#         to boolean False (since it is not a bool).
#         """
#         result                     = make_valid_classification()
#         result["can_auto_resolve"] = "true"
#         validated                  = _validate_result(result)
#         self.assertIsInstance(validated["can_auto_resolve"], bool)

#     def test_missing_suggested_action_gets_default(self):
#         """Missing suggested_action gets a default value."""
#         result = make_valid_classification()
#         del result["suggested_action"]
#         validated = _validate_result(result)
#         self.assertIn("suggested_action", validated)
#         self.assertGreater(len(validated["suggested_action"]), 0)

#     def test_missing_confidence_gets_default(self):
#         """Missing confidence field gets 'medium' default."""
#         result = make_valid_classification()
#         del result["confidence"]
#         validated = _validate_result(result)
#         self.assertIn("confidence", validated)
#         self.assertIn(validated["confidence"], VALID_CONFIDENCES)

#     def test_invalid_confidence_replaced(self):
#         """Invalid confidence value replaced with 'medium'."""
#         result               = make_valid_classification()
#         result["confidence"] = "very_high_confidence"
#         validated            = _validate_result(result)
#         self.assertIn(validated["confidence"], VALID_CONFIDENCES)

#     def test_all_valid_categories_accepted(self):
#         """All 10 valid categories should pass validation."""
#         for cat in VALID_CATEGORIES:
#             result             = make_valid_classification()
#             result["category"] = cat
#             validated          = _validate_result(result)
#             self.assertEqual(
#                 validated["category"],
#                 cat,
#                 f"Category '{cat}' was incorrectly replaced."
#             )

#     def test_all_valid_priorities_accepted(self):
#         """All 4 valid priorities should pass validation."""
#         for pri in VALID_PRIORITIES:
#             result             = make_valid_classification()
#             result["priority"] = pri
#             validated          = _validate_result(result)
#             self.assertEqual(
#                 validated["priority"],
#                 pri,
#                 f"Priority '{pri}' was incorrectly replaced."
#             )


# class TestFallbackClassification(unittest.TestCase):
#     """
#     Tests for _fallback_classification().
#     Verifies keyword-based fallback works for all categories.
#     """

#     def test_zoom_install_detected(self):
#         """'install zoom' should classify as app_install."""
#         result = _fallback_classification(
#             subject     = "Please install Zoom",
#             description = "I need Zoom on my laptop."
#         )
#         self.assertEqual(result["category"], "app_install")
#         self.assertTrue(result["can_auto_resolve"])

#     def test_antivirus_detected(self):
#         """Antivirus keywords should classify as antivirus."""
#         result = _fallback_classification(
#             subject     = "Antivirus not updating",
#             description = "Symantec virus definitions are outdated."
#         )
#         self.assertEqual(result["category"], "antivirus")

#     def test_password_detected(self):
#         """Password keywords should classify as password_reset."""
#         result = _fallback_classification(
#             subject     = "Forgot my password",
#             description = "Account is locked. Cannot log in."
#         )
#         self.assertEqual(result["category"], "password_reset")

#     def test_urgent_keyword_sets_high_priority(self):
#         """
#         Urgent keyword in ticket should set priority to high.
#         """
#         result = _fallback_classification(
#             subject     = "URGENT — Cannot work",
#             description = "Please fix immediately."
#         )
#         self.assertIn(result["priority"], ["high", "urgent"])

#     def test_unmatched_ticket_defaults_to_other(self):
#         """Ticket with no matching keywords defaults to 'other'."""
#         result = _fallback_classification(
#             subject     = "Random gibberish xyz",
#             description = "Something something something."
#         )
#         self.assertEqual(result["category"],         "other")
#         self.assertFalse(result["can_auto_resolve"])

#     def test_confidence_is_low_for_fallback(self):
#         """
#         Fallback classifier always returns 'low' confidence
#         since it is less reliable than the AI.
#         """
#         result = _fallback_classification(
#             subject     = "Install Zoom",
#             description = "Need Zoom installed."
#         )
#         self.assertEqual(result["confidence"], "low")

#     def test_result_has_all_required_keys(self):
#         """Fallback result must have all required keys."""
#         result = _fallback_classification(
#             subject     = "Any subject",
#             description = "Any description"
#         )
#         for key in ["category", "priority", "can_auto_resolve",
#                     "suggested_action", "confidence"]:
#             self.assertIn(key, result)


# class TestBatchClassify(unittest.TestCase):
#     """
#     Tests for batch_classify().
#     Verifies multiple tickets are classified in order.
#     """

#     @patch("classifier.ai_classifier.classify_ticket")
#     def test_batch_returns_correct_count(self, mock_classify):
#         """Batch classify should return one result per ticket."""
#         mock_classify.return_value = make_valid_classification()

#         tickets = [
#             {"id": 1, "subject": "Install Zoom",  "description": "Need Zoom."},
#             {"id": 2, "subject": "AV not working", "description": "AV error."},
#             {"id": 3, "subject": "Forgot password","description": "Locked out."},
#         ]

#         results = batch_classify(tickets)

#         self.assertEqual(len(results), 3)
#         self.assertEqual(mock_classify.call_count, 3)

#     @patch("classifier.ai_classifier.classify_ticket")
#     def test_batch_preserves_ticket_data(self, mock_classify):
#         """Batch results should include original ticket fields."""
#         mock_classify.return_value = make_valid_classification()

#         tickets = [
#             {
#                 "id"         : 9001,
#                 "subject"    : "Test ticket",
#                 "description": "Test description",
#             }
#         ]

#         results = batch_classify(tickets)

#         self.assertEqual(results[0]["id"],      9001)
#         self.assertEqual(results[0]["subject"], "Test ticket")
#         self.assertIn("classification",         results[0])

#     @patch("classifier.ai_classifier.classify_ticket")
#     def test_empty_batch_returns_empty_list(self, mock_classify):
#         """Empty ticket list should return empty results list."""
#         results = batch_classify([])
#         self.assertEqual(results, [])
#         mock_classify.assert_not_called()

#     @patch("classifier.ai_classifier.classify_ticket")
#     def test_batch_order_preserved(self, mock_classify):
#         """Results must be in same order as input tickets."""
#         categories = ["app_install", "antivirus", "hardware"]
#         mock_classify.side_effect = [
#             make_valid_classification(category=c)
#             for c in categories
#         ]

#         tickets = [
#             {"id": i+1, "subject": f"Ticket {i+1}", "description": "Desc"}
#             for i in range(3)
#         ]

#         results = batch_classify(tickets)

#         for i, cat in enumerate(categories):
#             self.assertEqual(
#                 results[i]["classification"]["category"],
#                 cat
#             )


# class TestCategoryRules(unittest.TestCase):
#     """
#     Tests for classify_by_rules() and supporting functions.
#     Verifies keyword scoring, priority detection, and
#     escalation trigger detection.
#     """

#     def test_zoom_install_classified(self):
#         """Zoom install ticket classified as app_install by rules."""
#         result = classify_by_rules(
#             subject     = "Please install Zoom on my laptop",
#             description = "I need Zoom installed on PC-ICICI-0042.",
#         )
#         self.assertEqual(result["category"], "app_install")
#         self.assertEqual(result["classified_by"], "rules")

#     def test_antivirus_classified(self):
#         """Antivirus keywords classified correctly."""
#         result = classify_by_rules(
#             subject     = "Antivirus not updating",
#             description = "Symantec definitions out of date.",
#         )
#         self.assertEqual(result["category"], "antivirus")

#     def test_password_reset_classified(self):
#         """Password keywords classified as password_reset."""
#         result = classify_by_rules(
#             subject     = "Forgot password account locked",
#             description = "Cannot log in. Account locked after 5 attempts.",
#         )
#         self.assertEqual(result["category"], "password_reset")

#     def test_hardware_cannot_auto_resolve(self):
#         """Hardware issues must not be auto-resolvable."""
#         result = classify_by_rules(
#             subject     = "Laptop screen flickering",
#             description = "My laptop screen is broken.",
#         )
#         self.assertEqual(result["category"],      "hardware")
#         self.assertFalse(result["can_auto_resolve"])

#     def test_empty_input_returns_default(self):
#         """Empty subject and description return safe defaults."""
#         result = classify_by_rules(subject="", description="")
#         self.assertEqual(result["category"],         "other")
#         self.assertFalse(result["can_auto_resolve"])
#         self.assertEqual(result["classified_by"],    "rules")

#     def test_result_has_all_required_keys(self):
#         """Rule result must have all required keys."""
#         result = classify_by_rules(
#             subject     = "Any subject",
#             description = "Any description",
#         )
#         required = [
#             "category", "priority", "can_auto_resolve",
#             "suggested_action", "confidence", "scores",
#             "force_escalate", "after_hours", "classified_by",
#         ]
#         for key in required:
#             self.assertIn(key, result)

#     def test_scores_dict_contains_all_categories(self):
#         """Scores dict must contain an entry for every category."""
#         result = classify_by_rules(
#             subject     = "Install Teams",
#             description = "Need Microsoft Teams installed.",
#         )
#         for cat in VALID_CATEGORIES[:-1]:
#             self.assertIn(
#                 cat,
#                 result["scores"],
#                 f"Category '{cat}' missing from scores"
#             )

#     def test_printer_classified(self):
#         """Printer keywords classified as printer."""
#         result = classify_by_rules(
#             subject     = "Printer offline cannot print",
#             description = "Print queue is stuck. Printer shows offline.",
#         )
#         self.assertEqual(result["category"], "printer")

#     def test_email_issue_classified(self):
#         """Outlook keywords classified as email_issue."""
#         result = classify_by_rules(
#             subject     = "Outlook not opening",
#             description = "Outlook crashes immediately. PST file error.",
#         )
#         self.assertEqual(result["category"], "email_issue")

#     def test_network_classified(self):
#         """VPN/network keywords classified as network."""
#         result = classify_by_rules(
#             subject     = "Cannot connect to VPN",
#             description = "Cisco AnyConnect connection timed out.",
#         )
#         self.assertEqual(result["category"], "network")


# class TestScoreCategories(unittest.TestCase):
#     """
#     Tests for _score_categories().
#     Verifies keyword and phrase scoring works correctly.
#     """

#     def test_zoom_scores_highest_for_app_install(self):
#         """
#         Text containing 'zoom' and 'install' should give
#         app_install the highest score.
#         """
#         text   = "please install zoom on my laptop"
#         scores = _score_categories(text)
#         self.assertGreater(
#             scores["app_install"],
#             scores["antivirus"]
#         )

#     def test_antivirus_scores_highest_for_av_text(self):
#         """
#         Text about antivirus definitions should give
#         antivirus the highest score.
#         """
#         text   = "antivirus virus definitions out of date scan failed"
#         scores = _score_categories(text)
#         self.assertGreater(
#             scores["antivirus"],
#             scores["app_install"]
#         )

#     def test_password_scores_highest_for_pw_text(self):
#         """
#         Password and locked keywords should give
#         password_reset the highest score.
#         """
#         text   = "forgot password account locked cannot login expired"
#         scores = _score_categories(text)
#         self.assertGreater(
#             scores["password_reset"],
#             scores["hardware"]
#         )

#     def test_scores_dict_has_all_categories(self):
#         """Scores dict must have entries for all categories."""
#         scores = _score_categories("random text here")
#         for cat in VALID_CATEGORIES[:-1]:
#             self.assertIn(cat, scores)

#     def test_empty_text_gives_zero_scores(self):
#         """Empty text should give zero scores for all categories."""
#         scores = _score_categories("")
#         for score in scores.values():
#             self.assertEqual(score, 0.0)

#     def test_phrase_match_scores_higher_than_keyword(self):
#         """
#         A phrase match should score higher than
#         individual keyword matches.
#         """
#         keyword_text = "printer"
#         phrase_text  = "printer not working"

#         kw_scores  = _score_categories(keyword_text)
#         ph_scores  = _score_categories(phrase_text)

#         self.assertGreaterEqual(
#             ph_scores["printer"],
#             kw_scores["printer"]
#         )


# class TestDetectPriority(unittest.TestCase):
#     """Tests for _detect_priority()."""

#     def test_urgent_keyword_gives_urgent(self):
#         """'critical' keyword should give urgent priority."""
#         result = _detect_priority("this is critical emergency production down")
#         self.assertEqual(result, "urgent")

#     def test_asap_gives_high(self):
#         """'urgent' keyword should give high priority."""
#         result = _detect_priority("i need help urgent asap cannot work")
#         self.assertIn(result, ["high", "urgent"])

#     def test_low_priority_keywords(self):
#         """'not urgent' keywords should give low priority."""
#         result = _detect_priority(
#             "when possible not urgent minor issue no rush"
#         )
#         self.assertEqual(result, "low")

#     def test_no_keywords_defaults_to_medium(self):
#         """Text with no priority keywords defaults to medium."""
#         result = _detect_priority("my computer has an issue")
#         self.assertEqual(result, "medium")

#     def test_empty_text_defaults_to_medium(self):
#         """Empty text defaults to medium priority."""
#         result = _detect_priority("")
#         self.assertEqual(result, "medium")


# class TestDetectUrgencyBoost(unittest.TestCase):
#     """Tests for _detect_urgency_boost()."""

#     def test_meeting_in_hours_triggers_boost(self):
#         """'meeting in 2 hours' should trigger urgency boost."""
#         result = _detect_urgency_boost(
#             "i have a meeting in 2 hours and cannot connect"
#         )
#         self.assertTrue(result)

#     def test_deadline_today_triggers_boost(self):
#         """'deadline today' should trigger urgency boost."""
#         result = _detect_urgency_boost(
#             "i have a deadline today please help"
#         )
#         self.assertTrue(result)

#     def test_client_call_triggers_boost(self):
#         """'client call in' should trigger urgency boost."""
#         result = _detect_urgency_boost(
#             "client call in 1 hour and vpn not working"
#         )
#         self.assertTrue(result)

#     def test_normal_text_no_boost(self):
#         """Normal text should not trigger urgency boost."""
#         result = _detect_urgency_boost(
#             "my computer is a bit slow sometimes"
#         )
#         self.assertFalse(result)

#     def test_empty_text_no_boost(self):
#         """Empty text should not trigger urgency boost."""
#         result = _detect_urgency_boost("")
#         self.assertFalse(result)


# class TestEscalationTriggers(unittest.TestCase):
#     """Tests for _check_escalation_triggers()."""

#     def test_ransomware_triggers_escalation(self):
#         """'ransomware' must trigger force escalation."""
#         result = _check_escalation_triggers(
#             "my files are being encrypted ransomware"
#         )
#         self.assertTrue(result)

#     def test_data_breach_triggers_escalation(self):
#         """'data breach' must trigger force escalation."""
#         result = _check_escalation_triggers(
#             "i think there is a data breach"
#         )
#         self.assertTrue(result)

#     def test_hacked_triggers_escalation(self):
#         """'hacked' must trigger force escalation."""
#         result = _check_escalation_triggers(
#             "i think my computer has been hacked"
#         )
#         self.assertTrue(result)

#     def test_normal_text_no_escalation(self):
#         """Normal IT support text should not trigger escalation."""
#         result = _check_escalation_triggers(
#             "please install zoom on my laptop"
#         )
#         self.assertFalse(result)

#     def test_ceo_triggers_escalation(self):
#         """CEO-related tickets should trigger escalation."""
#         result = _check_escalation_triggers(
#             "this is the ceo laptop issue needs immediate fix"
#         )
#         self.assertTrue(result)

#     def test_escalation_sets_auto_resolve_false(self):
#         """
#         When an escalation trigger is detected,
#         can_auto_resolve must be False in the full result.
#         """
#         result = classify_by_rules(
#             subject     = "Ransomware on my computer",
#             description = (
#                 "Files are encrypted. I see a ransom note. "
#                 "This looks like ransomware. Emergency."
#             ),
#         )
#         self.assertTrue(result["force_escalate"])
#         self.assertFalse(result["can_auto_resolve"])


# class TestNormalizeText(unittest.TestCase):
#     """Tests for _normalize_text()."""

#     def test_text_lowercased(self):
#         """Output should always be lowercase."""
#         result = _normalize_text("INSTALL ZOOM ON MY LAPTOP")
#         self.assertEqual(result, result.lower())

#     def test_extra_whitespace_removed(self):
#         """Multiple spaces and tabs should be normalized."""
#         result = _normalize_text("install   zoom   on   my    laptop")
#         self.assertNotIn("  ", result)

#     def test_contractions_expanded(self):
#         """Contractions should be expanded."""
#         result = _normalize_text("can't log in")
#         self.assertIn("cannot", result)

#     def test_empty_string_returns_empty(self):
#         """Empty string input returns empty string."""
#         result = _normalize_text("")
#         self.assertEqual(result, "")

#     def test_special_chars_removed(self):
#         """Special characters should be replaced with spaces."""
#         result = _normalize_text("zoom@#$% is needed!!")
#         self.assertNotIn("@", result)
#         self.assertNotIn("#", result)
#         self.assertNotIn("!!", result)


# class TestValidateAIResult(unittest.TestCase):
#     """
#     Tests for validate_ai_result().
#     Verifies rule-based validation of AI classifications.
#     """

#     def test_matching_categories_keeps_ai_result(self):
#         """
#         When AI and rules agree on category,
#         AI result should be returned unchanged.
#         """
#         ai_result = make_valid_classification(
#             category   = "app_install",
#             confidence = "high",
#         )
#         result = validate_ai_result(
#             ai_result   = ai_result,
#             subject     = "Install Zoom",
#             description = "Need Zoom installed on my laptop urgently.",
#         )
#         self.assertEqual(result["category"], "app_install")

#     def test_escalation_trigger_forces_no_auto_resolve(self):
#         """
#         When rules detect an escalation trigger,
#         can_auto_resolve must be forced to False even if
#         the AI said True.
#         """
#         ai_result = make_valid_classification(
#             category         = "app_install",
#             can_auto_resolve = True,
#         )
#         result = validate_ai_result(
#             ai_result   = ai_result,
#             subject     = "Ransomware detected",
#             description = "All my files are encrypted. Ransomware attack.",
#         )
#         self.assertFalse(result["can_auto_resolve"])

#     def test_after_hours_flag_propagated(self):
#         """After-hours flag from rules should appear in result."""
#         ai_result = make_valid_classification()
#         result    = validate_ai_result(
#             ai_result   = ai_result,
#             subject     = "Install Zoom",
#             description = "Need Zoom installed.",
#         )
#         self.assertIn("after_hours", result)


# class TestGetSuggestedAction(unittest.TestCase):
#     """Tests for _get_suggested_action()."""

#     def test_app_install_action_contains_install(self):
#         """App install suggested action should mention install."""
#         action = _get_suggested_action("app_install")
#         self.assertIsInstance(action, str)
#         self.assertGreater(len(action), 10)

#     def test_all_categories_return_string(self):
#         """All categories should return a non-empty string."""
#         for cat in VALID_CATEGORIES:
#             action = _get_suggested_action(cat)
#             self.assertIsInstance(action, str)
#             self.assertGreater(
#                 len(action), 5,
#                 f"Action too short for category '{cat}'"
#             )

#     def test_unknown_category_returns_default(self):
#         """Unknown category should return a default action string."""
#         action = _get_suggested_action("completely_unknown")
#         self.assertIsInstance(action, str)
#         self.assertGreater(len(action), 5)


# class TestGetAllCategories(unittest.TestCase):
#     """Tests for get_all_categories()."""

#     def test_returns_list(self):
#         """Should return a list."""
#         self.assertIsInstance(get_all_categories(), list)

#     def test_contains_all_expected_categories(self):
#         """Should contain all 10 category names."""
#         cats = get_all_categories()
#         for cat in VALID_CATEGORIES:
#             self.assertIn(cat, cats)

#     def test_contains_other(self):
#         """'other' must always be in the categories list."""
#         self.assertIn("other", get_all_categories())


# class TestGetAutoResolvableCategories(unittest.TestCase):
#     """Tests for get_auto_resolvable_categories()."""

#     def test_returns_list(self):
#         """Should return a list."""
#         self.assertIsInstance(get_auto_resolvable_categories(), list)

#     def test_app_install_is_auto_resolvable(self):
#         """app_install must be in auto-resolvable list."""
#         self.assertIn("app_install", get_auto_resolvable_categories())

#     def test_hardware_not_auto_resolvable(self):
#         """hardware must NOT be in auto-resolvable list."""
#         self.assertNotIn("hardware", get_auto_resolvable_categories())

#     def test_access_permission_not_auto_resolvable(self):
#         """access_permission must NOT be in auto-resolvable list."""
#         self.assertNotIn(
#             "access_permission",
#             get_auto_resolvable_categories()
#         )

#     def test_password_reset_is_auto_resolvable(self):
#         """password_reset must be in auto-resolvable list."""
#         self.assertIn("password_reset", get_auto_resolvable_categories())


# class TestGetCategoryKeywords(unittest.TestCase):
#     """Tests for get_category_keywords()."""

#     def test_returns_dict_with_keywords_and_phrases(self):
#         """Should return dict with 'keywords' and 'phrases' keys."""
#         result = get_category_keywords("app_install")
#         self.assertIn("keywords", result)
#         self.assertIn("phrases",  result)

#     def test_keywords_is_list(self):
#         """'keywords' value should be a list."""
#         result = get_category_keywords("antivirus")
#         self.assertIsInstance(result["keywords"], list)

#     def test_phrases_is_list(self):
#         """'phrases' value should be a list."""
#         result = get_category_keywords("antivirus")
#         self.assertIsInstance(result["phrases"], list)

#     def test_unknown_category_returns_empty(self):
#         """Unknown category returns dict with empty lists."""
#         result = get_category_keywords("totally_unknown")
#         self.assertIn("keywords", result)
#         self.assertIn("phrases",  result)
#         self.assertEqual(result["keywords"], [])
#         self.assertEqual(result["phrases"],  [])

#     def test_all_categories_have_keywords(self):
#         """All known categories should have at least one keyword."""
#         for cat in VALID_CATEGORIES[:-1]:
#             result = get_category_keywords(cat)
#             self.assertGreater(
#                 len(result["keywords"]),
#                 0,
#                 f"No keywords for category '{cat}'"
#             )


# class TestPromptBuilders(unittest.TestCase):
#     """
#     Tests for all prompt builder functions in prompts.py.
#     Verifies prompts are built correctly and contain
#     expected content.
#     """

#     def test_system_prompt_not_empty(self):
#         """System prompt should be a non-empty string."""
#         sp = get_system_prompt()
#         self.assertIsInstance(sp, str)
#         self.assertGreater(len(sp), 100)

#     def test_system_prompt_contains_categories(self):
#         """System prompt should mention all categories."""
#         sp = get_system_prompt()
#         for cat in VALID_CATEGORIES:
#             self.assertIn(
#                 cat, sp,
#                 f"Category '{cat}' not found in system prompt"
#             )

#     def test_classification_prompt_contains_subject(self):
#         """Classification prompt should include ticket subject."""
#         prompt = build_classification_prompt(
#             subject     = "Install Zoom please",
#             description = "Need Zoom on my laptop.",
#         )
#         self.assertIn("Install Zoom please", prompt)

#     def test_classification_prompt_contains_description(self):
#         """Classification prompt should include description."""
#         prompt = build_classification_prompt(
#             subject     = "Some subject",
#             description = "Very specific description text here.",
#         )
#         self.assertIn("Very specific description text here.", prompt)

#     def test_classification_prompt_contains_machine_name(self):
#         """Classification prompt should include machine name."""
#         prompt = build_classification_prompt(
#             subject      = "Issue",
#             description  = "Problem.",
#             machine_name = "PC-ICICI-9999",
#         )
#         self.assertIn("PC-ICICI-9999", prompt)

#     def test_classification_prompt_contains_ticket_id(self):
#         """Classification prompt should include ticket ID."""
#         prompt = build_classification_prompt(
#             subject     = "Issue",
#             description = "Problem.",
#             ticket_id   = 12345,
#         )
#         self.assertIn("12345", prompt)

#     def test_batch_prompt_contains_all_tickets(self):
#         """Batch prompt should include all ticket subjects."""
#         tickets = [
#             {"id": 1, "subject": "Install Zoom",   "description": "Need Zoom."},
#             {"id": 2, "subject": "AV not working", "description": "AV error."},
#         ]
#         prompt = build_batch_classification_prompt(tickets)
#         self.assertIn("Install Zoom",   prompt)
#         self.assertIn("AV not working", prompt)

#     def test_batch_prompt_contains_count(self):
#         """Batch prompt should mention the number of tickets."""
#         tickets = [
#             {"id": i, "subject": f"Ticket {i}", "description": "desc"}
#             for i in range(3)
#         ]
#         prompt = build_batch_classification_prompt(tickets)
#         self.assertIn("3", prompt)

#     def test_sentiment_prompt_contains_subject(self):
#         """Sentiment prompt should include ticket subject."""
#         prompt = build_sentiment_prompt(
#             subject     = "URGENT I cannot work",
#             description = "Please help immediately.",
#         )
#         self.assertIn("URGENT I cannot work", prompt)

#     def test_summary_prompt_contains_category(self):
#         """Summary prompt should include the category."""
#         prompt = build_summary_prompt(
#             subject     = "VPN issue",
#             description = "Cannot connect.",
#             category    = "network",
#             priority    = "high",
#         )
#         self.assertIn("network", prompt)

#     def test_quality_prompt_contains_machine_name(self):
#         """Quality check prompt should include machine name."""
#         prompt = build_quality_check_prompt(
#             subject      = "Issue",
#             description  = "Problem here.",
#             machine_name = "LAPTOP-TEST-001",
#         )
#         self.assertIn("LAPTOP-TEST-001", prompt)

#     def test_reclassification_prompt_contains_previous(self):
#         """Reclass prompt should show previous classification."""
#         prompt = build_reclassification_prompt(
#             subject         = "Issue",
#             description     = "Problem.",
#             prev_category   = "hardware",
#             prev_priority   = "high",
#             prev_auto       = False,
#             prev_confidence = "low",
#             flag_reason     = "Rules classifier disagreed.",
#         )
#         self.assertIn("hardware",                 prompt)
#         self.assertIn("Rules classifier disagreed.", prompt)

#     def test_ambiguous_prompt_built_correctly(self):
#         """Ambiguous prompt should include primary and secondary fields."""
#         prompt = build_ambiguous_ticket_prompt(
#             subject     = "Multiple things broken",
#             description = "VPN down and Outlook also crashing.",
#         )
#         self.assertIn("primary_issue",    prompt)
#         self.assertIn("secondary_issues", prompt)

#     def test_long_description_truncated(self):
#         """
#         Very long descriptions should be truncated in the
#         prompt so tokens are not wasted.
#         """
#         long_desc = "My laptop is slow. " * 500
#         prompt    = build_classification_prompt(
#             subject     = "Slow laptop",
#             description = long_desc,
#         )
#         self.assertIsInstance(prompt, str)
#         self.assertLess(len(prompt), len(long_desc) + 500)


# class TestValidValues(unittest.TestCase):
#     """Tests for the get_valid_* helper functions."""

#     def test_get_valid_categories_returns_list(self):
#         """get_valid_categories should return a list."""
#         cats = get_valid_categories()
#         self.assertIsInstance(cats, list)
#         self.assertGreater(len(cats), 0)

#     def test_get_valid_priorities_returns_list(self):
#         """get_valid_priorities should return a list."""
#         pris = get_valid_priorities()
#         self.assertIsInstance(pris, list)
#         self.assertIn("high",   pris)
#         self.assertIn("medium", pris)
#         self.assertIn("low",    pris)
#         self.assertIn("urgent", pris)

#     def test_get_valid_confidences_returns_list(self):
#         """get_valid_confidences should return a list."""
#         confs = get_valid_confidences()
#         self.assertIsInstance(confs, list)
#         self.assertIn("high",   confs)
#         self.assertIn("medium", confs)
#         self.assertIn("low",    confs)

#     def test_all_categories_match_expected(self):
#         """get_valid_categories matches expected list."""
#         cats = get_valid_categories()
#         for cat in VALID_CATEGORIES:
#             self.assertIn(cat, cats)


# class TestCategoryDescription(unittest.TestCase):
#     """Tests for get_category_description()."""

#     def test_all_categories_return_string(self):
#         """Every category should return a non-empty description."""
#         for cat in VALID_CATEGORIES:
#             desc = get_category_description(cat)
#             self.assertIsInstance(desc, str)
#             self.assertGreater(len(desc), 3)

#     def test_app_install_description(self):
#         """app_install should return a readable label."""
#         desc = get_category_description("app_install")
#         self.assertIn("Software", desc)

#     def test_unknown_category_returns_formatted_string(self):
#         """Unknown category returns formatted fallback string."""
#         desc = get_category_description("some_unknown_cat")
#         self.assertIsInstance(desc, str)
#         self.assertGreater(len(desc), 3)


# class TestEstimatedResolutionTime(unittest.TestCase):
#     """Tests for get_estimated_resolution_time()."""

#     def test_returns_string(self):
#         """Should always return a string."""
#         result = get_estimated_resolution_time("app_install", "high")
#         self.assertIsInstance(result, str)
#         self.assertGreater(len(result), 3)

#     def test_urgent_faster_than_low(self):
#         """
#         Urgent priority should give a shorter time estimate
#         than low priority for the same category.
#         """
#         urgent_time = get_estimated_resolution_time("antivirus", "urgent")
#         low_time    = get_estimated_resolution_time("antivirus", "low")
#         self.assertNotEqual(urgent_time, low_time)

#     def test_hardware_takes_longer(self):
#         """
#         Hardware estimates should reflect longer resolution
#         time than a simple password reset.
#         """
#         hw_time = get_estimated_resolution_time("hardware",       "medium")
#         pw_time = get_estimated_resolution_time("password_reset", "medium")
#         self.assertNotEqual(hw_time, pw_time)

#     def test_all_categories_return_result(self):
#         """All categories and priorities should return a result."""
#         for cat in VALID_CATEGORIES:
#             for pri in VALID_PRIORITIES:
#                 result = get_estimated_resolution_time(cat, pri)
#                 self.assertIsInstance(result, str)
#                 self.assertGreater(len(result), 0)


# def run_all_tests():
#     """Run the complete classifier test suite."""
#     loader = unittest.TestLoader()
#     suite  = unittest.TestSuite()

#     test_classes = [
#         TestClassifyTicket,
#         TestParseResponse,
#         TestValidateResult,
#         TestFallbackClassification,
#         TestBatchClassify,
#         TestCategoryRules,
#         TestScoreCategories,
#         TestDetectPriority,
#         TestDetectUrgencyBoost,
#         TestEscalationTriggers,
#         TestNormalizeText,
#         TestValidateAIResult,
#         TestGetSuggestedAction,
#         TestGetAllCategories,
#         TestGetAutoResolvableCategories,
#         TestGetCategoryKeywords,
#         TestPromptBuilders,
#         TestValidValues,
#         TestCategoryDescription,
#         TestEstimatedResolutionTime,
#     ]

#     for cls in test_classes:
#         suite.addTests(loader.loadTestsFromTestCase(cls))

#     runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)

#     print("\n" + "=" * 65)
#     print("CLASSIFIER TEST SUITE")
#     print("=" * 65 + "\n")

#     result = runner.run(suite)

#     print("\n" + "=" * 65)
#     print("TEST SUMMARY")
#     print("=" * 65)
#     print(f"  Tests run : {result.testsRun}")
#     print(f"  Passed    : {result.testsRun - len(result.failures) - len(result.errors)}")
#     print(f"  Failures  : {len(result.failures)}")
#     print(f"  Errors    : {len(result.errors)}")
#     print(f"  Overall   : {'PASSED' if result.wasSuccessful() else 'FAILED'}")
#     print("=" * 65 + "\n")

#     return result.wasSuccessful()


# if __name__ == "__main__":
#     success = run_all_tests()
#     sys.exit(0 if success else 1)


import os
import re
import logging
from datetime import datetime, timezone
from dotenv   import load_dotenv

load_dotenv("config/.env")

log = logging.getLogger(__name__)

DEMO_MODE       = os.getenv("DEMO_MODE",            "false").strip().lower() == "true"
CHROMA_DIR      = os.getenv("KB_CHROMA_DIR",        "knowledge_base/chroma_db")
COLLECTION_NAME = os.getenv("KB_COLLECTION_NAME",   "it_support_kb")
MAX_RESULTS     = int(os.getenv("KB_MAX_RESULTS",   3))
MIN_SCORE       = float(os.getenv("KB_MIN_SCORE",   0.3))
EMBED_MODEL     = os.getenv("KB_EMBED_MODEL",       "all-MiniLM-L6-v2")

_chroma_client      = None
_collection         = None
_embedding_function = None


def _get_collection():
    """
    Get or initialize the ChromaDB collection.
    Uses module-level singleton so the connection is
    created once and reused across all search calls.
    Lazy initialization — only connects when first
    search is made, not at import time.

    Returns:
        ChromaDB collection object or None if unavailable
    """
    global _chroma_client, _collection, _embedding_function

    if _collection is not None:
        return _collection

    try:
        import chromadb
        from chromadb.utils import embedding_functions

        if not os.path.exists(CHROMA_DIR):
            log.warning(
                f"ChromaDB directory not found: '{CHROMA_DIR}'. "
                "Run kb_indexer.py first to build the index."
            )
            return None

        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_DIR
        )

        _embedding_function = (
            embedding_functions
            .SentenceTransformerEmbeddingFunction(
                model_name=EMBED_MODEL
            )
        )

        try:
            _collection = _chroma_client.get_collection(
                name               = COLLECTION_NAME,
                embedding_function = _embedding_function,
            )
            log.info(
                f"Connected to KB collection "
                f"'{COLLECTION_NAME}' with "
                f"{_collection.count()} chunk(s)."
            )
            return _collection

        except Exception:
            log.warning(
                f"KB collection '{COLLECTION_NAME}' not found. "
                "Run kb_indexer.py first."
            )
            return None

    except ImportError:
        log.error(
            "chromadb not installed. Run:\n"
            "  pip install chromadb sentence-transformers"
        )
        return None

    except Exception as e:
        log.error(f"Failed to connect to ChromaDB: {e}")
        return None


def search_knowledge_base(
    query      : str,
    max_results: int   = None,
    min_score  : float = None,
) -> str | None:
    """
    Main search function called by orchestrator.py
    and demo_runner.py.
    Searches ChromaDB for the most relevant IT support
    guide content matching the query.

    Returns clean formatted text ready to send to the user,
    or None if no relevant content is found above threshold.

    Args:
        query       : Ticket description or search query text
        max_results : Max number of chunks to retrieve
        min_score   : Minimum relevance score 0.0 to 1.0

    Returns:
        Formatted guide string or None
    """
    if not query or not query.strip():
        log.warning(
            "search_knowledge_base called with empty query."
        )
        return None

    max_results = max_results or MAX_RESULTS
    min_score   = min_score   or MIN_SCORE

    log.info(f"KB search query: '{query[:80]}...'")

    cleaned_query = _clean_query(query)
    results       = _vector_search(cleaned_query, max_results)

    if not results:
        log.info("No results from vector search.")
        return None

    filtered = _filter_by_score(results, min_score)

    if not filtered:
        log.info(
            f"No results above minimum score threshold "
            f"({min_score}). Best score was "
            f"{results[0]['score']:.3f}."
        )
        return None

    deduplicated = _deduplicate_results(filtered)
    formatted    = _format_guide(deduplicated, query)

    log.info(
        f"KB search returned {len(deduplicated)} "
        f"relevant chunk(s) for query."
    )

    return formatted


def search_with_details(
    query      : str,
    max_results: int   = None,
    min_score  : float = None,
) -> list:
    """
    Extended search returning full result details including
    scores, source files, and chunk metadata.
    Used by the Streamlit dashboard and debugging.

    Args:
        query       : Search query text
        max_results : Max chunks to retrieve
        min_score   : Minimum relevance score

    Returns:
        List of result dicts with keys:
            text, score, file_name, chunk_index,
            word_count, indexed_at, rank
    """
    if not query or not query.strip():
        return []

    max_results = max_results or MAX_RESULTS
    min_score   = min_score   or MIN_SCORE

    cleaned_query = _clean_query(query)
    results       = _vector_search(
        cleaned_query, max_results * 2
    )

    if not results:
        return []

    filtered     = _filter_by_score(results, min_score)
    deduplicated = _deduplicate_results(filtered)

    for rank, result in enumerate(deduplicated, start=1):
        result["rank"] = rank

    return deduplicated


def search_by_category(category: str) -> str | None:
    """
    Search the knowledge base using a ticket category name.
    Useful as a fallback when the ticket description is short.

    Args:
        category : Ticket category e.g. 'antivirus', 'network'

    Returns:
        Formatted guide text or None if not found
    """
    category_queries = {
        "app_install"       : (
            "how to install software application "
            "on Windows laptop"
        ),
        "antivirus"         : (
            "antivirus not working virus definitions "
            "update scan"
        ),
        "password_reset"    : (
            "forgot password account locked reset "
            "windows login"
        ),
        "network"           : (
            "cannot connect to internet VPN network "
            "not working"
        ),
        "printer"           : (
            "printer offline not printing print queue stuck"
        ),
        "email_issue"       : (
            "outlook not working email not sending "
            "receiving pst"
        ),
        "hardware"          : (
            "laptop hardware issue screen keyboard battery"
        ),
        "os_issue"          : (
            "windows update failed blue screen "
            "system crash slow"
        ),
        "access_permission" : (
            "access denied folder permission shared drive"
        ),
        "other"             : "IT support help troubleshooting",
    }

    query = category_queries.get(category, category)
    log.info(
        f"Category search for '{category}' "
        f"using query: '{query}'"
    )
    return search_knowledge_base(query)


def search_multi_query(queries: list) -> str | None:
    """
    Run multiple search queries and merge the best results.
    Used when a ticket covers multiple issues e.g. both
    VPN and Outlook problems.

    Args:
        queries : List of query strings to search

    Returns:
        Merged formatted guide text or None
    """
    if not queries:
        return None

    all_results = []
    seen_ids    = set()

    for query in queries:
        if not query or not query.strip():
            continue

        cleaned = _clean_query(query)
        results = _vector_search(cleaned, MAX_RESULTS)

        for result in results:
            chunk_id = result.get("id", "")
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                all_results.append(result)

    if not all_results:
        return None

    all_results.sort(
        key=lambda x: x.get("score", 0), reverse=True
    )
    filtered     = _filter_by_score(all_results, MIN_SCORE)
    deduplicated = _deduplicate_results(filtered)

    if not deduplicated:
        return None

    return _format_guide(
        deduplicated, " | ".join(queries)
    )


def is_kb_available() -> bool:
    """
    Check if the knowledge base index is built and ready.
    Called by orchestrator.py and demo_runner.py before
    attempting a search.

    Returns:
        True if ChromaDB collection exists and has documents
    """
    try:
        collection = _get_collection()
        if collection is None:
            return False
        return collection.count() > 0

    except Exception as e:
        log.error(f"KB availability check failed: {e}")
        return False


def get_kb_stats() -> dict:
    """
    Return statistics about the knowledge base.
    Used by the Streamlit dashboard and startup summary.

    Returns:
        Dict with is_available, total_chunks,
        collection_name, chroma_dir, embed_model
    """
    try:
        collection = _get_collection()

        if collection is None:
            return {
                "is_available"    : False,
                "total_chunks"    : 0,
                "collection_name" : COLLECTION_NAME,
                "chroma_dir"      : CHROMA_DIR,
                "embed_model"     : EMBED_MODEL,
            }

        return {
            "is_available"    : True,
            "total_chunks"    : collection.count(),
            "collection_name" : COLLECTION_NAME,
            "chroma_dir"      : CHROMA_DIR,
            "embed_model"     : EMBED_MODEL,
        }

    except Exception as e:
        log.error(f"Cannot get KB stats: {e}")
        return {
            "is_available" : False,
            "total_chunks" : 0,
            "error"        : str(e),
        }


def reset_collection_cache() -> None:
    """
    Reset the module-level ChromaDB singleton.
    Call this after kb_indexer.build_index() completes
    so the next search gets a fresh connection to the
    newly built index.

    Used by demo_runner.py after building the index.
    """
    global _chroma_client, _collection, _embedding_function
    _chroma_client      = None
    _collection         = None
    _embedding_function = None
    log.info("KB collection cache reset — next search will reconnect.")


def _vector_search(query: str, n_results: int) -> list:
    """
    Execute a vector similarity search against ChromaDB.
    Converts ChromaDB distances to similarity scores where
    1.0 = perfect match, 0.0 = completely unrelated.

    Args:
        query     : Cleaned search query text
        n_results : Number of results to retrieve

    Returns:
        List of result dicts sorted by score descending
    """
    collection = _get_collection()

    if collection is None:
        log.warning(
            "KB collection unavailable — cannot search."
        )
        return []

    if collection.count() == 0:
        log.warning(
            "KB collection is empty — "
            "run kb_indexer.py first."
        )
        return []

    try:
        n_results = min(n_results, collection.count())

        raw = collection.query(
            query_texts = [query],
            n_results   = n_results,
            include     = [
                "documents", "metadatas", "distances"
            ],
        )

        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        ids       = raw.get("ids",       [[]])[0]

        results = []
        for doc, meta, dist, chunk_id in zip(
            documents, metadatas, distances, ids
        ):
            similarity = max(0.0, 1.0 - dist)
            results.append({
                "text"        : doc,
                "score"       : round(similarity, 4),
                "file_name"   : meta.get("file_name",   "unknown"),
                "chunk_index" : meta.get("chunk_index", 0),
                "word_count"  : meta.get("word_count",  0),
                "indexed_at"  : meta.get("indexed_at",  ""),
                "id"          : chunk_id,
            })

        results.sort(
            key=lambda x: x["score"], reverse=True
        )

        if results:
            log.debug(
                f"Vector search: {len(results)} result(s). "
                f"Top score: {results[0]['score']:.3f}"
            )

        return results

    except Exception as e:
        log.error(f"ChromaDB query failed: {e}")
        return []


def _filter_by_score(
    results  : list,
    min_score: float,
) -> list:
    """
    Remove results below the minimum relevance threshold.

    Args:
        results   : List of result dicts from _vector_search()
        min_score : Minimum score to keep (0.0 to 1.0)

    Returns:
        Filtered list of result dicts
    """
    filtered = [
        r for r in results if r["score"] >= min_score
    ]
    log.debug(
        f"Score filter ({min_score}): "
        f"{len(results)} → {len(filtered)} results."
    )
    return filtered


def _deduplicate_results(results: list) -> list:
    """
    Remove duplicate or near-duplicate chunks from results.
    Keeps at most 2 chunks per source file and removes
    chunks that share more than 60% of their words with
    an already-selected chunk.

    Args:
        results : List of result dicts from _filter_by_score()

    Returns:
        Deduplicated list of result dicts
    """
    if not results:
        return []

    file_counts  = {}
    deduplicated = []

    for result in results:
        file_name = result["file_name"]
        count     = file_counts.get(file_name, 0)

        if count >= 2:
            continue

        is_duplicate = False
        for existing in deduplicated:
            overlap = _text_overlap_ratio(
                result["text"],
                existing["text"]
            )
            if overlap > 0.6:
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(result)
            file_counts[file_name] = count + 1

    log.debug(
        f"Deduplication: "
        f"{len(results)} → {len(deduplicated)} results."
    )
    return deduplicated


def _text_overlap_ratio(text_a: str, text_b: str) -> float:
    """
    Calculate what fraction of words in text_a also appear
    in text_b. Used for near-duplicate chunk detection.

    Args:
        text_a : First text string
        text_b : Second text string

    Returns:
        Overlap ratio between 0.0 and 1.0
    """
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())

    if not words_a:
        return 0.0

    return len(words_a & words_b) / len(words_a)


def _clean_query(query: str) -> str:
    """
    Clean and normalize query text before embedding.
    Removes noise that hurts vector search quality:
    email addresses, machine names, numbers, and expands
    common IT abbreviations.

    Args:
        query : Raw query text from ticket description

    Returns:
        Cleaned query string (max 200 words)
    """
    if not query:
        return ""

    text = query.lower().strip()

    it_expansions = {
        "av"    : "antivirus",
        "pw"    : "password",
        "pwd"   : "password",
        "os"    : "operating system",
        "o365"  : "office 365",
        "ms"    : "microsoft",
        "pc"    : "computer",
        "vpn"   : "virtual private network vpn",
        "mfa"   : "multi factor authentication mfa",
        "otp"   : "one time password otp",
        "pst"   : "outlook pst email file",
        "bsod"  : "blue screen of death error",
        "rdp"   : "remote desktop rdp",
        "asap"  : "",
        "fyi"   : "",
        "pls"   : "please",
        "plz"   : "please",
        "thx"   : "",
        "thnks" : "",
        "plzz"  : "please",
    }

    words = text.split()
    words = [it_expansions.get(w, w) for w in words]
    text  = " ".join(words)

    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+'
        r'\.[A-Z|a-z]{2,}\b',
        '', text,
    )

    text = re.sub(
        r'\b[A-Z]{2,6}[-_]?[A-Z0-9]{0,4}[-_]?\d{3,6}\b',
        '', text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r'\b\d{3,}\b', '', text)
    text = re.sub(r'[^\w\s\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    if len(words) > 200:
        text = " ".join(words[:200])

    log.debug(f"Cleaned query: '{text[:80]}'")
    return text


def _format_guide(
    results       : list,
    original_query: str,
) -> str:
    """
    Format search results into a clean readable self-help
    guide ready to send to the user.

    Single source → one guide with header.
    Multiple sources → section per document.
    Always adds a footer with timestamp and follow-up note.

    Args:
        results        : Deduplicated result dicts
        original_query : Original search query for context

    Returns:
        Formatted guide string
    """
    if not results:
        return ""

    source_files = list({r["file_name"] for r in results})
    timestamp    = datetime.now(timezone.utc).strftime(
        "%d %b %Y"
    )

    if len(source_files) == 1:
        guide = _format_single_source(results, original_query)
    else:
        guide = _format_multi_source(results, original_query)

    footer = (
        f"\n{'─' * 50}\n"
        f"This guide was automatically retrieved from the "
        f"IT Knowledge Base ({timestamp}).\n"
        f"If these steps do not resolve your issue, an "
        f"engineer will follow up with you shortly.\n"
        f"Please let us know if this guide was helpful."
    )

    return guide + footer


def _format_single_source(results: list, query: str) -> str:
    """
    Format results from a single source document.

    Args:
        results : List of result dicts from one source file
        query   : Original query for context

    Returns:
        Formatted guide string
    """
    file_name  = results[0]["file_name"]
    guide_name = _file_name_to_title(file_name)
    top_score  = results[0]["score"]

    header = (
        f"SELF-HELP GUIDE: {guide_name}\n"
        f"{'═' * 50}\n"
        f"Relevance: {_score_to_label(top_score)}\n\n"
    )

    body_parts = [
        _clean_chunk_text(r["text"])
        for r in results
        if _clean_chunk_text(r["text"])
    ]

    return header + "\n\n".join(body_parts)


def _format_multi_source(results: list, query: str) -> str:
    """
    Format results from multiple source documents.
    Groups chunks by source file and adds section headers.

    Args:
        results : List of result dicts from multiple files
        query   : Original query for context

    Returns:
        Formatted guide string with section headers
    """
    header = (
        f"SELF-HELP GUIDES\n"
        f"{'═' * 50}\n"
        f"We found relevant guides from multiple sources:\n\n"
    )

    grouped: dict = {}
    for result in results:
        fname = result["file_name"]
        if fname not in grouped:
            grouped[fname] = []
        grouped[fname].append(result)

    sections = []
    for file_name, file_results in grouped.items():
        title     = _file_name_to_title(file_name)
        top_score = file_results[0]["score"]

        section_header = (
            f"{'─' * 50}\n"
            f"{title}\n"
            f"Relevance: {_score_to_label(top_score)}\n"
            f"{'─' * 50}\n"
        )

        body_parts = [
            _clean_chunk_text(r["text"])
            for r in file_results
            if _clean_chunk_text(r["text"])
        ]

        sections.append(
            section_header + "\n\n".join(body_parts)
        )

    return header + "\n\n".join(sections)


def _clean_chunk_text(text: str) -> str:
    """
    Clean raw chunk text for display in the formatted guide.
    Normalizes whitespace and removes chunking artifacts.

    Args:
        text : Raw chunk text from ChromaDB

    Returns:
        Cleaned display text
    """
    if not text:
        return ""

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' \n', '\n', text)
    return text.strip()


def _file_name_to_title(file_name: str) -> str:
    """
    Convert a filename to a human-readable guide title.
    e.g. 'vpn_setup_guide.txt' → 'VPN Setup Guide'

    Args:
        file_name : Source document filename

    Returns:
        Human-readable title string
    """
    name = os.path.splitext(file_name)[0]
    name = name.replace("_", " ").replace("-", " ")
    name = " ".join(w.capitalize() for w in name.split())

    overrides = {
        "Vpn Setup Guide"         : "VPN Setup Guide",
        "Antivirus Guide"         : "Antivirus Troubleshooting Guide",
        "Password Reset Guide"    : "Password Reset Guide",
        "Printer Guide"           : "Printer Troubleshooting Guide",
        "Outlook Guide"           : "Microsoft Outlook Troubleshooting Guide",
        "Network Guide"           : "Network Troubleshooting Guide",
        "Os Issue Guide"          : "Windows OS Troubleshooting Guide",
        "App Install Guide"       : "Software Installation Guide",
        "Access Permission Guide" : "Access and Permission Guide",
    }

    return overrides.get(name, name)


def _score_to_label(score: float) -> str:
    """
    Convert a cosine similarity score to a readable label.

    Args:
        score : Score between 0.0 and 1.0

    Returns:
        Label string e.g. 'High (82%)'
    """
    if score >= 0.75:
        label = "High"
    elif score >= 0.50:
        label = "Medium"
    elif score >= 0.30:
        label = "Low"
    else:
        label = "Very Low"

    return f"{label} ({score:.0%})"


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

    print("\n" + "=" * 65)
    print("KB SEARCH — TEST RUN")
    print("=" * 65)
    print(
        f"  Mode       : "
        f"{'DEMO' if DEMO_MODE else 'LIVE'}"
    )
    print(f"  Collection : {COLLECTION_NAME}")
    print(f"  Min score  : {MIN_SCORE}")
    print(f"  Max results: {MAX_RESULTS}")
    print(f"  Embed model: {EMBED_MODEL}")
    print()

    print("Checking KB availability...")
    available = is_kb_available()

    if not available:
        print(
            "KB not indexed — building now...\n"
        )
        from knowledge_base.kb_indexer import (
            create_sample_docs,
            build_index,
        )
        create_sample_docs()
        build_index(force_rebuild=True)

        reset_collection_cache()
        available = is_kb_available()

        if not available:
            print("Failed to build index. Check logs.")
            exit(1)

    stats = get_kb_stats()
    print(f"  Status       : Available ✓")
    print(f"  Total chunks : {stats['total_chunks']}")
    print(f"  Collection   : {stats['collection_name']}")
    print(f"  Embed model  : {stats['embed_model']}\n")

    print("=" * 65)
    print("SEARCH TEST CASES")
    print("=" * 65)

    test_cases = [
        {
            "label" : "VPN not connecting",
            "query" : (
                "I cannot connect to VPN from home. "
                "Cisco AnyConnect shows connection timed out. "
                "I need to access company files urgently."
            ),
        },
        {
            "label" : "Antivirus out of date",
            "query" : (
                "My Symantec antivirus is showing a red warning. "
                "Virus definitions are out of date. "
                "LiveUpdate keeps failing."
            ),
        },
        {
            "label" : "Password reset",
            "query" : (
                "I forgot my Windows password and my account "
                "is locked out. I cannot log in to my laptop."
            ),
        },
        {
            "label" : "Outlook crashing",
            "query" : (
                "Outlook is not opening this morning. "
                "It crashes immediately on startup. "
                "I cannot send or receive emails."
            ),
        },
        {
            "label" : "Printer offline",
            "query" : (
                "My printer is showing as offline. "
                "Cannot print. Print queue is stuck."
            ),
        },
        {
            "label"    : "Category search — network",
            "category" : "network",
        },
        {
            "label"   : "Multi-query — VPN and Outlook",
            "queries" : [
                "VPN not connecting from home",
                "Outlook not opening email not working",
            ],
        },
        {
            "label" : "Short query",
            "query" : "printer not printing",
        },
        {
            "label" : "Unrelated — should return None",
            "query" : (
                "I want to order a new office chair and "
                "request stationery supplies for my desk."
            ),
        },
    ]

    found_count    = 0
    notfound_count = 0

    for i, tc in enumerate(test_cases, start=1):
        label = tc["label"]
        print(f"\n[Test {i}] {label}")
        print("-" * 55)

        if "category" in tc:
            result = search_by_category(tc["category"])
        elif "queries" in tc:
            result = search_multi_query(tc["queries"])
        else:
            result = search_knowledge_base(tc["query"])

        if result:
            found_count += 1
            preview = result[:250].replace("\n", " ")
            print(f"  Result  : FOUND ✓")
            print(f"  Preview : {preview}...")

            if "query" in tc:
                details = search_with_details(tc["query"])
                if details:
                    print(f"  Sources :")
                    for d in details:
                        print(
                            f"    [{d['rank']}] "
                            f"{d['file_name']:<35} "
                            f"score: {d['score']:.3f} "
                            f"chunk: {d['chunk_index']}"
                        )
        else:
            notfound_count += 1
            print(f"  Result  : NOT FOUND ✗")

    print("\n" + "=" * 65)
    print(
        f"Tests complete — "
        f"{found_count} found, "
        f"{notfound_count} not found."
    )
    print("=" * 65 + "\n")