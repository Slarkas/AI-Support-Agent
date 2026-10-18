#!/usr/bin/env python3
"""
AI Support Agent - Rule-based prototype for ticket analysis.
Uses keyword matching to categorize and prioritize support tickets.
Compatible with Python 3.10, standard library only.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

# Add test dependencies only when actually running tests.
try:
    import unittest
except ImportError:
    unittest = None
try:
    from unittest import mock
except ImportError:
    mock = None
# Import LLM client module (provides analyze_ticket_with_llm)
from llm_client import analyze_ticket_with_llm

# Import configuration directly from config.py
from config import API_URL, MODEL_ID, REQUIRED_FIELDS

# Import ticket storage module for SQLite persistence
try:
    from ticket_store import init_db, save_ticket
except ImportError:
    save_ticket = None

REQUEST_TIMEOUT = 120
def analyze_ticket(message: str) -> dict:
    """
    Analyze a support ticket message and return structured results.

    Returns a dictionary with:
        - category: one of 'technical_issue', 'billing', 'order_status', 'general'
        - priority: one of 'high', 'medium', 'low'
        - summary: brief auto-generated summary
        - recommended_action: suggested response action
    """
    if not message or not message.strip():
        return {
            "category": "general",
            "priority": "low",
            "summary": "Empty ticket provided.",
            "recommended_action": "Request additional details from the customer."
        }

    text = message.lower()

    # Determine category using keyword matching
    category = _detect_category(text)

    # Determine priority based on urgency indicators
    priority = _detect_priority(text, category)

    # Generate summary (first 80 chars or full if shorter)
    clean_message = message.strip()
    if len(clean_message) > 80:
        summary = clean_message[:77] + "..."
    else:
        summary = clean_message

    # Recommend action based on category and priority
    recommended_action = _recommend_action(category, priority, text)

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "recommended_action": recommended_action
    }


def _detect_category(text: str) -> str:
    """Detect ticket category from message keywords."""
    # Technical issue indicators
    technical_keywords = [
        "error", "crash", "broken", "bug", "not working", "doesn't work",
        "access", "login", "password", "account locked", "timeout", "slow",
        "freeze", "frozen", "restart", "reboot", "install", "update failed"
    ]

    # Billing indicators
    billing_keywords = [
        "invoice", "charge", "payment", "refund", "price", "billing",
        "subscription", "plan upgrade", "overcharged", "fee"
    ]

    # Order status indicators
    order_keywords = [
        "order", "shipping", "delivery", "tracking", "package", "where is my"
    ]

        
    
    # Check for specific technical failures first - these are more precise
    # indicators than general topic words like "payment"
    crash_error_keywords = ["error", "crash", "broken", "bug", "not working",
                           "doesn't work", "freeze", "frozen", "failed"]
    for keyword in crash_error_keywords:
        if keyword in text:
            return "technical_issue"

    # Check for billing issues - but only after specific technical failures
    for keyword in billing_keywords:
        if keyword in text:
            return "billing"

    # Check for remaining technical access/login issues
    access_keywords = ["access", "login", "password", "account locked",
                      "timeout", "slow", "restart", "reboot", "install"]
    for keyword in access_keywords:
        if keyword in text:
            return "technical_issue"

    # Check for order status
    for keyword in order_keywords:
        if keyword in text:
            return "order_status"

    # Default to general
    return "general"


def _detect_priority(text: str, category: str) -> str:
    """Detect ticket priority from urgency indicators."""
        # High priority for service outages (applies to all categories)
    # Use word boundary regex for short keywords like "down" to avoid false
    # matches inside words such as "downloaded", "downtown", etc.
    if re.search(r'\bdown\b', text) or "outage" in text or "service down" in text:
        return "high"

    # Urgency keywords that apply generally
    urgency_keywords = ["urgent", "critical"]
    if any(keyword in text for keyword in urgency_keywords):
        return "high"

    # Access-related high priority - only for technical issues, not billing/order
    access_high_priority_keywords = [
        "can't access", "cannot access", "locked out",
        "not working at all", "everyone affected", "all users", "complete failure"
    ]

    if category == "technical_issue":
        for keyword in access_high_priority_keywords:
            if keyword in text:
                return "high"

    # Technical issues with error indicators are medium-high
    if category == "technical_issue":
        if any(word in text for word in ["error code", "exception", "failed"]):
            return "medium"

    # Default to medium for technical, low for others
    if category == "billing":
        if any(word in text for word in ["wrong amount", "double charged"]):
            return "medium"
        return "low"

    if category == "technical_issue":
        return "medium"

    return "low"


def _recommend_action(category: str, priority: str, text: str) -> str:
    """Generate recommended action based on analysis."""
    if priority == "high":
        if "outage" in text or "down" in text:
            return "Escalate to engineering immediately. Check service status dashboard and notify affected users."
        elif any(word in text for word in ["access", "locked", "login"]):
            return "Prioritize account access restoration. Verify user identity and reset credentials if needed."
        else:
            return "Escalate as urgent. Assign to senior support specialist."

    if category == "technical_issue":
        return "Troubleshoot step-by-step. Check logs, verify configuration, and suggest restart/update if applicable."

    if category == "billing":
        return "Review account charges. Verify invoice details and process adjustment or refund if needed."

    if category == "order_status":
        return "Check order tracking information. Provide estimated delivery date and shipping status to customer."

    return "Respond politely, gather more context, and route as appropriate."








def run_tests():
    """Run the test suite from this script."""
    if unittest is None:
        raise ImportError("unittest not available; cannot run tests.")

    # Import the test module dynamically so we can discover all tests.
    import test_agent
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_agent)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    """Interactive command-line interface for the AI Support Agent."""
    # Check for --test argument to run tests instead of interactive mode.
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            exit_code = run_tests()
        except Exception as e:
            print(f"Failed to run tests: {e}")
            exit_code = 1
        finally:
            sys.exit(exit_code)

    print("=" * 60)
    print("AI Support Agent - Ticket Analysis (Rule-Based Prototype)")
    print("=" * 60)
    
    # Initialize SQLite ticket storage if available
    try:
        init_db()
    except Exception as e:
        print(f"Note: Ticket database initialization warning: {e}")
    print("Type a support ticket message to analyze.")
    print("Type 'quit' or 'exit' to end.\n")

    while True:
        try:
            user_input = input("Enter ticket message: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input.strip():
            print("Please enter a ticket message, or type 'quit' to exit.")
            continue
        
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        try:
            result = analyze_ticket_with_llm(user_input)
            analysis_method = "LLM"
        except Exception as exc:
            print(f"LLM analysis failed: {exc}")
            print("Falling back to rule-based analysis.")
            result = analyze_ticket(user_input)
            analysis_method = "Rule-based fallback"
        
        # Save ticket to SQLite database for persistence
        try:
            if save_ticket is not None:
                ticket_id = save_ticket(message=user_input, result=result, analysis_method=analysis_method)
                print(f"Ticket saved with ID: {ticket_id}")
        except Exception as e:
            print(f"Warning: Failed to save ticket to database: {e}")

        print("\n" + "-" * 60)
        print(f"Analysis method:    {analysis_method}")
        print(f"Category:           {result['category']}")
        print(f"Priority:           {result['priority']}")
        print(f"Summary:            {result['summary']}")
        print(f"Recommended Action: {result['recommended_action']}")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()