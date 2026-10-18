"""
AI Support Agent - LLM Client Module.
Provides LLM-based ticket analysis using LM Studio API.
Compatible with Python 3.10, standard library only.
"""

from config import (
    MODEL_ID,
    API_URL,
    REQUEST_TIMEOUT,
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    REQUIRED_FIELDS,
    validate_response_structure,
)
import json
import urllib.request


def analyze_ticket_with_llm(message: str) -> dict:
    """
    Analyze a support ticket using the LM Studio LLM API.

    Sends the message to the configured model and parses its JSON response.
    Returns a dictionary with category, priority, summary, recommended_action.
    Raises an exception if the request fails or the response is invalid.
    """
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
            {"role": "user", "content": f"Classify this support ticket:\n\n{message}"}
        ],
        "temperature": 0.1,
        "max_tokens": 300,
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise Exception(f"URL error: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise Exception("API response is not valid JSON") from e

    # Extract the model's response content
    choices = result.get("choices", [])
    if not choices:
        raise Exception("API returned empty choices list")

    message_obj = choices[0].get("message", {})
    raw_content = (message_obj.get("content") or "").strip()
    if not raw_content:
        raise Exception("Model returned empty content")

    # Parse the JSON object from the model's response
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse model output as JSON: {e}\nRaw: {raw_content}") from e

    if not isinstance(parsed, dict):
        raise Exception("Model response is not a JSON object")

    # Use centralized validation helper from config.py
    validate_response_structure(parsed)

    return {
        "category": parsed["category"],
        "priority": parsed["priority"],
        "summary": parsed["summary"],
        "recommended_action": parsed["recommended_action"]
    }