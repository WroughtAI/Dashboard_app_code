import pytest
import os
import subprocess
import time
import requests
import docker
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to example service
EXAMPLE_SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../examples/example_service'))

# Docker image name
IMAGE_NAME = "code-attachment-example-service"
CONTAINER_NAME = "code-attachment-test-container"

# Check if docker is available
def is_docker_available():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except:
        return False

# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not is_docker_available(), reason="Docker not available")

@pytest.fixture(scope="module")
def docker_image():
    """Build the Docker image for testing"""
    if not is_docker_available():
        pytest.skip("Docker not available")
        
    logger.info(f"Building Docker image: {IMAGE_NAME}")
    
    # Build the image
    try:
        client = docker.from_env()
        image, logs = client.images.build(
            path=EXAMPLE_SERVICE_DIR,
            tag=IMAGE_NAME,
            rm=True
        )
        return image.id
    except Exception as e:
        logger.error(f"Failed to build Docker image: {e}")
        pytest.fail(f"Failed to build Docker image: {e}")

@pytest.fixture(scope="module")
def docker_container(docker_image):
    """Start the Docker container for testing"""
    if not docker_image:
        pytest.skip("Docker image not available")
    
    # Check if container already exists and remove it
    client = docker.from_env()
    try:
        container = client.containers.get(CONTAINER_NAME)
        logger.info(f"Removing existing container: {CONTAINER_NAME}")
        container.remove(force=True)
    except docker.errors.NotFound:
        pass
    
    # Start the container
    logger.info(f"Starting container: {CONTAINER_NAME}")
    container = client.containers.run(
        image=IMAGE_NAME,
        name=CONTAINER_NAME,
        detach=True,
        ports={'8000/tcp': 8000},
        remove=True
    )
    
    # Wait for container to start
    max_retries = 30
    retry_interval = 1
    
    for i in range(max_retries):
        try:
            # Check if container is running
            container.reload()
            if container.status != 'running':
                if i == max_retries - 1:
                    pytest.fail(f"Container failed to start: {container.status}")
                time.sleep(retry_interval)
                continue
                
            # Check if service is responding
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            if i == max_retries - 1:
                pytest.fail("Container started but service is not responding")
            time.sleep(retry_interval)
    
    # Yield the container for tests
    yield container
    
    # Cleanup
    logger.info(f"Stopping container: {CONTAINER_NAME}")
    try:
        container.stop(timeout=10)
    except Exception as e:
        logger.error(f"Error stopping container: {e}")

def test_dockerfile_exists():
    """Test that Dockerfile exists in example service directory"""
    dockerfile_path = os.path.join(EXAMPLE_SERVICE_DIR, "Dockerfile")
    assert os.path.exists(dockerfile_path), "Dockerfile not found in example service directory"
    
    # Check Dockerfile content
    with open(dockerfile_path, 'r') as f:
        content = f.read()
        
    # Check for required elements in Dockerfile
    assert "FROM" in content, "Dockerfile must specify a base image"
    assert "EXPOSE" in content, "Dockerfile should expose port(s)"
    assert "CMD" in content or "ENTRYPOINT" in content, "Dockerfile must specify how to run the application"

def test_docker_build(docker_image):
    """Test that Docker image builds successfully"""
    assert docker_image, "Docker image should be built successfully"

def test_container_starts(docker_container):
    """Test that container starts successfully"""
    assert docker_container.status == "running", f"Container should be running, but status is {docker_container.status}"

def test_container_health_endpoint(docker_container):
    """Test that health endpoint is accessible in the container"""
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200, "Health endpoint should return 200 OK"
    
    data = response.json()
    assert data["status"] == "healthy", "Health endpoint should report 'healthy' status"
    assert data["service"] == "example-data-processor", "Health endpoint should report correct service name"

def test_container_api_endpoints(docker_container):
    """Test that API endpoints are accessible in the container"""
    # Test get-stats endpoint
    columns = ["column1", "column2"]
    response = requests.post("http://localhost:8000/get-stats", json=columns)
    assert response.status_code == 200, "get-stats endpoint should return 200 OK"
    
    data = response.json()
    assert data["status"] == "success", "get-stats endpoint should report 'success' status"
    assert "results" in data, "get-stats endpoint should return results"
    
    # We don't test the upload endpoint here as it requires file handling
    # and we've already tested it in the unit tests

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 