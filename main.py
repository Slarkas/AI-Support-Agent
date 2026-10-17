
#!/usr/bin/env python3
"""
AI Support Agent - LLM-first support ticket analysis.
Uses an LLM by default and falls back to rule-based analysis on failure.
Compatible with Python 3.10, standard library only.
"""

import json
import re
import urllib.error
import urllib.request

from config import (
    API_URL,
    MODEL_ID,
    REQUEST_TIMEOUT,
    get_api_headers,
    validate_response_structure,
)


def analyze_ticket(message: str) -> dict:
    """Analyze a support ticket using rule-based classification."""
    if not message or not message.strip():
        return {
            "category": "general",
            "priority": "low",
            "summary": "Empty ticket provided.",
            "recommended_action": "Request additional details from the customer.",
        }

    text = message.lower()
    category = _detect_category(text)
    priority = _detect_priority(text, category)

    clean_message = message.strip()
    summary = clean_message if len(clean_message) <= 80 else clean_message[:77] + "..."
    recommended_action = _recommend_action(category, priority, text)

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "recommended_action": recommended_action,
    }


def _detect_category(text: str) -> str:
    """Detect ticket category from message keywords."""
    crash_error_keywords = [
        "error", "crash", "broken", "bug", "not working",
        "doesn't work", "freeze", "frozen", "failed",
    ]

    billing_keywords = [
        "invoice", "charge", "payment", "refund", "price",
        "billing", "subscription", "plan upgrade", "overcharged", "fee",
    ]

    access_keywords = [
        "access", "login", "password", "account locked",
        "timeout", "slow", "restart", "reboot", "install",
    ]

    order_keywords = [
        "order", "shipping", "delivery", "tracking",
        "package", "where is my",
    ]

    # Specific technical failures take precedence over topic keywords.
    if any(keyword in text for keyword in crash_error_keywords):
        return "technical_issue"

    if any(keyword in text for keyword in billing_keywords):
        return "billing"

    if any(keyword in text for keyword in access_keywords):
        return "technical_issue"

    if any(keyword in text for keyword in order_keywords):
        return "order_status"

    return "general"


def _detect_priority(text: str, category: str) -> str:
    """Detect ticket priority from urgency indicators."""
    if re.search(r"\bdown\b", text) or "outage" in text or "service down" in text:
        return "high"

    if any(keyword in text for keyword in ["urgent", "critical"]):
        return "high"

    access_high_priority_keywords = [
        "can't access", "cannot access", "locked out",
        "not working at all", "everyone affected",
        "all users", "complete failure",
    ]

    if category == "technical_issue":
        if any(keyword in text for keyword in access_high_priority_keywords):
            return "high"

        if any(word in text for word in ["error code", "exception", "failed"]):
            return "medium"

    if category == "billing":
        if any(word in text for word in ["wrong amount", "double charged"]):
            return "medium"
        return "low"

    if category == "technical_issue":
        return "medium"

    return "low"


def analyze_ticket_with_llm(message: str) -> dict:
    """
    Analyze a support ticket using the configured LLM API.

    Raises an exception if the request fails or the model response is invalid.
    """
    if not message or not message.strip():
        return analyze_ticket(message)

    system_prompt = (
        "You are a support ticket analyzer. Classify each ticket into one of these "
        "categories: technical_issue, billing, order_status, general. Assign one of "
        "these priorities: high, medium, low.\n\n"
        "Return ONLY a JSON object with exactly four fields:\n"
        "- category (string): the ticket category\n"
        "- priority (string): the ticket priority\n"
        "- summary (string): brief auto-generated summary\n"
        "- recommended_action (string): suggested response action\n\n"
        "Do not include any text outside the JSON object. Do not explain your reasoning."
    )

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this support ticket:\n\n{message}"},
        ],
        "temperature": 0.1,
        "max_tokens": 300,
        "response_format": {"type": "json_schema", "json_schema": {
    "name": "ticket_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["technical_issue", "billing", "order_status", "general"]
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"]
            },
            "summary": {"type": "string"},
            "recommended_action": {"type": "string"}
        },
        "required": ["category", "priority", "summary", "recommended_action"],
        "additionalProperties": False
    }
}},
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=get_api_headers(),
        method="POST",
    )

    
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            api_result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"LLM API HTTP error {exc.code}: {exc.reason}\n"
            f"Details: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not connect to the LLM API: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM API returned invalid JSON") from exc
    except TimeoutError as exc:
        raise RuntimeError("LLM API request timed out") from exc

    if not isinstance(api_result, dict):
        raise RuntimeError("LLM API response is not a JSON object")

    choices = api_result.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("LLM API returned no choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("LLM API returned an invalid choice")

    response_message = first_choice.get("message")
    if not isinstance(response_message, dict):
        raise RuntimeError("LLM API response has no valid message")

    raw_content = response_message.get("content")
    if not isinstance(raw_content, str) or not raw_content.strip():
        raise RuntimeError("LLM returned empty content")

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Could not parse the model output as JSON") from exc

    return validate_response_structure(parsed)


def _recommend_action(category: str, priority: str, text: str) -> str:
    """Generate a recommended action for rule-based analysis."""
    if priority == "high":
        if "outage" in text or re.search(r"\bdown\b", text):
            return (
                "Escalate to engineering immediately. Check service status "
                "dashboard and notify affected users."
            )

        if any(word in text for word in ["access", "locked", "login"]):
            return (
                "Prioritize account access restoration. Verify user identity "
                "and reset credentials if needed."
            )

        return "Escalate as urgent. Assign to senior support specialist."

    if category == "technical_issue":
        return (
            "Troubleshoot step-by-step. Check logs, verify configuration, "
            "and suggest restart/update if applicable."
        )

    if category == "billing":
        return (
            "Review account charges. Verify invoice details and process "
            "adjustment or refund if needed."
        )

    if category == "order_status":
        return (
            "Check order tracking information. Provide estimated delivery "
            "date and shipping status to customer."
        )

    return "Respond politely, gather more context, and route as appropriate."


def main():
    """Run the interactive LLM-first support ticket analyzer."""
    print("=" * 60)
    print("AI Support Agent - LLM-First Ticket Analysis")
    print("=" * 60)
    print("LLM analysis is enabled by default.")
    print("If the LLM fails, rule-based analysis will be used instead.")
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

        if user_input.strip().lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        try:
            result = analyze_ticket_with_llm(user_input)
            analysis_method = "LLM"
        except Exception as exc:
            print(f"\nLLM analysis failed: {exc}")
            print("Falling back to rule-based analysis.")
            result = analyze_ticket(user_input)
            analysis_method = "Rule-based fallback"

        print("\n" + "-" * 60)
        print(f"Analysis method:    {analysis_method}")
        print(f"Category:           {result['category']}")
        print(f"Priority:           {result['priority']}")
        print(f"Summary:            {result['summary']}")
        print(f"Recommended Action: {result['recommended_action']}")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
