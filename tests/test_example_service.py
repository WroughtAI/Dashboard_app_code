import pytest
import requests
import pandas as pd
import io
import json
import os
from fastapi.testclient import TestClient
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../examples/example_service')))

try:
    from app import app
    # Create a test client
    client = TestClient(app)
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    pytest.skip("Example service app not found", allow_module_level=True)

# Test data path
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(TEST_DATA_DIR, exist_ok=True)

def create_test_csv():
    """Create a test CSV file for upload testing"""
    df = pd.DataFrame({
        'id': range(1, 101),
        'value': [i * 0.5 for i in range(1, 101)],
        'category': ['A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C' for i in range(1, 101)]
    })
    
    test_csv_path = os.path.join(TEST_DATA_DIR, 'test_data.csv')
    df.to_csv(test_csv_path, index=False)
    return test_csv_path

# Test health check endpoint
def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "example-data-processor"
    assert "version" in data

# Test get-stats endpoint
def test_get_stats():
    """Test the stats endpoint"""
    columns = ["column1", "column2"]
    response = client.post("/get-stats", json=columns)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data
    # Check that stats were returned for each requested column
    for column in columns:
        assert column in data["results"]
        assert "mean" in data["results"][column]
        assert "median" in data["results"][column]

# Test file upload endpoint
def test_file_upload():
    """Test the file upload endpoint"""
    # Create a test CSV file
    test_csv_path = create_test_csv()
    
    # Test with default options
    with open(test_csv_path, 'rb') as f:
        response = client.post(
            "/upload",
            files={"file": ("test_data.csv", f, "text/csv")},
            data={"options": json.dumps({"calculate_stats": True})}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "test_data.csv"
    assert "summary" in data
    assert data["summary"]["rows"] == 100
    assert "id" in data["summary"]["columns"]
    assert "value" in data["summary"]["columns"]
    assert "category" in data["summary"]["columns"]
    assert "statistics" in data["summary"]
    assert "value" in data["summary"]["statistics"]

# Test file upload with no stats calculation
def test_file_upload_no_stats():
    """Test file upload with stats calculation disabled"""
    # Create a test CSV file
    test_csv_path = create_test_csv()
    
    # Test with stats calculation disabled
    with open(test_csv_path, 'rb') as f:
        response = client.post(
            "/upload",
            files={"file": ("test_data.csv", f, "text/csv")},
            data={"options": json.dumps({"calculate_stats": False})}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "statistics" not in data["summary"]

# Integration test to check if the service can be accessed via HTTP
def test_service_integration():
    """
    Integration test to verify the service can be accessed when deployed.
    This test is skipped by default as it requires the service to be running.
    To run this test, set the environment variable TEST_INTEGRATION=1
    """
    if not os.environ.get("TEST_INTEGRATION"):
        pytest.skip("Integration test disabled. Set TEST_INTEGRATION=1 to enable.")
    
    # Try to connect to the deployed service
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    except requests.RequestException as e:
        pytest.fail(f"Failed to connect to service: {e}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 