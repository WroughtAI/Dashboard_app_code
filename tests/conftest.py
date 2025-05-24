import pytest
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(TEST_DATA_DIR, exist_ok=True)

def pytest_configure(config):
    """
    Custom pytest configuration
    """
    # Add custom markers
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "docker: mark test as requiring docker")
    config.addinivalue_line("markers", "api: mark test as API test")

def pytest_collection_modifyitems(config, items):
    """
    Skip integration tests by default unless --run-integration is specified
    """
    run_integration = config.getoption("--run-integration", default=False)
    run_docker = config.getoption("--run-docker", default=False)
    
    if not run_integration:
        skip_integration = pytest.mark.skip(reason="Integration tests skipped. Use --run-integration to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
                
    if not run_docker:
        skip_docker = pytest.mark.skip(reason="Docker tests skipped. Use --run-docker to run")
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(skip_docker)

def pytest_addoption(parser):
    """
    Add command line options for pytest
    """
    parser.addoption(
        "--run-integration", 
        action="store_true", 
        default=False, 
        help="Run integration tests"
    )
    parser.addoption(
        "--run-docker", 
        action="store_true", 
        default=False, 
        help="Run docker tests"
    ) 