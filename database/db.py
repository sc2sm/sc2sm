"""
Database operations for CodeRabbit reports

This module provides functions for managing SQLite database operations including:
- Database initialization and schema creation
- Report storage and retrieval
- Metrics parsing and storage
- Query operations with filtering and pagination
"""

import os
import sqlite3
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/reports.db" if os.getenv("VERCEL") else "reports.db")


def init_database() -> None:
    """
    Initialize the SQLite database with required tables.

    Creates the following tables if they don't exist:
    - reports: Main table for storing report metadata and data
    - report_metrics: Table for storing structured metrics extracted from reports

    The function is idempotent and can be called multiple times safely.
    """
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


def get_db_connection() -> sqlite3.Connection:
    """
    Get a database connection with row factory enabled.
    
    Returns:
        sqlite3.Connection: Database connection with row factory for named column access
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn


def json_serializer(obj: Any) -> str:
    """
    JSON serializer for datetime objects.
    
    Args:
        obj: Object to serialize
        
    Returns:
        str: ISO format string for datetime objects
        
    Raises:
        TypeError: If object type is not supported
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def save_report_to_db(organization: str, from_date: str, to_date: str, 
                     report_data: Optional[Dict[str, Any]], status: str = "completed", 
                     error_message: Optional[str] = None, **kwargs: Any) -> int:
    """
    Save a report to the database.

    Args:
        organization: Organization identifier
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        report_data: Report data from CodeRabbit (can be None for failed reports)
        status: Report status (default: "completed")
        error_message: Error message if report generation failed
        **kwargs: Additional parameters used in the request including:
            - scheduleRange: Schedule range
            - prompt: Custom prompt
            - promptTemplate: Prompt template
            - parameters: Filter parameters
            - groupBy: Primary grouping
            - subgroupBy: Secondary grouping
            - orgId: Organization ID

    Returns:
        int: The ID of the created report record
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