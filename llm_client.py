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
    validate_response_structure,
)
import json
import urllib.request


def _normalize_category(category: str) -> str:
    """Normalize category name to standard format."""
    normalized = category.lower().strip()
    
    # Map variations to canonical values
    if any(x in normalized for x in ["system outage", "technical issue", 
                                        "technical problem"]):
        return "technical_issue"
    elif any(x in normalized for x in ["payment issue", "billing issue"]):
        return "billing"
    elif any(x in normalized for x in ["order status", "delivery status"]):
        return "order_status"
    elif normalized == "general inquiry":
        return "general"
    
    # If no mapping found, leave unchanged (validation will reject invalid values)
    return category


def analyze_ticket_with_llm(message: str) -> dict:
    """
    Analyze a support ticket using the LM Studio LLM API.

    Sends the message to the configured model and parses its JSON response.
    Returns a dictionary with category, priority, summary, recommended_action.
    Raises an exception if the request fails or the response is invalid.
    """
    system_prompt = (
        "Return ONLY valid JSON with these fields: category, priority, summary, recommended_action. No other text.\n\n"
        "VALID CATEGORIES (choose exactly one):\n"
        "- technical_issue\n"
        "- billing\n"
        "- order_status\n"
        "- general\n\n"
        "VALID PRIORITIES (choose exactly one):\n"
        "- high\n"
        "- medium\n"
        "- low\n\n"
        "IMPORTANT:\n"
        "- The category 'critical' is NOT valid. Use priority='high' for critical issues.\n"
        "- Return ONLY the JSON object, no explanations or extra text."
    )

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this support ticket:\n\n{message}"}
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
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
        # Add diagnostic logging for empty content case
        print(f"  [DEBUG] Model response analysis:")
        print(f"  [DEBUG]   HTTP status code: {response.getcode()}")
        print(f"  [DEBUG]   Response JSON top-level keys: {list(result.keys())}")
        print(f"  [DEBUG]   First choice object keys: {list(choices[0].keys()) if choices else 'N/A'}")

        first_choice = choices[0]
        msg_obj = first_choice.get("message", {})

        content_exists = "content" in msg_obj
        reasoning_content_exists = "reasoning_content" in msg_obj or "reasoning" in msg_obj

        print(f"  [DEBUG]   'message.content' exists: {content_exists}")
        if content_exists:
            print(f"  [DEBUG]     message.content length: {len(msg_obj.get('content', ''))} chars")

        reasoning_exists = (msg_obj.get("reasoning_content") or msg_obj.get("reasoning")) is not None
        print(f"  [DEBUG]   'message.reasoning_content'/'message.reasoning' exists: {reasoning_exists}")
        if reasoning_exists:
            for key in ["reasoning_content", "reasoning"]:
                val = msg_obj.get(key)
                if val:
                    print(f"  [DEBUG]     '{key}' length: {len(val)} chars")

        finish_reason = first_choice.get("finish_reason", "N/A")
        print(f"  [DEBUG]   finish_reason: {finish_reason}")

    if not raw_content:
        # Log diagnostic info for empty content case
        first_choice = choices[0]
        msg_obj = first_choice.get("message", {})
        
        print(f"  [DEBUG] Model returned empty content:")
        print(f"  [DEBUG]   finish_reason: {first_choice.get('finish_reason', 'N/A')}")
        usage = result.get("usage", {})
        if usage:
            print(f"  [DEBUG]   usage.prompt_tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  [DEBUG]   usage.completion_tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  [DEBUG]   usage.total_tokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print(f"  [DEBUG]   usage object missing from response")
        
        if not msg_obj or not msg_obj.get("content"):
            print(f"  [DEBUG]   message.content is empty")
        else:
            print(f"  [DEBUG]   message.content length: {len(msg_obj.get('content', ''))} chars")
            
        has_reasoning = (msg_obj.get("reasoning_content") or msg_obj.get("reasoning"))
        if has_reasoning:
            for key in ["reasoning_content", "reasoning"]:
                val = msg_obj.get(key)
                if val:
                    print(f"  [DEBUG]   {key}: present ({len(val)} chars)")

    # Check for empty content and raise a clear exception before JSON parsing
    if not raw_content or (isinstance(raw_content, str) and raw_content.strip() == ""):
        raise Exception("Empty model response: no valid JSON returned")

# Parse the JSON object from the model's response
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse model output as JSON: {e}\nRaw: {raw_content}") from e

    if not isinstance(parsed, dict):
        raise Exception("Model response is not a JSON object")

    # Normalize the category before validation
    original_category = parsed["category"]
    normalized_category = _normalize_category(original_category)
    
    if normalized_category != original_category:
        print(f"  [DEBUG] Normalized category from '{original_category}' to '{normalized_category}'")
    else:
        # Check if the original value is still valid after normalization attempt
        valid_categories = {"technical_issue", "billing", "order_status", "general"}
        if parsed["category"] not in valid_categories:
            raise Exception(
                f"Invalid category '{original_category}': expected one of "
                f"{{'technical_issue', 'billing', 'order_status', 'general'}}. "
                f"(Note: 'critical' is a priority, not a category; use priority='high')"
            )
    
    # Use centralized validation helper from config.py
    validate_response_structure(parsed)

    return {
        "category": parsed["category"],
        "priority": parsed["priority"],
        "summary": parsed["summary"],
        "recommended_action": parsed["recommended_action"]
    }