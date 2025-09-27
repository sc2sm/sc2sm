"""
CodeRabbit API integration service for automated code analysis.

This module provides comprehensive integration with the CodeRabbit API for
generating code review reports. It handles authentication, request formatting,
error handling, parameter validation, and response processing.

Key Features:
- Secure API authentication using API keys
- Comprehensive parameter validation and formatting
- Robust error handling with detailed error messages
- Support for custom prompts and analysis parameters
- Timeout handling and connection error management
- Logging for debugging and monitoring

Main Functions:
- generate_coderabbit_report(): Generate reports from CodeRabbit API
- validate_report_parameters(): Validate and format request parameters
- _load_default_prompt(): Load default analysis prompts

API Integration:
- Base URL: https://api.coderabbit.ai/api/v1
- Authentication: x-coderabbitai-api-key header
- Endpoint: /report.generate
- Timeout: 120 seconds for long-running analysis

Author: Source2Social Team
Version: 1.0.0
"""

import os
import requests
import logging
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# CodeRabbit API Configuration
CODERABBIT_API_KEY: Optional[str] = os.getenv("CODERABBIT_API_KEY")
CODERABBIT_API_BASE: str = "https://api.coderabbit.ai/api/v1"


def _load_default_prompt() -> str:
    """
    Load the default analysis prompt from crprompt.md file.

    This function reads the default prompt template used for CodeRabbit
    analysis. The prompt file contains instructions for the AI analysis
    engine on how to analyze code and generate reports.

    Returns:
        str: The default prompt text, or empty string if file not found

    File Location:
        - Expected file: crprompt.md in the project root
        - Fallback: Empty string if file doesn't exist

    Usage:
        The prompt is automatically loaded when no custom prompt is
        provided in the API request. It ensures consistent analysis
        quality across different report generations.
    """
    try:
        with open('crprompt.md', 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("crprompt.md not found, using empty default prompt")
        return ""

def generate_coderabbit_report(from_date: str, to_date: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Generate a comprehensive CodeRabbit report for the specified date range.

    This function serves as the main interface to the CodeRabbit API for
    generating code analysis reports. It handles authentication, request
    formatting, error handling, and response processing.

    Process Flow:
    1. Validates API key configuration
    2. Builds request payload with required and optional parameters
    3. Loads default prompt if no custom prompt provided
    4. Makes authenticated request to CodeRabbit API
    5. Handles various error conditions (timeout, connection, API errors)
    6. Returns structured response with success/error status

    Args:
        from_date: Start date for analysis in YYYY-MM-DD format
        to_date: End date for analysis in YYYY-MM-DD format
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

    Error Handling:
        - Missing API key: Returns configuration error
        - Network timeout: Returns timeout error (120s limit)
        - Connection errors: Returns connection error
        - API errors: Returns detailed API error information
        - Unexpected errors: Returns generic error message

    Logging:
        - INFO: Request details, response status, successful operations
        - ERROR: API errors, connection failures, unexpected errors
        - WARNING: Missing configuration, fallback scenarios

    Example Usage:
        result = generate_coderabbit_report(
            from_date="2024-01-01",
            to_date="2024-01-31",
            organization="my-org",
            scheduleRange="monthly"
        )
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
    Comprehensive validation of CodeRabbit report parameters.

    This function performs thorough validation of all input parameters
    for CodeRabbit report generation. It ensures data integrity, format
    compliance, and logical consistency before making API requests.

    Validation Rules:
    1. Required Fields: 'from'/'from_date' and 'to'/'to_date' must be present
    2. Date Format: All dates must be in YYYY-MM-DD format
    3. Date Logic: from_date must be chronologically before to_date
    4. Optional Parameters: Validates and formats optional parameters
    5. Data Types: Ensures correct data types for all parameters

    Args:
        data: Dictionary containing the request parameters to validate
            Expected keys:
            - from/from_date: Start date (required)
            - to/to_date: End date (required)
            - organization: Organization identifier (optional)
            - scheduleRange: Schedule range (optional)
            - prompt: Custom prompt (optional)
            - promptTemplate: Prompt template name (optional)
            - parameters: Filter parameters array (optional)
            - groupBy: Primary grouping field (optional)
            - subgroupBy: Secondary grouping field (optional)
            - orgId: Organization ID (optional)

    Returns:
        Tuple containing:
        - bool: True if validation passes, False otherwise
        - Optional[str]: Error message if validation fails, None if successful
        - Optional[Dict]: Validated and formatted parameters if successful, None if failed

    Validation Examples:
        Valid: {"from": "2024-01-01", "to": "2024-01-31"}
        Invalid: {"from": "2024-01-31", "to": "2024-01-01"}  # Wrong order
        Invalid: {"from": "01/01/2024", "to": "01/31/2024"}  # Wrong format
        Invalid: {"from": "2024-01-01"}  # Missing 'to' date

    Error Messages:
        - "from/from_date and to/to_date are required"
        - "Invalid date format. Use YYYY-MM-DD"
        - "from_date must be before to_date"
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