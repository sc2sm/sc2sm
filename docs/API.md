# CodeRabbit Report API Documentation

## Overview

The CodeRabbit Report API is a Flask-based backend service that integrates with the CodeRabbit API to generate code review reports for GitHub repositories. It provides endpoints to generate, retrieve, and manage code review reports with persistent storage in SQLite.

## Base URL

```
http://localhost:5001
```

## Authentication

All API endpoints require a valid CodeRabbit API key configured via the `CODERABBIT_API_KEY` environment variable.

## Endpoints

### Health Check

#### GET /health

Check the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "service": "coderabbit-report-api"
}
```

**Example:**
```bash
curl "http://localhost:5001/health"
```

---

### Report Generation

#### POST /reports/generate

Generate a new CodeRabbit report and store it in the database.

**Request Body:**
```json
{
  "from": "2024-05-01",                    // required: Start date (YYYY-MM-DD)
  "to": "2024-05-15",                      // required: End date (YYYY-MM-DD)
  "organization": "my-org",                // optional: Local organization identifier
  "scheduleRange": "weekly",               // optional: Schedule range
  "prompt": "Custom analysis prompt",      // optional: Custom prompt
  "promptTemplate": "template_name",       // optional: Prompt template
  "parameters": [                          // optional: Array of filter parameters
    {
      "type": "repository",
      "value": "my-repo"
    }
  ],
  "groupBy": "repository",                 // optional: Primary grouping
  "subgroupBy": "author",                  // optional: Secondary grouping
  "orgId": "org-123"                       // optional: Organization ID
}
```

**Success Response (201):**
```json
{
  "report_id": 123,
  "status": "completed",
  "message": "Report generated successfully",
  "organization": "my-org",
  "from": "2024-05-01",
  "to": "2024-05-15",
  "parameters_used": {
    "scheduleRange": "weekly",
    "prompt": "Custom analysis prompt"
  },
  "created_at": "2024-05-15T10:30:00"
}
```

**Error Response (400):**
```json
{
  "error": "from/from_date and to/to_date are required"
}
```

**Error Response (500):**
```json
{
  "report_id": 123,
  "status": "failed",
  "error": "CodeRabbit API error: 401",
  "details": {
    "message": "Invalid API key"
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:5001/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "2024-05-01",
    "to": "2024-05-15",
    "organization": "my-org"
  }'
```

---

### Get Report

#### GET /reports/{report_id}

Retrieve a specific report by its ID.

**Path Parameters:**
- `report_id` (integer): The ID of the report to retrieve

**Success Response (200):**
```json
{
  "id": 123,
  "organization": "my-org",
  "from_date": "2024-05-01",
  "to_date": "2024-05-15",
  "status": "completed",
  "created_at": "2024-05-15T10:30:00",
  "report_data": {
    "total_reviews": 45,
    "total_comments": 120,
    "review_coverage": 85.5,
    "avg_review_time": "2.5 hours"
  },
  "metrics": [
    {
      "id": 1,
      "metric_name": "total_reviews",
      "metric_value": "45",
      "metadata": null
    }
  ]
}
```

**Error Response (404):**
```json
{
  "error": "Report not found"
}
```

**Example:**
```bash
curl "http://localhost:5001/reports/123"
```

---

### List Reports

#### GET /reports

List all reports with optional filtering and pagination.

**Query Parameters:**
- `organization` (string, optional): Filter by organization
- `status` (string, optional): Filter by status (`pending`, `completed`, `failed`)
- `from_date` (string, optional): Filter reports generated after this date
- `to_date` (string, optional): Filter reports generated before this date
- `limit` (integer, optional): Limit number of results (default: 50)
- `offset` (integer, optional): Offset for pagination (default: 0)

**Success Response (200):**
```json
{
  "reports": [
    {
      "id": 123,
      "organization": "my-org",
      "from_date": "2024-05-01",
      "to_date": "2024-05-15",
      "status": "completed",
      "created_at": "2024-05-15T10:30:00",
      "error_message": null
    }
  ],
  "total_count": 1,
  "limit": 50,
  "offset": 0,
  "has_more": false
}
```

**Example:**
```bash
curl "http://localhost:5001/reports?organization=my-org&status=completed&limit=10"
```

---

### Get Report Metrics

#### GET /reports/{report_id}/metrics

Retrieve metrics for a specific report.

**Path Parameters:**
- `report_id` (integer): The ID of the report

**Success Response (200):**
```json
{
  "report_id": 123,
  "metrics": {
    "total_reviews": {
      "value": "45",
      "metadata": null
    },
    "total_comments": {
      "value": "120",
      "metadata": null
    },
    "metadata": {
      "value": "json",
      "metadata": {
        "additional_data": "value"
      }
    }
  }
}
```

**Error Response (404):**
```json
{
  "error": "Report not found"
}
```

**Example:**
```bash
curl "http://localhost:5001/reports/123/metrics"
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

All error responses include an `error` field with a descriptive message:

```json
{
  "error": "Error description"
}
```

## Rate Limiting

The API respects CodeRabbit's rate limits. If you encounter rate limiting, the API will return appropriate error messages.

## Data Models

### Report

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique report identifier |
| `organization` | string | Organization identifier |
| `from_date` | string | Start date (YYYY-MM-DD) |
| `to_date` | string | End date (YYYY-MM-DD) |
| `status` | string | Report status (`pending`, `completed`, `failed`) |
| `created_at` | timestamp | Creation timestamp |
| `report_data` | object | Report data from CodeRabbit |
| `error_message` | string | Error message if failed |

### Report Metrics

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique metric identifier |
| `report_id` | integer | Associated report ID |
| `metric_name` | string | Name of the metric |
| `metric_value` | string | Value of the metric |
| `metadata` | object | Additional metadata |

## Examples

### Complete Workflow

1. **Generate a report:**
```bash
curl -X POST "http://localhost:5001/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "2024-05-01",
    "to": "2024-05-15",
    "organization": "my-org",
    "scheduleRange": "weekly"
  }'
```

2. **Check report status:**
```bash
curl "http://localhost:5001/reports/123"
```

3. **Get report metrics:**
```bash
curl "http://localhost:5001/reports/123/metrics"
```

4. **List all reports:**
```bash
curl "http://localhost:5001/reports?organization=my-org"
```
