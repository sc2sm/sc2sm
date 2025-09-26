"""
CodeRabbit API integration service
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# CodeRabbit Configuration
CODERABBIT_API_KEY = os.getenv("CODERABBIT_API_KEY")
CODERABBIT_API_BASE = "https://api.coderabbit.ai/api/v1"


def generate_coderabbit_report(from_date, to_date, **kwargs):
    """
    Generate a CodeRabbit report with the specified parameters

    Args:
        from_date (str): Start date in YYYY-MM-DD format
        to_date (str): End date in YYYY-MM-DD format
        **kwargs: Additional CodeRabbit API parameters

    Returns:
        dict: API response or error information
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

    # Add optional parameters if provided
    optional_params = [
        "scheduleRange", "prompt", "promptTemplate", "parameters",
        "groupBy", "subgroupBy", "orgId"
    ]

    for param in optional_params:
        if param in kwargs and kwargs[param] is not None:
            payload[param] = kwargs[param]

    try:
        response = requests.post(
            f"{CODERABBIT_API_BASE}/report.generate",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return {"data": response.json(), "status": "success"}
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"message": response.text}
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


def validate_report_parameters(data):
    """
    Validate CodeRabbit report parameters

    Args:
        data (dict): Request data to validate

    Returns:
        tuple: (is_valid, error_message, validated_params)
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