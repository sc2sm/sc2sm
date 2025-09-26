"""
Flask backend for GitHub OAuth Device Flow
"""

import os
import requests
import time
import sqlite3
import json
from datetime import datetime, date
from flask import Flask, request, jsonify, session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_DEVICE_ENDPOINT = "https://github.com/login/device/code"
GITHUB_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"

# CodeRabbit Configuration
CODERABBIT_API_KEY = os.getenv("CODERABBIT_API_KEY")
CODERABBIT_API_BASE = "https://api.coderabbit.ai/api/v1"

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "reports.db")

# In-memory storage for device codes (in production, use Redis or database)
device_codes = {}


def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization TEXT,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report_data TEXT,
            error_message TEXT
        )
    """)

    # Create report_metrics table for structured data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value TEXT,
            metadata TEXT,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    """)

    conn.commit()
    conn.close()


def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn


def json_serializer(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def generate_coderabbit_report(from_date, to_date):
    """
    Generate a CodeRabbit report for the specified date range

    Args:
        from_date (str): Start date in YYYY-MM-DD format
        to_date (str): End date in YYYY-MM-DD format

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

    payload = {
        "from": from_date,
        "to": to_date
    }

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


def save_report_to_db(organization, from_date, to_date, report_data, status="completed", error_message=None):
    """
    Save a report to the database

    Args:
        organization (str): Organization identifier
        from_date (str): Start date
        to_date (str): End date
        report_data (dict): Report data from CodeRabbit
        status (str): Report status
        error_message (str): Error message if any

    Returns:
        int: Report ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (organization, from_date, to_date, status, report_data, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        organization,
        from_date,
        to_date,
        status,
        json.dumps(report_data, default=json_serializer) if report_data else None,
        error_message
    ))

    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return report_id


def parse_and_store_metrics(report_id, report_data):
    """
    Parse report data and store metrics in the database

    Args:
        report_id (int): Report ID
        report_data (dict): Report data to parse
    """
    if not report_data:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Extract common metrics from the report
    # Note: This will depend on the actual structure of CodeRabbit reports
    metrics_to_extract = [
        "total_reviews",
        "total_comments",
        "review_coverage",
        "avg_review_time",
        "total_files_reviewed",
        "total_pull_requests"
    ]

    for metric_name in metrics_to_extract:
        if metric_name in report_data:
            cursor.execute("""
                INSERT INTO report_metrics (report_id, metric_name, metric_value)
                VALUES (?, ?, ?)
            """, (report_id, metric_name, str(report_data[metric_name])))

    # Store any nested data as JSON metadata
    if "metadata" in report_data:
        cursor.execute("""
            INSERT INTO report_metrics (report_id, metric_name, metric_value, metadata)
            VALUES (?, ?, ?, ?)
        """, (report_id, "metadata", "json", json.dumps(report_data["metadata"], default=json_serializer)))

    conn.commit()
    conn.close()


@app.route("/auth/device", methods=["POST"])
def initiate_device_flow():
    """
    Initiate GitHub OAuth Device Flow
    
    Requests a device code from GitHub with repo scope.
    Returns user_code, verification_uri, expires_in, and interval.
    """
    
    # Check if GitHub client ID is configured
    if not GITHUB_CLIENT_ID:
        return jsonify({"error": "GITHUB_CLIENT_ID not configured"}), 500
    
    try:
        # Prepare request payload for GitHub device flow
        payload = {
            "client_id": GITHUB_CLIENT_ID,
            "scope": "repo"  # Request repository access
        }
        
        # Make request to GitHub device endpoint
        response = requests.post(
            GITHUB_DEVICE_ENDPOINT,
            json=payload,
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Extract required fields
        device_code = data.get("device_code")
        user_code = data.get("user_code")
        verification_uri = data.get("verification_uri")
        verification_uri_complete = data.get("verification_uri_complete")
        expires_in = data.get("expires_in")
        interval = data.get("interval")
        
        # Validate required fields
        if not all([device_code, user_code, verification_uri, expires_in, interval]):
            return jsonify({"error": "Invalid response from GitHub"}), 500
        
        # Store device code in memory with expiration
        device_codes[device_code] = {
            "created_at": time.time(),
            "expires_in": expires_in,
            "interval": interval,
            "status": "pending"
        }
        
        # Return the information needed for user authorization
        return jsonify({
            "user_code": user_code,
            "verification_uri": verification_uri,
            "verification_uri_complete": verification_uri_complete,
            "expires_in": expires_in,
            "interval": interval,
            "device_code": device_code  # Include for polling
        })
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to GitHub timed out"}), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Failed to connect to GitHub"}), 503
        
    except requests.exceptions.HTTPError as e:
        error_message = f"GitHub API error: {e.response.status_code}"
        try:
            error_details = e.response.json()
            error_message += f" - {error_details.get('error_description', 'Unknown error')}"
        except:
            error_message += f" - {e.response.text}"
        
        return jsonify({"error": error_message}), e.response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/auth/poll", methods=["POST"])
def poll_for_token():
    """
    Poll GitHub for access token using device code
    
    Checks if the user has authorized the device and returns access_token.
    """
    
    # Get device_code from request
    data = request.get_json()
    if not data or "device_code" not in data:
        return jsonify({"error": "device_code is required"}), 400
    
    device_code = data["device_code"]
    
    # Check if device code exists in our storage
    if device_code not in device_codes:
        return jsonify({"error": "Invalid or expired device_code"}), 400
    
    device_info = device_codes[device_code]
    
    # Check if device code has expired
    current_time = time.time()
    if current_time - device_info["created_at"] > device_info["expires_in"]:
        # Clean up expired device code
        del device_codes[device_code]
        return jsonify({"error": "Device code has expired"}), 400
    
    try:
        # Prepare request payload for token endpoint
        payload = {
            "client_id": GITHUB_CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        }
        
        # Make request to GitHub token endpoint
        response = requests.post(
            GITHUB_TOKEN_ENDPOINT,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        # Parse the response
        response_data = response.json()
        
        # Check for authorization pending
        if response.status_code == 400 and response_data.get("error") == "authorization_pending":
            return jsonify({
                "status": "pending",
                "message": "User has not yet authorized the device"
            }), 202
        
        # Check for slow down
        if response.status_code == 400 and response_data.get("error") == "slow_down":
            return jsonify({
                "status": "slow_down",
                "message": "Polling too frequently, please wait longer"
            }), 429
        
        # Check for access denied
        if response.status_code == 400 and response_data.get("error") == "access_denied":
            # Clean up device code
            del device_codes[device_code]
            return jsonify({
                "status": "denied",
                "message": "User denied the authorization request"
            }), 403
        
        # Check for expired token
        if response.status_code == 400 and response_data.get("error") == "expired_token":
            # Clean up device code
            del device_codes[device_code]
            return jsonify({
                "status": "expired",
                "message": "Device code has expired"
            }), 400
        
        # Check if request was successful
        response.raise_for_status()
        
        # Extract access token
        access_token = response_data.get("access_token")
        if not access_token:
            return jsonify({"error": "No access token in response"}), 500
        
        # Clean up device code after successful authorization
        del device_codes[device_code]
        
        # Return the access token
        return jsonify({
            "status": "success",
            "access_token": access_token,
            "token_type": response_data.get("token_type", "bearer"),
            "scope": response_data.get("scope", "repo")
        })
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to GitHub timed out"}), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Failed to connect to GitHub"}), 503
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/auth/status/<device_code>", methods=["GET"])
def get_device_status(device_code):
    """
    Get the status of a device code (optional endpoint for checking status)
    """
    
    if device_code not in device_codes:
        return jsonify({"error": "Device code not found"}), 404
    
    device_info = device_codes[device_code]
    current_time = time.time()
    
    # Check if expired
    if current_time - device_info["created_at"] > device_info["expires_in"]:
        del device_codes[device_code]
        return jsonify({"error": "Device code has expired"}), 400
    
    return jsonify({
        "status": device_info["status"],
        "expires_in": device_info["expires_in"] - (current_time - device_info["created_at"]),
        "interval": device_info["interval"]
    })


@app.route("/reports/generate", methods=["POST"])
def generate_report():
    """
    Generate a CodeRabbit report and store it in the database

    Expected JSON payload:
    {
        "from_date": "2024-05-01",
        "to_date": "2024-05-15",
        "organization": "my-org" (optional)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON payload is required"}), 400

    # Validate required fields
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    organization = data.get("organization", "default")

    if not from_date or not to_date:
        return jsonify({"error": "from_date and to_date are required"}), 400

    # Validate date format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Validate date range
    if from_date >= to_date:
        return jsonify({"error": "from_date must be before to_date"}), 400

    try:
        # Initialize database if not exists
        init_database()

        # Generate report from CodeRabbit
        result = generate_coderabbit_report(from_date, to_date)

        if result["status"] == "error":
            # Save failed report to database
            report_id = save_report_to_db(
                organization=organization,
                from_date=from_date,
                to_date=to_date,
                report_data=None,
                status="failed",
                error_message=result["error"]
            )

            return jsonify({
                "report_id": report_id,
                "status": "failed",
                "error": result["error"],
                "details": result.get("details")
            }), 500

        # Save successful report to database
        report_data = result["data"]
        report_id = save_report_to_db(
            organization=organization,
            from_date=from_date,
            to_date=to_date,
            report_data=report_data,
            status="completed"
        )

        # Parse and store metrics
        parse_and_store_metrics(report_id, report_data)

        return jsonify({
            "report_id": report_id,
            "status": "completed",
            "message": "Report generated successfully",
            "organization": organization,
            "from_date": from_date,
            "to_date": to_date,
            "created_at": datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    """
    Get a specific report by ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()

        if not report:
            return jsonify({"error": "Report not found"}), 404

        # Get associated metrics
        cursor.execute("SELECT * FROM report_metrics WHERE report_id = ?", (report_id,))
        metrics = cursor.fetchall()

        conn.close()

        # Convert report data to dict
        report_dict = dict(report)
        if report_dict["report_data"]:
            report_dict["report_data"] = json.loads(report_dict["report_data"])

        # Add metrics to response
        report_dict["metrics"] = [dict(metric) for metric in metrics]

        return jsonify(report_dict)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/reports", methods=["GET"])
def list_reports():
    """
    List all reports with optional filtering

    Query parameters:
    - organization: Filter by organization
    - status: Filter by status (pending, completed, failed)
    - from_date: Filter reports generated after this date
    - to_date: Filter reports generated before this date
    - limit: Limit number of results (default 50)
    - offset: Offset for pagination (default 0)
    """
    try:
        # Get query parameters
        organization = request.args.get("organization")
        status = request.args.get("status")
        from_date_filter = request.args.get("from_date")
        to_date_filter = request.args.get("to_date")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build dynamic query
        where_clauses = []
        params = []

        if organization:
            where_clauses.append("organization = ?")
            params.append(organization)

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        if from_date_filter:
            where_clauses.append("created_at >= ?")
            params.append(from_date_filter)

        if to_date_filter:
            where_clauses.append("created_at <= ?")
            params.append(to_date_filter)

        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Get total count
        count_query = f"SELECT COUNT(*) FROM reports{where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Get reports
        query = f"""
            SELECT id, organization, from_date, to_date, status, created_at, error_message
            FROM reports
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        reports = cursor.fetchall()

        conn.close()

        return jsonify({
            "reports": [dict(report) for report in reports],
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        })

    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/reports/<int:report_id>/metrics", methods=["GET"])
def get_report_metrics(report_id):
    """
    Get metrics for a specific report
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify report exists
        cursor.execute("SELECT id FROM reports WHERE id = ?", (report_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Report not found"}), 404

        # Get metrics
        cursor.execute("""
            SELECT metric_name, metric_value, metadata
            FROM report_metrics
            WHERE report_id = ?
            ORDER BY metric_name
        """, (report_id,))
        metrics = cursor.fetchall()

        conn.close()

        metrics_dict = {}
        for metric in metrics:
            metric_dict = dict(metric)
            if metric_dict["metadata"]:
                try:
                    metric_dict["metadata"] = json.loads(metric_dict["metadata"])
                except json.JSONDecodeError:
                    pass
            metrics_dict[metric_dict["metric_name"]] = {
                "value": metric_dict["metric_value"],
                "metadata": metric_dict["metadata"]
            }

        return jsonify({
            "report_id": report_id,
            "metrics": metrics_dict
        })

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "github-oauth-device-flow-with-coderabbit",
        "active_device_codes": len(device_codes)
    })


if __name__ == "__main__":
    # Development server
    app.run(debug=True, host="0.0.0.0", port=5000)
