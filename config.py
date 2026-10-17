"""
AI Support Agent - Configuration settings for AI provider integration.
Centralizes all API-related constants and provides validation utilities.
Compatible with Python 3.10, standard library only.
"""

import os

# Base URL for the LM Studio server (without trailing /chat/completions)
API_BASE_URL = "http://localhost:1235/v1"

# Full API endpoint constructed from base URL
API_URL = f"{API_BASE_URL}/chat/completions"

# The specific model to use on the LM Studio server
MODEL_ID = "qwen3.8-27b-turbofcfusion-735-882-here-uncen-neo-coder-max-low-mtp"

# API key from environment variable, empty string if not set (LM Studio default)
API_KEY = os.getenv("AI_API_KEY", "")

# Timeout in seconds for HTTP requests to the LLM server
REQUEST_TIMEOUT = 120

# Allowed categories and priorities for validation
ALLOWED_CATEGORIES = {"technical_issue", "billing", "order_status", "general"}
ALLOWED_PRIORITIES = {"high", "medium", "low"}
REQUIRED_FIELDS = ["category", "priority", "summary", "recommended_action"]


def get_api_headers() -> dict:
    """Return HTTP headers for API requests.

    Includes authorization header only if API key is configured.
    LM Studio's default configuration does not require authentication.
    """
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def validate_response_structure(response_data):
    """Validate that parsed JSON response has the required structure.

    Args:
        response_data: Parsed JSON object from the API.

    Returns:
        dict: Validated and cleaned data with required fields.

    Raises:
        Exception: If validation fails for any reason.
    """
    if not isinstance(response_data, dict):
        raise Exception("Response is not a JSON object")

    # Validate all required fields exist and are non-empty strings
    for field in REQUIRED_FIELDS:
        value = response_data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise Exception(f"Missing or empty required field: '{field}'")

    # Strip whitespace from values
    cleaned = {}
    for field in REQUIRED_FIELDS:
        cleaned[field] = response_data[field].strip()

    # Validate enum-like fields against allowed values
    if cleaned["category"] not in ALLOWED_CATEGORIES:
        raise Exception(f"Invalid category: '{cleaned['category']}'")
    if cleaned["priority"] not in ALLOWED_PRIORITIES:
        raise Exception(f"Invalid priority: '{cleaned['priority']}'")

    return cleaned