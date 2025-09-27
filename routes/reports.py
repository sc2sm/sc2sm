"""
Report-related routes for CodeRabbit API integration.

This module provides Flask Blueprint routes for managing CodeRabbit reports
including generation, retrieval, listing, and metrics extraction. It handles
the complete lifecycle of code analysis reports from creation to storage.

Key Features:
- Asynchronous report generation with background processing
- Comprehensive parameter validation and error handling
- Database integration for report persistence
- Metrics extraction and structured storage
- RESTful API design with proper HTTP status codes

Routes:
- POST /reports/generate: Generate new CodeRabbit reports
- GET /reports/{id}: Retrieve specific report by ID
- GET /reports: List reports with filtering and pagination
- GET /reports/{id}/metrics: Get metrics for a specific report
- GET /reports/bottom5: Get the 5 most recent reports

Author: Source2Social Team
Version: 1.0.0
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from database.db import (
    init_database, save_report_to_db, get_report_by_id, list_reports,
    get_report_metrics, parse_and_store_metrics, get_db_connection
)

# Create Blueprint for reports routes with URL prefix
reports_bp = Blueprint('reports', __name__)


@reports_bp.route("/reports/generate", methods=["POST"])
def generate_report():
    """
    Generate a CodeRabbit report and store it in the database.

    This endpoint initiates a CodeRabbit code analysis request. It validates
    input parameters, generates the report using the CodeRabbit API, and
    stores the results in the database with proper error handling.

    Request Processing:
    1. Validates required parameters (from_date, to_date)
    2. Validates optional parameters and formats them for CodeRabbit API
    3. Calls CodeRabbit API to generate the report
    4. Stores successful reports with metrics extraction
    5. Stores failed reports with error messages
    6. Returns appropriate HTTP status codes and response data

    Expected JSON payload:
    {
        "from": "2024-05-01",                    # required: Start date (YYYY-MM-DD)
        "to": "2024-05-15",                      # required: End date (YYYY-MM-DD)
        "organization": "my-org",                # optional: Local organization identifier
        "scheduleRange": "string",               # optional: Schedule range
        "prompt": "string",                      # optional: Custom prompt
        "promptTemplate": "string",              # optional: Prompt template
        "parameters": [...],                     # optional: Array of filter parameters
        "groupBy": "string",                     # optional: Primary grouping
        "subgroupBy": "string",                  # optional: Secondary grouping
        "orgId": "string"                        # optional: Organization ID
    }

    Returns:
        JSON response with report ID, status, and metadata
        - 201 Created: Report generated successfully
        - 400 Bad Request: Invalid parameters
        - 500 Internal Server Error: CodeRabbit API error or system error
    """
    from services.coderabbit import generate_coderabbit_report, validate_report_parameters

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON payload is required"}), 400

    # Validate parameters
    is_valid, error_message, validated_params = validate_report_parameters(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    try:
        # Initialize database if not exists
        init_database()

        # Generate report from CodeRabbit
        result = generate_coderabbit_report(
            validated_params["from_date"],
            validated_params["to_date"],
            **validated_params["optional_params"]
        )

        if result["status"] == "error":
            # Save failed report to database
            report_id = save_report_to_db(
                organization=validated_params["organization"],
                from_date=validated_params["from_date"],
                to_date=validated_params["to_date"],
                report_data=None,
                status="failed",
                error_message=result["error"],
                **validated_params["optional_params"]
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
            organization=validated_params["organization"],
            from_date=validated_params["from_date"],
            to_date=validated_params["to_date"],
            report_data=report_data,
            status="completed",
            **validated_params["optional_params"]
        )

        # Parse and store metrics
        parse_and_store_metrics(report_id, report_data)

        return jsonify({
            "report_id": report_id,
            "status": "completed",
            "message": "Report generated successfully",
            "organization": validated_params["organization"],
            "from": validated_params["from_date"],
            "to": validated_params["to_date"],
            "parameters_used": validated_params["optional_params"],
            "created_at": datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@reports_bp.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    """
    Retrieve a specific report by its ID with associated metrics.

    This endpoint fetches a complete report record including all metadata,
    report data, and associated metrics. It's used for detailed report
    viewing and analysis.

    Args:
        report_id: Integer ID of the report to retrieve

    Returns:
        JSON response containing:
        - Complete report metadata (dates, parameters, status)
        - Full report data from CodeRabbit
        - Associated metrics extracted from the report
        - Error message if the report failed

    HTTP Status Codes:
        - 200 OK: Report found and returned successfully
        - 404 Not Found: Report with specified ID does not exist
        - 500 Internal Server Error: Database or system error
    """
    try:
        report = get_report_by_id(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404

        return jsonify(report)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@reports_bp.route("/reports", methods=["GET"])
def list_all_reports():
    """
    List all reports with comprehensive filtering and pagination support.

    This endpoint provides a flexible way to query reports with multiple
    filter options and pagination. It's designed for dashboard views,
    report management interfaces, and API integrations.

    Query Parameters:
        - organization (str): Filter by organization identifier
        - status (str): Filter by report status ("pending", "completed", "failed")
        - from_date (str): Filter reports created after this date (YYYY-MM-DD)
        - to_date (str): Filter reports created before this date (YYYY-MM-DD)
        - limit (int): Maximum number of results to return (default: 50, max: 100)
        - offset (int): Number of results to skip for pagination (default: 0)

    Returns:
        JSON response containing:
        - reports: Array of report objects with metadata
        - total_count: Total number of reports matching filters
        - limit: Applied limit parameter
        - offset: Applied offset parameter
        - has_more: Boolean indicating if more results are available

    Example Usage:
        GET /reports?organization=my-org&status=completed&limit=10&offset=0
        GET /reports?from_date=2024-01-01&to_date=2024-12-31

    HTTP Status Codes:
        - 200 OK: Reports retrieved successfully
        - 400 Bad Request: Invalid query parameters
        - 500 Internal Server Error: Database or system error
    """
    try:
        # Get query parameters
        organization = request.args.get("organization")
        status = request.args.get("status")
        from_date_filter = request.args.get("from_date")
        to_date_filter = request.args.get("to_date")

        try:
            limit = int(request.args.get("limit", 50))
            offset = int(request.args.get("offset", 0))
        except ValueError:
            return jsonify({"error": "limit and offset must be integers"}), 400

        result = list_reports(
            organization=organization,
            status=status,
            from_date_filter=from_date_filter,
            to_date_filter=to_date_filter,
            limit=limit,
            offset=offset
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@reports_bp.route("/reports/<int:report_id>/metrics", methods=["GET"])
def get_report_metrics_endpoint(report_id):
    """Get metrics for a specific report"""
    try:
        metrics = get_report_metrics(report_id)
        if not metrics:
            return jsonify({"error": "Report not found"}), 404

        return jsonify(metrics)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@reports_bp.route("/reports/bottom5", methods=["GET"])
def get_bottom_5_reports():
    """
    Get the bottom 5 reports from the database (most recent 5)
    
    Returns:
        JSON response with the 5 most recent reports
    """
    try:
        # Initialize database if not exists
        init_database()
        
        # Get total count first
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reports")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            return jsonify({
                "message": "No reports found in database",
                "total_count": 0,
                "reports": []
            })
        
        # Calculate offset to get bottom 5 (most recent)
        offset = max(0, total_count - 5)
        
        # Get the bottom 5 reports ordered by created_at DESC
        query = """
            SELECT id, organization, from_date, to_date, status, created_at, error_message
            FROM reports
            ORDER BY created_at DESC
            LIMIT 5 OFFSET ?
        """
        
        cursor.execute(query, (offset,))
        reports = cursor.fetchall()
        
        # Format the results
        formatted_reports = []
        for report in reports:
            formatted_reports.append({
                "id": report[0],
                "organization": report[1],
                "from_date": report[2],
                "to_date": report[3],
                "status": report[4],
                "created_at": report[5],
                "error_message": report[6]
            })
        
        conn.close()
        
        return jsonify({
            "message": f"Bottom 5 reports (most recent)",
            "total_count": total_count,
            "showing": len(formatted_reports),
            "reports": formatted_reports
        })
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500