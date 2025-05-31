#!/usr/bin/env python3
"""
Test script for dashboard service integration with scaffold framework.
This script verifies that the dashboard service can be properly integrated
using the integration setup script.
"""

import requests
import time
import sys
import json
from typing import Dict, Any

def test_service_health(base_url: str) -> bool:
    """Test if the service health endpoint is working."""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Verify expected response format
        required_fields = ["status", "service", "version"]
        for field in required_fields:
            if field not in data:
                print(f"❌ Health check missing required field: {field}")
                return False
        
        if data["status"] != "healthy":
            print(f"❌ Service reports unhealthy status: {data['status']}")
            return False
            
        print(f"✅ Health check passed: {data['service']} v{data['version']}")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_endpoints(base_url: str) -> bool:
    """Test core API endpoints."""
    endpoints = [
        "/agent-status",
        "/llm-usage", 
        "/vector-status",
        "/recent-activity",
        "/llm-history",
        "/vector-collections",
        "/package-status",
        "/compliance/test-results",
        "/compliance/summary"
    ]
    
    failed_endpoints = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Verify standard response format
            if "status" not in data or "service" not in data:
                print(f"❌ {endpoint}: Invalid response format")
                failed_endpoints.append(endpoint)
                continue
                
            if data["status"] == "error":
                print(f"❌ {endpoint}: Service error - {data.get('error', 'Unknown')}")
                failed_endpoints.append(endpoint)
                continue
                
            print(f"✅ {endpoint}: Working correctly")
            
        except requests.RequestException as e:
            print(f"❌ {endpoint}: Request failed - {e}")
            failed_endpoints.append(endpoint)
    
    if failed_endpoints:
        print(f"\n❌ {len(failed_endpoints)} endpoints failed: {failed_endpoints}")
        return False
    else:
        print(f"\n✅ All {len(endpoints)} endpoints working correctly")
        return True

def test_file_upload(base_url: str) -> bool:
    """Test file upload functionality."""
    try:
        # Create a test JSON file
        test_data = {
            "test": True,
            "integration": "dashboard-service",
            "timestamp": time.time()
        }
        
        files = {
            'file': ('test_config.json', json.dumps(test_data), 'application/json')
        }
        
        response = requests.post(f"{base_url}/upload", files=files, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success":
            print(f"❌ File upload failed: {data.get('error', 'Unknown error')}")
            return False
            
        print("✅ File upload working correctly")
        return True
        
    except requests.RequestException as e:
        print(f"❌ File upload failed: {e}")
        return False

def test_service_contract() -> bool:
    """Test the service contract implementation."""
    try:
        from dashboard_service_contract import DashboardServiceContract
        
        # Create service contract instance
        contract = DashboardServiceContract()
        
        # Test health check through contract
        health = contract.health_check()
        if health.get("status") != "healthy":
            print(f"❌ Service contract health check failed: {health}")
            return False
            
        # Test a few other methods
        agent_status = contract.get_agent_status()
        if agent_status.get("status") != "success":
            print(f"❌ Service contract agent status failed: {agent_status}")
            return False
            
        llm_usage = contract.get_llm_usage()
        if llm_usage.get("status") != "success":
            print(f"❌ Service contract LLM usage failed: {llm_usage}")
            return False
            
        print("✅ Service contract working correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Service contract import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Service contract test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Dashboard Service Integration")
    print("=" * 50)
    
    # Service configuration
    base_url = "http://localhost:8000"
    
    # Wait for service to be ready
    print("⏳ Waiting for service to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Service is ready")
                break
        except requests.RequestException:
            pass
        
        if i < max_retries - 1:
            time.sleep(2)
    else:
        print("❌ Service failed to start within timeout period")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_service_health(base_url)),
        ("API Endpoints", lambda: test_api_endpoints(base_url)),
        ("File Upload", lambda: test_file_upload(base_url)),
        ("Service Contract", test_service_contract)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Dashboard service is ready for scaffold integration.")
        print("\nTo integrate with scaffold framework, run:")
        print("cd scripts")
        print("./integration_setup.sh \\")
        print("  --service-name=dashboard-service \\")
        print("  --service-port=8000 \\")
        print("  --contract=../dashboard_service_contract.py")
        sys.exit(0)
    else:
        print(f"\n❌ {len(tests) - passed} tests failed. Please fix issues before integration.")
        sys.exit(1)

if __name__ == "__main__":
    main() 