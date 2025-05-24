import pytest
import json
import os
import sys
import re
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# Add the parent directory to sys.path to import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../examples/example_service')))

try:
    from app import app
except ImportError as e:
    pytest.skip(f"Failed to import app: {e}", allow_module_level=True)

# Test API standards compliance
def test_api_has_health_endpoint():
    """Verify that the API has a /health endpoint"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    paths = openapi_schema.get("paths", {})
    assert "/health" in paths, "API must have a /health endpoint"
    assert "get" in paths["/health"], "Health endpoint must support GET method"

def test_api_returns_consistent_response_format():
    """Verify API endpoints follow consistent response format"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Check for consistent response format in all endpoints
    paths = openapi_schema.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue
                
            responses = details.get("responses", {})
            success_response = responses.get("200", {})
            
            # Skip if no 200 response defined
            if not success_response:
                continue
                
            # Get response schema
            content = success_response.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            
            # Check if schema uses references
            if "$ref" in schema:
                # We'll skip detailed validation of referenced schemas for simplicity
                continue
                
            # For direct schemas, check for common fields
            properties = schema.get("properties", {})
            
            # Most REST APIs should return consistent response formats
            # Here we're checking for common field patterns
            assert any(field in properties for field in ["status", "data", "results", "message", "service"]), \
                f"Endpoint {path} {method} should have a consistent response format"

def test_api_version_in_response():
    """Verify the API includes version information in responses"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check if version is included in response
    assert "version" in data, "API responses should include version information"

def test_api_documentation():
    """Verify API has proper documentation"""
    # Check app title and description
    assert app.title, "API must have a title"
    assert app.version, "API must have a version"
    assert app.description, "API must have a description"
    
    # Check route documentation
    for route in app.routes:
        if hasattr(route, "endpoint") and route.path != "/openapi.json" and route.path != "/docs" and route.path != "/redoc":
            # Get the function object
            function = route.endpoint
            
            # Check if the function has a docstring
            assert function.__doc__, f"Endpoint {route.path} must have documentation"

def test_api_error_handling():
    """Test proper error handling in API endpoints"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test with invalid data for the /upload endpoint (missing required file)
    response = client.post("/upload", files={}, data={})
    assert response.status_code != 500, "API should not return 500 for invalid input"
    assert response.status_code in [400, 422], "API should return 400 or 422 for invalid input"
    
    # Test with invalid data for get-stats endpoint
    response = client.post("/get-stats", json="not_a_list")
    assert response.status_code != 500, "API should not return 500 for invalid input"
    assert response.status_code in [400, 422], "API should return 400 or 422 for invalid input"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 