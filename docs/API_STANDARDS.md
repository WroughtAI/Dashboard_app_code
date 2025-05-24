# API Standards for Scaffold Integration

This document outlines the API standards and conventions that your service should follow for successful integration with the scaffold framework.

## General API Design Principles

1. **RESTful Design**: Follow RESTful principles for API design
2. **JSON Response Format**: All responses should be in JSON format
3. **HTTP Status Codes**: Use appropriate HTTP status codes
4. **Versioning**: Include API version in URL or header
5. **Documentation**: Document all endpoints with OpenAPI/Swagger

## Required Endpoints

### Health Check Endpoint

Every service must implement a health check endpoint:

```
GET /health
```

**Response Format**:
```json
{
  "status": "healthy",
  "service": "your-service-name",
  "version": "1.0.0"
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy

### File Upload Endpoint (if applicable)

If your service processes files, implement a file upload endpoint:

```
POST /upload
```

**Request Format**:
- `multipart/form-data` with:
  - `file`: The file to upload
  - `options`: Optional JSON string with processing parameters

**Response Format**:
```json
{
  "status": "success",
  "service": "your-service-name",
  "filename": "uploaded-file.csv",
  "results": [
    // Processing results specific to your service
  ]
}
```

**Status Codes**:
- `200 OK`: File processed successfully
- `400 Bad Request`: Invalid request or file format
- `422 Unprocessable Entity`: File cannot be processed
- `500 Internal Server Error`: Server error

## Standard Response Format

All API responses should follow this format:

```json
{
  "status": "success|error",
  "service": "your-service-name",
  "results": [...],  // For successful requests
  "error": "Error message",  // For error responses
  "details": {}  // Optional error details
}
```

### Success Response

```json
{
  "status": "success",
  "service": "your-service-name",
  "results": [
    {
      "id": "123",
      "name": "Example Result",
      "value": 42
    }
  ]
}
```

### Error Response

```json
{
  "status": "error",
  "service": "your-service-name",
  "error": "Invalid input parameters",
  "details": {
    "field": "param1",
    "reason": "Value must be a positive integer"
  }
}
```

## Authentication & Authorization

If your service requires authentication:

1. **Bearer Token**: Use Bearer token authentication
2. **Authorization Header**: Include token in the Authorization header
3. **Proper Error Codes**: Return 401/403 for auth errors

Example:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Error Handling

### Error Response Format

```json
{
  "status": "error",
  "service": "your-service-name",
  "error": "Brief error message",
  "details": {
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "field": "field_name",  // If applicable
    "suggestion": "How to fix"  // Optional
  }
}
```

### Common HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Not authorized
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Valid request but cannot process
- `500 Internal Server Error`: Server error

## Rate Limiting

If your service implements rate limiting:

1. **Headers**: Include rate limit headers
2. **Status Code**: Return 429 Too Many Requests

Example headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1626384000
```

## Versioning

Version your API using one of these methods:

1. **URL Path**: `/api/v1/resource`
2. **Query Parameter**: `/api/resource?version=1`
3. **Accept Header**: `Accept: application/vnd.api+json;version=1`

## CORS Configuration

Configure CORS to allow requests from the scaffold framework:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://scaffold-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## OpenAPI Documentation

Document your API using OpenAPI/Swagger:

```python
app = FastAPI(
    title="Your Service API",
    description="API for Your Service that integrates with the Scaffold Framework",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

## Implementation Examples

### FastAPI Example

```python
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List

app = FastAPI(
    title="Example Service API",
    description="Example service API that integrates with the Scaffold Framework",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "example-service",
        "version": "1.0.0",
    }

@app.post("/your-endpoint")
async def your_endpoint(param1: str) -> Dict[str, Any]:
    """Example endpoint."""
    try:
        # Your service logic here
        result = {
            "status": "success",
            "service": "example-service",
            "results": [
                {
                    "id": "123",
                    "name": param1,
                    "processed": True
                }
            ]
        }
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "service": "example-service",
                "error": str(e)
            }
        )
```

## Testing Your API

Use these curl commands to test your API:

```bash
# Health check
curl -X GET http://localhost:8000/health

# Example endpoint
curl -X POST -H "Content-Type: application/json" \
  -d '{"param1": "test"}' \
  http://localhost:8000/your-endpoint

# File upload
curl -X POST http://localhost:8000/upload \
  -F "file=@./test_file.csv" \
  -F "options={\"option1\": true}"
``` 