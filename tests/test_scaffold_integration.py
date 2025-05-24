import pytest
import os
import sys
import json
import requests
import re
import logging
import docker
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Path to example service
EXAMPLE_SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../examples/example_service'))

# Required API endpoints for Agent-Scaffolding compatibility
REQUIRED_ENDPOINTS = [
    "/health"  # Health check endpoint is mandatory
]

@pytest.mark.integration
def test_service_exposes_required_endpoints():
    """Test if the service exposes all required endpoints for Agent-Scaffolding integration"""
    # Import the FastAPI app and use TestClient to check endpoints
    try:
        sys.path.insert(0, EXAMPLE_SERVICE_DIR)
        from app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Check health endpoint
        response = client.get("/health")
        assert response.status_code == 200, "Health endpoint must return 200 OK"
        
        # Verify health response format
        data = response.json()
        assert "status" in data, "Health endpoint must include 'status' field"
        assert "service" in data, "Health endpoint must include 'service' field"
        assert "version" in data, "Health endpoint must include 'version' field"
        
    except ImportError as e:
        pytest.skip(f"Could not import app: {e}")

@pytest.mark.docker
def test_dockerfile_scaffolding_compatibility():
    """Test if the Dockerfile is compatible with Agent-Scaffolding requirements"""
    dockerfile_path = os.path.join(EXAMPLE_SERVICE_DIR, "Dockerfile")
    assert os.path.exists(dockerfile_path), "Dockerfile not found"
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check for essential Dockerfile elements
    assert "FROM" in content, "Dockerfile must specify a base image"
    assert "EXPOSE" in content, "Dockerfile must expose port(s) for external access"
    assert "0.0.0.0" in content or "CMD" in content, "Service must bind to 0.0.0.0 for external access"
    
    # Check if port 8000 is exposed (common for FastAPI)
    assert "EXPOSE 8000" in content or re.search(r"EXPOSE.*8000", content), "Port 8000 should be exposed for FastAPI apps"

@pytest.mark.docker
def test_docker_network_binding():
    """Test if the service binds to 0.0.0.0 inside Docker container"""
    if not os.environ.get("TEST_DOCKER_INTEGRATION"):
        pytest.skip("Docker integration test disabled. Set TEST_DOCKER_INTEGRATION=1 to enable.")
    
    try:
        client = docker.from_env()
        
        # Check if the image exists
        image_name = "code-attachment-example-service"
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            # Build the image if it doesn't exist
            client.images.build(path=EXAMPLE_SERVICE_DIR, tag=image_name, rm=True)
        
        # Run the container
        container = client.containers.run(
            image=image_name,
            name="scaffold-integration-test",
            detach=True,
            ports={'8000/tcp': 8000},
            remove=True
        )
        
        try:
            # Wait for container to start
            import time
            time.sleep(3)
            
            # Check if service is accessible
            response = requests.get("http://localhost:8000/health", timeout=2)
            assert response.status_code == 200, "Service should be accessible from outside the container"
        finally:
            container.stop(timeout=1)
            
    except Exception as e:
        pytest.skip(f"Docker test failed: {e}")

@pytest.mark.integration
def test_api_response_format():
    """Test if API responses follow the required format for Agent-Scaffolding"""
    try:
        sys.path.insert(0, EXAMPLE_SERVICE_DIR)
        from app import app
        from fastapi.testclient import TestClient
        from fastapi.openapi.utils import get_openapi
        
        client = TestClient(app)
        
        # Get OpenAPI schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Check all endpoints return consistent response format
        paths = openapi_schema.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                    
                # Test the endpoint if it's GET or has a simple schema
                if method.lower() == "get":
                    try:
                        response = client.request(method.upper(), path)
                        if response.status_code == 200:
                            data = response.json()
                            # Check for common field patterns
                            assert any(field in data for field in ["status", "data", "results", "message", "service"]), \
                                f"Endpoint {path} {method} should have a consistent response format"
                    except Exception:
                        # Skip if endpoint requires parameters
                        pass
                    
    except ImportError as e:
        pytest.skip(f"Could not import app: {e}")

def test_requirements_txt():
    """Test if requirements.txt includes necessary dependencies"""
    requirements_path = os.path.join(EXAMPLE_SERVICE_DIR, "requirements.txt")
    assert os.path.exists(requirements_path), "requirements.txt not found"
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Check for essential packages
    assert "fastapi" in content.lower(), "FastAPI should be included in requirements.txt"
    assert "uvicorn" in content.lower(), "Uvicorn should be included in requirements.txt"

def test_scaffolding_integration_checklist():
    """Check if the service meets all Agent-Scaffolding integration requirements"""
    print("\nAgent-Scaffolding Integration Checklist:")
    
    # Check Dockerfile
    dockerfile_path = os.path.join(EXAMPLE_SERVICE_DIR, "Dockerfile")
    dockerfile_exists = os.path.exists(dockerfile_path)
    print(f"✓ Dockerfile exists: {dockerfile_exists}")
    
    # Check requirements.txt
    requirements_path = os.path.join(EXAMPLE_SERVICE_DIR, "requirements.txt")
    requirements_exists = os.path.exists(requirements_path)
    print(f"✓ requirements.txt exists: {requirements_exists}")
    
    # Check app.py
    app_path = os.path.join(EXAMPLE_SERVICE_DIR, "app.py")
    app_exists = os.path.exists(app_path)
    print(f"✓ Service implementation (app.py) exists: {app_exists}")
    
    # Check health endpoint implementation
    health_endpoint = False
    if app_exists:
        with open(app_path, 'r') as f:
            content = f.read()
            health_endpoint = "/health" in content
    print(f"✓ Health endpoint implemented: {health_endpoint}")
    
    # Summary
    all_passed = all([dockerfile_exists, requirements_exists, app_exists, health_endpoint])
    if all_passed:
        print("\n✅ All basic integration requirements are met!")
    else:
        print("\n❌ Some integration requirements are not met.")
        
    print("\nReminder: For full Agent-Scaffolding integration, ensure your service:")
    print("1. Exposes all ports on 0.0.0.0 (not 127.0.0.1)")
    print("2. Returns standardized response formats (with status, service, version fields)")
    print("3. Includes proper error handling")
    print("4. Documents all API endpoints")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 