"""
CodeRabbit API integration service

This module provides functions to interact with the CodeRabbit API for generating
code review reports. It handles authentication, request formatting, error handling,
and parameter validation.
"""

import os
import requests
import logging
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# CodeRabbit Configuration
CODERABBIT_API_KEY: Optional[str] = os.getenv("CODERABBIT_API_KEY")
CODERABBIT_API_BASE: str = "https://api.coderabbit.ai/api/v1"


def _load_default_prompt() -> str:
    """Load the default prompt from crprompt.md"""
    try:
        with open('crprompt.md', 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("crprompt.md not found, using empty default prompt")
        return ""

def generate_coderabbit_report(from_date: str, to_date: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Generate a CodeRabbit report with the specified parameters.

    This function makes a POST request to the CodeRabbit API to generate a code
    review report for the specified date range. It handles authentication,
    request formatting, and error responses.

    Args:
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        **kwargs: Additional CodeRabbit API parameters including:
            - scheduleRange (str): Schedule range for the report
            - prompt (str): Custom prompt for analysis
            - promptTemplate (str): Template name for prompts
            - parameters (list): Array of filter parameters
            - groupBy (str): Primary grouping field
            - subgroupBy (str): Secondary grouping field
            - orgId (str): Organization ID

    Returns:
        Dict containing either:
        - Success: {"data": report_data, "status": "success"}
        - Error: {"error": error_message, "details": error_details, "status": "error"}

    Raises:
        No exceptions are raised; all errors are returned in the response dict.
    """
    if not CODERABBIT_API_KEY:
        return {"error": "CODERABBIT_API_KEY not configured", "status": "error"}

    headers = {
        "x-coderabbitai-api-key": CODERABBIT_API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    # Build payload with required parameters
    payload = {
        "from": from_date,
        "to": to_date
    }

    # Add default prompt if no custom prompt is provided
    if "prompt" not in kwargs or kwargs["prompt"] is None:
        default_prompt = _load_default_prompt()
        if default_prompt:
            payload["prompt"] = default_prompt

    # Add optional parameters if provided
    optional_params = [
        "scheduleRange", "prompt", "promptTemplate", "parameters",
        "groupBy", "subgroupBy", "orgId"
    ]

    for param in optional_params:
        if param in kwargs and kwargs[param] is not None:
            payload[param] = kwargs[param]

    try:
        logger.info(f"Making request to CodeRabbit API: {CODERABBIT_API_BASE}/report.generate")
        logger.info(f"Request payload: {payload}")
        logger.info(f"Request headers: {headers}")
        
        response = requests.post(
            f"{CODERABBIT_API_BASE}/report.generate",
            json=payload,
            headers=headers,
            timeout=120
        )

        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response text: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response JSON: {response_data}")
            return {"data": response_data, "status": "success"}
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"message": response.text}
            logger.error(f"CodeRabbit API error: {response.status_code}")
            logger.error(f"Error details: {error_data}")
            return {
                "error": f"CodeRabbit API error: {response.status_code}",
                "details": error_data,
                "status": "error"
            }

    except requests.exceptions.Timeout:
        return {"error": "Request to CodeRabbit timed out", "status": "error"}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to CodeRabbit", "status": "error"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "status": "error"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "status": "error"}


def validate_report_parameters(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate CodeRabbit report parameters.

    This function validates the input parameters for generating a CodeRabbit report.
    It checks for required fields, date format validation, and date range logic.

    Args:
        data: Dictionary containing the request parameters to validate

    Returns:
        Tuple containing:
        - bool: True if validation passes, False otherwise
        - Optional[str]: Error message if validation fails, None if successful
        - Optional[Dict]: Validated and formatted parameters if successful, None if failed

    Validation Rules:
        - 'from'/'from_date' and 'to'/'to_date' are required
        - Dates must be in YYYY-MM-DD format
        - from_date must be before to_date
        - Optional parameters are passed through if present
    """
    from datetime import datetime

    # Validate required fields (support both 'from'/'to' and 'from_date'/'to_date')
    from_date = data.get("from") or data.get("from_date")
    to_date = data.get("to") or data.get("to_date")

    if not from_date or not to_date:
        return False, "from/from_date and to/to_date are required", None

    # Validate date format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD", None

    # Validate date range
    if from_date >= to_date:
        return False, "from_date must be before to_date", None

    # Extract optional parameters
    optional_params = {}
    param_mapping = {
        "scheduleRange": "scheduleRange",
        "prompt": "prompt",
        "promptTemplate": "promptTemplate",
        "parameters": "parameters",
        "groupBy": "groupBy",
        "subgroupBy": "subgroupBy",
        "orgId": "orgId"
    }

    for key, coderabbit_key in param_mapping.items():
        if key in data and data[key] is not None:
            optional_params[coderabbit_key] = data[key]

    return True, None, {
        "from_date": from_date,
        "to_date": to_date,
        "organization": data.get("organization", "default"),
        "optional_params": optional_params
    }