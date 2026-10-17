import unittest
import sys
from unittest import mock
import json
import urllib.request
import urllib.error

sys.path.insert(0, '.')
from main import analyze_ticket, analyze_ticket_with_llm, API_URL, MODEL_ID


class TicketAnalysisTests(unittest.TestCase):
    """Unit tests for the AI Support Agent ticket analysis."""

    def test_service_outage_high_priority(self):
        result = analyze_ticket("Our website is down and nobody can access it!")
        self.assertEqual(result['category'], 'technical_issue')
        self.assertEqual(result['priority'], 'high')

    def test_billing_wrong_invoice_low_priority(self):
        result = analyze_ticket("I received a wrong invoice for $50 instead of $30")
        self.assertEqual(result['category'], 'billing')
        self.assertEqual(result['priority'], 'low')

    def test_order_tracking_low_priority(self):
        result = analyze_ticket("Where is my order? Tracking number 12345")
        self.assertEqual(result['category'], 'order_status')
        self.assertEqual(result['priority'], 'low')

    def test_empty_message_general_low_priority(self):
        result = analyze_ticket("")
        self.assertEqual(result['category'], 'general')
        self.assertEqual(result['priority'], 'low')

    def test_billing_with_account_access_not_tech_issue(self):
        """Billing message mentioning access should be billing, not technical."""
        result = analyze_ticket("I can't access my invoice and it's wrong")
        self.assertEqual(result['category'], 'billing')

    def test_downloaded_invoice_is_not_high_priority(self):
        """Invoice download issue should not be high priority."""
        result = analyze_ticket("I downloaded my invoice but need a copy emailed to me")
        self.assertNotEqual(result['priority'], 'high')

    def test_payment_page_crash_is_technical(self):
        """Payment page crash is a technical issue, not billing."""
        result = analyze_ticket("The payment page crashes whenever I try to pay")
        self.assertEqual(result['category'], 'technical_issue')

    def test_delayed_order_with_refund_request(self):
        """Documents current behavior: refund keyword triggers billing category."""
        result = analyze_ticket("My order is late - I want a refund")
        # Current rule-based logic detects 'refund' before 'order'
        self.assertEqual(result['category'], 'billing')

    def test_non_urgent_technical_issue(self):
        """Technical issue without urgency should be medium, not high."""
        result = analyze_ticket("I'm getting an error when saving files")
        self.assertEqual(result['category'], 'technical_issue')
        self.assertEqual(result['priority'], 'medium')

    def test_result_contains_all_required_keys(self):
        messages = [
            "Our website is down",
            "Wrong invoice received",
            "Where is my order?",
            ""
        ]
        required_keys = ['category', 'priority', 'summary', 'recommended_action']
        
        for msg in messages:
            result = analyze_ticket(msg)
            for key in required_keys:
                self.assertIn(key, result, f"Missing key '{key}' for message: {msg!r}")


class LLMAnalysisTests(unittest.TestCase):
    """Unit tests for analyze_ticket_with_llm with mocked HTTP."""

    def test_valid_llm_response(self):
        payload = {
            "choices": [{
                "message": {"content": json.dumps({
                    "category": "technical_issue",
                    "priority": "high",
                    "summary": "Website is down for all users.",
                    "recommended_action": "Escalate to engineering."
                })}
            }]
        }

        class FakeResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def getcode(self):
                return 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            result = analyze_ticket_with_llm("Our website is completely down.")

        self.assertEqual(result["category"], "technical_issue")
        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["summary"], "Website is down for all users.")
        self.assertEqual(result["recommended_action"], "Escalate to engineering.")

    def test_empty_model_content_raises(self):
        payload = {"choices": [{"message": {"content": ""}}]}

        class FakeResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def getcode(self):
                return 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(Exception) as ctx:
                analyze_ticket_with_llm("Ticket message")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_invalid_json_raises(self):
        payload = {"choices": [{"message": {"content": "not json"}}]}

        class FakeResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def getcode(self):
                return 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(Exception) as ctx:
                analyze_ticket_with_llm("Ticket message")
        self.assertIn("json", str(ctx.exception).lower())

    def test_invalid_category_raises(self):
        payload = {
            "choices": [{
                "message": {"content": json.dumps({
                    "category": "unknown_type",
                    "priority": "high",
                    "summary": "Test summary.",
                    "recommended_action": "Test action."
                })}
            }]
        }

        class FakeResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def getcode(self):
                return 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(Exception) as ctx:
                analyze_ticket_with_llm("Ticket message")
        self.assertIn("category", str(ctx.exception).lower())

    def test_invalid_priority_raises(self):
        payload = {
            "choices": [{
                "message": {"content": json.dumps({
                    "category": "technical_issue",
                    "priority": "extreme",
                    "summary": "Test summary.",
                    "recommended_action": "Test action."
                })}
            }]
        }

        class FakeResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def getcode(self):
                return 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(Exception) as ctx:
                analyze_ticket_with_llm("Ticket message")
        self.assertIn("priority", str(ctx.exception).lower())

    def test_missing_field_raises(self):
        payload = {
            "choices": [{
                "message": {"content": json.dumps({
                    "category": "technical_issue",
                    "priority": "high"
                })}
            }]
        }

        class FakeResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def getcode(self):
                return 200
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(Exception) as ctx:
                analyze_ticket_with_llm("Ticket message")
        self.assertIn("field", str(ctx.exception).lower())

    def test_http_error_raises(self):
        with mock.patch("urllib.request.urlopen") as mock_open:
            http_err = urllib.error.HTTPError(
                API_URL, 503, "Service Unavailable", {}, None)
            mock_open.side_effect = http_err

            with self.assertRaises(Exception) as ctx:
                analyze_ticket_with_llm("Ticket message")
        self.assertIn("503", str(ctx.exception))
