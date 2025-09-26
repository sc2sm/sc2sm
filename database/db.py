"""
Database operations for CodeRabbit reports
"""

import os
import sqlite3
import json
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "reports.db")


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
            schedule_range TEXT,
            prompt TEXT,
            prompt_template TEXT,
            parameters TEXT,
            group_by TEXT,
            subgroup_by TEXT,
            org_id TEXT,
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


def save_report_to_db(organization, from_date, to_date, report_data, status="completed", error_message=None, **kwargs):
    """
    Save a report to the database

    Args:
        organization (str): Organization identifier
        from_date (str): Start date
        to_date (str): End date
        report_data (dict): Report data from CodeRabbit
        status (str): Report status
        error_message (str): Error message if any
        **kwargs: Additional parameters used in the request

    Returns:
        int: Report ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (
            organization, from_date, to_date, schedule_range, prompt, prompt_template,
            parameters, group_by, subgroup_by, org_id, status, report_data, error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        organization,
        from_date,
        to_date,
        kwargs.get("scheduleRange"),
        kwargs.get("prompt"),
        kwargs.get("promptTemplate"),
        json.dumps(kwargs.get("parameters")) if kwargs.get("parameters") else None,
        kwargs.get("groupBy"),
        kwargs.get("subgroupBy"),
        kwargs.get("orgId"),
        status,
        json.dumps(report_data, default=json_serializer) if report_data else None,
        error_message
    ))

    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return report_id


def get_report_by_id(report_id):
    """Get a specific report by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()

    if not report:
        conn.close()
        return None

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

    return report_dict


def list_reports(organization=None, status=None, from_date_filter=None, to_date_filter=None, limit=50, offset=0):
    """
    List reports with optional filtering

    Args:
        organization (str): Filter by organization
        status (str): Filter by status
        from_date_filter (str): Filter reports generated after this date
        to_date_filter (str): Filter reports generated before this date
        limit (int): Limit number of results
        offset (int): Offset for pagination

    Returns:
        dict: Reports list with pagination info
    """
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

    return {
        "reports": [dict(report) for report in reports],
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total_count
    }


def get_report_metrics(report_id):
    """Get metrics for a specific report"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify report exists
    cursor.execute("SELECT id FROM reports WHERE id = ?", (report_id,))
    if not cursor.fetchone():
        conn.close()
        return None

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

    return {
        "report_id": report_id,
        "metrics": metrics_dict
    }


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