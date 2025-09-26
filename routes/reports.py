"""
Report-related routes for CodeRabbit API
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from services.coderabbit import generate_coderabbit_report, validate_report_parameters
from database.db import (
    init_database, save_report_to_db, get_report_by_id, list_reports,
    get_report_metrics, parse_and_store_metrics
)

# Create Blueprint for reports routes
reports_bp = Blueprint('reports', __name__)


@reports_bp.route("/reports/generate", methods=["POST"])
def generate_report():
    """
    Generate a CodeRabbit report and store it in the database

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
    """
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
    """Get a specific report by ID"""
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