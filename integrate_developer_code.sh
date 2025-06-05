#!/bin/bash
# integrate_developer_code.sh
#
# This script automates the integration of developer code (implementing Code_Attachment_to_scaffold requirements)
# into the agent-scaffolding framework to create a complete, deployable agent.
#
# The script dynamically discovers the developer's REST API structure and adapts the agent-scaffold 
# to work with that specific implementation, allowing for integration of 30+ different agent types
# with unique capabilities.
#
# Usage: ./integrate_developer_code.sh <developer_repo_url> <component_type>
#
# Example: ./integrate_developer_code.sh https://github.com/developer/bias-detector-component bias_detector

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Error: Missing arguments${NC}"
    echo "Usage: $0 <developer_repo_url> <component_type>"
    echo "Example: $0 https://github.com/developer/bias-detector-component bias_detector"
    exit 1
fi

DEVELOPER_REPO_URL=$1
COMPONENT_TYPE=$2
INTEGRATION_DIR="integrated-agent-${COMPONENT_TYPE}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVELOPER_CODE_DIR="developer-${COMPONENT_TYPE}"
API_DISCOVERY_FILE="api_discovery.json"
TEMP_API_REQUESTS="temp_api_requests.json"

# Function to display section header
section() {
    echo -e "\n${GREEN}==== $1 ====${NC}\n"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
for tool in git docker docker-compose curl jq; do
    if ! command_exists $tool; then
        echo -e "${RED}Error: Required tool '$tool' is not installed${NC}"
        exit 1
    fi
done

section "Starting Integration Process for $COMPONENT_TYPE"

# Create a working directory for the integration
WORK_DIR="${SCRIPT_DIR}/integration_work"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Step 1: Clone developer's repository
section "Cloning Developer Repository"
if [ -d "$DEVELOPER_CODE_DIR" ]; then
    echo -e "${YELLOW}Warning: Developer code directory already exists. Removing...${NC}"
    rm -rf "$DEVELOPER_CODE_DIR"
fi

echo -e "Cloning from: ${BLUE}$DEVELOPER_REPO_URL${NC}"
git clone "$DEVELOPER_REPO_URL" "$DEVELOPER_CODE_DIR"
cd "$DEVELOPER_CODE_DIR"

# Step 2: Verify developer's code meets requirements
section "Verifying Developer's Code Structure"

# Check for Dockerfile
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: No Dockerfile found in developer's repository${NC}"
    exit 1
fi

# Check for src directory
if [ ! -d "src" ]; then
    echo -e "${RED}Error: No src directory found in developer's repository${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Developer code structure verification passed${NC}"

# Step 3: Build developer's Docker container
section "Building Developer's Docker Container"
DEVELOPER_IMAGE="developer-${COMPONENT_TYPE}:latest"
docker build -t "$DEVELOPER_IMAGE" .

echo -e "${GREEN}✓ Developer container built successfully: $DEVELOPER_IMAGE${NC}"

# Step 4: Run developer's container and perform dynamic API discovery
section "Dynamic API Discovery"

# Run container in background
CONTAINER_ID=$(docker run -d -p 8000:8000 "$DEVELOPER_IMAGE")
echo -e "Container started with ID: $CONTAINER_ID"

# Wait for container to start
echo -e "Waiting for container to initialize..."
sleep 5

# Test health endpoint
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HEALTH_STATUS" != "200" ]; then
    echo -e "${YELLOW}Warning: Standard health endpoint (http://localhost:8000/health) not found. Looking for alternatives...${NC}"
    
    # Try common health endpoint alternatives
    for endpoint in "/healthz" "/status" "/api/health" "/api/v1/health"; do
        ALT_HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint")
        if [ "$ALT_HEALTH_STATUS" == "200" ]; then
            echo -e "${GREEN}Found alternative health endpoint: $endpoint${NC}"
            HEALTH_ENDPOINT="$endpoint"
            break
        fi
    done
    
    if [ -z "$HEALTH_ENDPOINT" ]; then
        echo -e "${RED}Error: No valid health endpoint found${NC}"
        docker stop "$CONTAINER_ID"
        exit 1
    fi
else
    HEALTH_ENDPOINT="/health"
    echo -e "${GREEN}✓ Standard health endpoint verified${NC}"
fi

# Perform API discovery
echo -e "Discovering API endpoints..."

# Create a JSON file to store API discovery results
echo "{\"base_url\": \"http://localhost:8000\", \"endpoints\": []}" > "$API_DISCOVERY_FILE"

# Check for OpenAPI/Swagger documentation
SWAGGER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/swagger.json")
OPENAPI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/openapi.json")

if [ "$SWAGGER_STATUS" == "200" ]; then
    echo -e "${GREEN}Found Swagger documentation${NC}"
    curl -s "http://localhost:8000/swagger.json" > swagger.json
    # Extract endpoints from Swagger
    jq -r '.paths | keys[]' swagger.json | while read -r endpoint; do
        # Get methods for this endpoint
        jq -r --arg ep "$endpoint" '.paths[$ep] | keys[]' swagger.json | while read -r method; do
            description=$(jq -r --arg ep "$endpoint" --arg method "$method" '.paths[$ep][$method].description // .paths[$ep][$method].summary // "No description"' swagger.json)
            # Add to our API discovery file
            jq --arg ep "$endpoint" --arg method "$method" --arg desc "$description" '.endpoints += [{"path": $ep, "method": $method, "description": $desc}]' "$API_DISCOVERY_FILE" > temp.json && mv temp.json "$API_DISCOVERY_FILE"
        done
    done
elif [ "$OPENAPI_STATUS" == "200" ]; then
    echo -e "${GREEN}Found OpenAPI documentation${NC}"
    curl -s "http://localhost:8000/openapi.json" > openapi.json
    # Extract endpoints from OpenAPI
    jq -r '.paths | keys[]' openapi.json | while read -r endpoint; do
        # Get methods for this endpoint
        jq -r --arg ep "$endpoint" '.paths[$ep] | keys[]' openapi.json | while read -r method; do
            description=$(jq -r --arg ep "$endpoint" --arg method "$method" '.paths[$ep][$method].description // .paths[$ep][$method].summary // "No description"' openapi.json)
            # Add to our API discovery file
            jq --arg ep "$endpoint" --arg method "$method" --arg desc "$description" '.endpoints += [{"path": $ep, "method": $method, "description": $desc}]' "$API_DISCOVERY_FILE" > temp.json && mv temp.json "$API_DISCOVERY_FILE"
        done
    done
else
    echo -e "${YELLOW}No OpenAPI/Swagger documentation found. Probing common API paths...${NC}"
    
    # Define common API patterns to probe
    COMMON_PATHS=(
        "/api/v1"
        "/api"
        "/v1"
        "/api/v1/${COMPONENT_TYPE}"
        "/api/${COMPONENT_TYPE}"
        "/${COMPONENT_TYPE}"
    )
    
    # Probe common paths with multiple HTTP methods
    for path in "${COMMON_PATHS[@]}"; do
        for method in "GET" "POST"; do
            if [ "$method" == "GET" ]; then
                STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "http://localhost:8000${path}")
            else
                # For POST, send an empty JSON body
                STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{}' "http://localhost:8000${path}")
            fi
            
            if [ "$STATUS" != "404" ] && [ "$STATUS" != "000" ]; then
                echo -e "${GREEN}Found potential API endpoint: ${method} ${path} (Status: ${STATUS})${NC}"
                jq --arg path "$path" --arg method "$method" --arg status "$STATUS" '.endpoints += [{"path": $path, "method": $method, "status": $status, "probed": true}]' "$API_DISCOVERY_FILE" > temp.json && mv temp.json "$API_DISCOVERY_FILE"
            fi
        done
    done
    
    # If we still haven't found endpoints, try more aggressive probing
    if [ "$(jq '.endpoints | length' "$API_DISCOVERY_FILE")" == "0" ]; then
        echo -e "${YELLOW}No standard endpoints found. Performing deeper API probe...${NC}"
        
        # More specific endpoint patterns based on component type
        SPECIFIC_PATHS=(
            "/api/v1/${COMPONENT_TYPE}/analyze"
            "/api/v1/${COMPONENT_TYPE}/process"
            "/api/v1/${COMPONENT_TYPE}/predict"
            "/api/v1/${COMPONENT_TYPE}/detect"
            "/api/v1/${COMPONENT_TYPE}/evaluate"
            "/api/${COMPONENT_TYPE}/analyze"
            "/${COMPONENT_TYPE}/analyze"
            "/analyze"
            "/process"
            "/predict"
            "/detect"
            "/evaluate"
        )
        
        for path in "${SPECIFIC_PATHS[@]}"; do
            for method in "GET" "POST"; do
                if [ "$method" == "GET" ]; then
                    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "http://localhost:8000${path}")
                else
                    # For POST, send an empty JSON body
                    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{}' "http://localhost:8000${path}")
                fi
                
                if [ "$STATUS" != "404" ] && [ "$STATUS" != "000" ]; then
                    echo -e "${GREEN}Found potential API endpoint: ${method} ${path} (Status: ${STATUS})${NC}"
                    jq --arg path "$path" --arg method "$method" --arg status "$STATUS" '.endpoints += [{"path": $path, "method": $method, "status": $status, "probed": true}]' "$API_DISCOVERY_FILE" > temp.json && mv temp.json "$API_DISCOVERY_FILE"
                fi
            done
        done
    fi
fi

# Determine primary endpoint for agent integration
if [ "$(jq '.endpoints | length' "$API_DISCOVERY_FILE")" == "0" ]; then
    echo -e "${YELLOW}Warning: No API endpoints discovered. Falling back to default: /api/v1/function${NC}"
    PRIMARY_ENDPOINT="/api/v1/function"
    PRIMARY_METHOD="POST"
else
    # Prioritize endpoints based on naming conventions and HTTP methods
    # First, look for POST endpoints with 'process', 'analyze', or component name in the path
    PRIMARY_ENDPOINT=$(jq -r '.endpoints[] | select(.method == "POST" and (.path | contains("process") or contains("analyze") or contains("'${COMPONENT_TYPE}'"))' "$API_DISCOVERY_FILE" | head -1 | jq -r '.path')
    
    # If none found, just take the first POST endpoint
    if [ -z "$PRIMARY_ENDPOINT" ] || [ "$PRIMARY_ENDPOINT" == "null" ]; then
        PRIMARY_ENDPOINT=$(jq -r '.endpoints[] | select(.method == "POST")' "$API_DISCOVERY_FILE" | head -1 | jq -r '.path')
        
        # If still none found, take any endpoint
        if [ -z "$PRIMARY_ENDPOINT" ] || [ "$PRIMARY_ENDPOINT" == "null" ]; then
            PRIMARY_ENDPOINT=$(jq -r '.endpoints[0].path' "$API_DISCOVERY_FILE")
            PRIMARY_METHOD=$(jq -r '.endpoints[0].method' "$API_DISCOVERY_FILE")
        else
            PRIMARY_METHOD="POST"
        fi
    else
        PRIMARY_METHOD="POST"
    fi
fi

echo -e "${GREEN}✓ Selected primary endpoint: ${PRIMARY_METHOD} ${PRIMARY_ENDPOINT}${NC}"

# Sample request/response analysis for the primary endpoint
if [ "$PRIMARY_METHOD" == "POST" ]; then
    echo -e "Analyzing request/response format for primary endpoint..."
    
    # Generate some sample request payloads
    cat > "$TEMP_API_REQUESTS" << EOF
[
  {},
  {"data": "sample"},
  {"input": "sample"},
  {"text": "sample"},
  {"content": "sample"},
  {"query": "sample"},
  {"${COMPONENT_TYPE}_input": "sample"}
]
EOF
    
    # Try each sample payload and record the response
    jq -c '.[]' "$TEMP_API_REQUESTS" | while read -r payload; do
        RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$payload" "http://localhost:8000${PRIMARY_ENDPOINT}")
        STATUS=$?
        
        if [ $STATUS -eq 0 ] && [ "$RESPONSE" != "" ] && [ "$RESPONSE" != "null" ]; then
            echo -e "${GREEN}Found working request format: ${payload}${NC}"
            echo "$payload" > working_request.json
            echo "$RESPONSE" > working_response.json
            break
        fi
    done
    
    # If no automatic detection worked, use a default
    if [ ! -f "working_request.json" ]; then
        echo -e "${YELLOW}Could not automatically determine request format. Using default.${NC}"
        echo '{"input": "sample_data"}' > working_request.json
    fi
else
    echo -e "${YELLOW}Primary endpoint is not POST. Skipping request/response analysis.${NC}"
    echo '{}' > working_request.json
fi

# Stop container
docker stop "$CONTAINER_ID"

echo -e "${GREEN}✓ API discovery complete${NC}"

# Return to work directory
cd "$WORK_DIR"

# Step 5: Set up fresh agent-scaffold
section "Setting Up Fresh Agent-Scaffold"
if [ -d "$INTEGRATION_DIR" ]; then
    echo -e "${YELLOW}Warning: Integration directory already exists. Removing...${NC}"
    rm -rf "$INTEGRATION_DIR"
fi

echo -e "Creating fresh agent-scaffold..."
mkdir -p "$INTEGRATION_DIR"

# Instead of cloning from a hardcoded path, copy from the current repo structure
# This assumes the script is run from the agent-scaffolding repository
echo -e "Copying agent-scaffold structure..."
cp -r "$SCRIPT_DIR/src" "$INTEGRATION_DIR/"
cp -r "$SCRIPT_DIR/tests" "$INTEGRATION_DIR/" 2>/dev/null || mkdir -p "$INTEGRATION_DIR/tests"
cp -r "$SCRIPT_DIR/config" "$INTEGRATION_DIR/" 2>/dev/null || mkdir -p "$INTEGRATION_DIR/config"
cp "$SCRIPT_DIR/Dockerfile" "$INTEGRATION_DIR/" 2>/dev/null || echo -e "${YELLOW}Warning: No Dockerfile found in agent-scaffolding${NC}"
cp "$SCRIPT_DIR/docker-compose.yml" "$INTEGRATION_DIR/" 2>/dev/null || echo -e "${YELLOW}Warning: No docker-compose.yml found in agent-scaffolding${NC}"
cp "$SCRIPT_DIR/requirements.txt" "$INTEGRATION_DIR/" 2>/dev/null || echo -e "${YELLOW}Warning: No requirements.txt found in agent-scaffolding${NC}"

cd "$INTEGRATION_DIR"

# Step 6: Generate dynamic adapter based on discovered API
section "Generating Dynamic Adapter"

# Create adapters directory if it doesn't exist
mkdir -p src/agent_shell/adapters

# Generate adapter for the discovered API
cat > src/agent_shell/adapters/${COMPONENT_TYPE}_adapter.py << EOF
"""
Dynamically generated adapter for ${COMPONENT_TYPE}
Primary endpoint: ${PRIMARY_METHOD} ${PRIMARY_ENDPOINT}
Generated by integrate_developer_code.sh
"""

import json
import requests
from typing import Dict, Any, Optional

class ${COMPONENT_TYPE^}Adapter:
    """
    Adapter for ${COMPONENT_TYPE} service.
    This adapter was automatically generated based on API discovery.
    """
    
    def __init__(self, base_url: str = "http://${COMPONENT_TYPE}-container:8000"):
        """
        Initialize the adapter with the service base URL.
        
        Args:
            base_url: Base URL of the ${COMPONENT_TYPE} service
        """
        self.base_url = base_url.rstrip('/')
        self.primary_endpoint = f"{self.base_url}${PRIMARY_ENDPOINT}"
        self.health_endpoint = f"{self.base_url}${HEALTH_ENDPOINT}"
    
    def check_health(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def process_request(self, data: Any, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a request using the ${COMPONENT_TYPE} service.
        
        Args:
            data: The data to process
            parameters: Additional parameters for processing
            
        Returns:
            Dict[str, Any]: Results from the service
        """
        try:
            # Create payload based on discovered API format
            payload = self._create_payload(data, parameters)
            
            # Send request to the service
            response = requests.${PRIMARY_METHOD.lower()}(
                self.primary_endpoint,
                json=payload,
                timeout=30
            )
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse and return the response
            return response.json()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to process request through ${COMPONENT_TYPE} service"
            }
    
    def _create_payload(self, data: Any, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a payload for the service based on the discovered API format.
        
        Args:
            data: The data to include in the payload
            parameters: Additional parameters to include
            
        Returns:
            Dict[str, Any]: Formatted payload for the service
        """
        # Load the working request format discovered during API analysis
        try:
            with open("${DEVELOPER_CODE_DIR}/working_request.json", "r") as f:
                request_template = json.load(f)
                
            # If template is empty, use a default format
            if not request_template:
                request_template = {"input": None}
                
            # The most common input field name from the template
            input_field = next(iter(request_template.keys()))
            
            # Create the payload by mapping data to the input field
            payload = request_template.copy()
            payload[input_field] = data
            
            # Add any additional parameters
            if parameters:
                for key, value in parameters.items():
                    if key not in payload:
                        payload[key] = value
                        
            return payload
        except Exception:
            # Fallback to a simple payload if template loading fails
            return {"input": data, **(parameters or {})}
EOF

echo -e "${GREEN}✓ Dynamic adapter generated${NC}"

# Step 7: Configure agent-scaffold to use developer's container
section "Configuring Agent-Scaffold"

# Update docker-compose.yml
echo -e "Updating docker-compose.yml..."
cat > docker-compose.yml << EOF
version: '3'
services:
  agent:
    build: .
    ports:
      - "9000:9000"
    depends_on:
      - ${COMPONENT_TYPE}-container
    environment:
      - FUNCTION_ENDPOINT=http://${COMPONENT_TYPE}-container:8000${PRIMARY_ENDPOINT}
      - HEALTH_ENDPOINT=http://${COMPONENT_TYPE}-container:8000${HEALTH_ENDPOINT}
      - COMPONENT_TYPE=${COMPONENT_TYPE}
  
  ${COMPONENT_TYPE}-container:
    image: ${DEVELOPER_IMAGE}
    ports:
      - "8000:8000"
EOF

# Create/update configuration directory
mkdir -p config
cat > config/agent_config.yaml << EOF
function:
  name: ${COMPONENT_TYPE}
  container: ${DEVELOPER_IMAGE}
  api_endpoint: http://${COMPONENT_TYPE}-container:8000${PRIMARY_ENDPOINT}
  health_endpoint: http://${COMPONENT_TYPE}-container:8000${HEALTH_ENDPOINT}
  method: ${PRIMARY_METHOD}
  timeout: 30s
  retries: 3
agent:
  name: ${COMPONENT_TYPE}-agent
  version: 1.0.0
  adapter: ${COMPONENT_TYPE}_adapter
EOF

# Create/update Kubernetes deployment files
mkdir -p k8s
cat > k8s/deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: integrated-${COMPONENT_TYPE}-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: integrated-${COMPONENT_TYPE}-agent
  template:
    metadata:
      labels:
        app: integrated-${COMPONENT_TYPE}-agent
    spec:
      containers:
      - name: agent
        image: \${AGENT_IMAGE}
        ports:
        - containerPort: 9000
        env:
        - name: FUNCTION_ENDPOINT
          value: http://localhost:8000${PRIMARY_ENDPOINT}
        - name: HEALTH_ENDPOINT
          value: http://localhost:8000${HEALTH_ENDPOINT}
        - name: COMPONENT_TYPE
          value: ${COMPONENT_TYPE}
      - name: ${COMPONENT_TYPE}-container
        image: ${DEVELOPER_IMAGE}
        ports:
        - containerPort: 8000
EOF

cat > k8s/service.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: integrated-${COMPONENT_TYPE}-agent
spec:
  selector:
    app: integrated-${COMPONENT_TYPE}-agent
  ports:
  - port: 80
    targetPort: 9000
  type: ClusterIP
EOF

echo -e "${GREEN}✓ Agent-scaffold configuration updated${NC}"

# Copy the API discovery results to the integration directory for reference
cp "${DEVELOPER_CODE_DIR}/${API_DISCOVERY_FILE}" .
if [ -f "${DEVELOPER_CODE_DIR}/working_request.json" ]; then
  cp "${DEVELOPER_CODE_DIR}/working_request.json" .
fi
if [ -f "${DEVELOPER_CODE_DIR}/working_response.json" ]; then
  cp "${DEVELOPER_CODE_DIR}/working_response.json" .
fi

# Step 8: Generate dynamic tests based on discovered API
section "Generating Dynamic Tests"

mkdir -p tests/integration

cat > tests/integration/test_${COMPONENT_TYPE}_integration.py << EOF
"""
Dynamically generated integration tests for ${COMPONENT_TYPE}
Primary endpoint: ${PRIMARY_METHOD} ${PRIMARY_ENDPOINT}
Generated by integrate_developer_code.sh
"""

import pytest
import requests
import json
import os
import time

# Load test data from working request if available
try:
    with open("working_request.json", "r") as f:
        TEST_REQUEST = json.load(f)
except Exception:
    TEST_REQUEST = {"input": "test_data"}

@pytest.fixture(scope="module")
def services_ready():
    """Ensure services are ready before running tests"""
    # Wait for services to be available
    agent_url = "http://localhost:9000/api/v1/agent/status"
    function_url = "http://localhost:8000${HEALTH_ENDPOINT}"
    
    max_retries = 10
    retry_delay = 2
    
    for _ in range(max_retries):
        try:
            agent_response = requests.get(agent_url)
            function_response = requests.get(function_url)
            
            if agent_response.status_code == 200 and function_response.status_code == 200:
                return True
        except Exception:
            pass
        
        time.sleep(retry_delay)
    
    pytest.fail("Services did not become ready in time")

def test_agent_status(services_ready):
    """Test agent status endpoint"""
    response = requests.get("http://localhost:9000/api/v1/agent/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"

def test_agent_function_integration(services_ready):
    """Test agent integration with ${COMPONENT_TYPE} function"""
    response = requests.post(
        "http://localhost:9000/api/v1/agent/function",
        json=TEST_REQUEST
    )
    assert response.status_code == 200

def test_direct_function_call(services_ready):
    """Test direct call to ${COMPONENT_TYPE} function"""
    response = requests.${PRIMARY_METHOD.lower()}(
        "http://localhost:8000${PRIMARY_ENDPOINT}",
        json=TEST_REQUEST
    )
    assert response.status_code == 200
EOF

echo -e "${GREEN}✓ Dynamic tests generated${NC}"

# Step 9: Run integration tests
section "Running Integration Tests"

# Build integrated solution
echo -e "Building integrated solution..."
docker-compose build

# Start services
echo -e "Starting services..."
docker-compose up -d

# Wait for services to start
echo -e "Waiting for services to initialize..."
sleep 15

# Run the tests
echo -e "Running integration tests..."
# We'll assume pytest is available in the environment
if command_exists pytest; then
    PYTHONPATH=. pytest -xvs tests/integration/test_${COMPONENT_TYPE}_integration.py
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -ne 0 ]; then
        echo -e "${YELLOW}Warning: Some tests failed. Review the test output above.${NC}"
        echo -e "You may need to manually adjust the adapter in src/agent_shell/adapters/${COMPONENT_TYPE}_adapter.py"
    else
        echo -e "${GREEN}✓ All integration tests passed${NC}"
    fi
else
    echo -e "${YELLOW}Warning: pytest not found. Skipping automatic test execution.${NC}"
    echo -e "To run tests manually, install pytest and run:"
    echo -e "PYTHONPATH=. pytest -xvs tests/integration/test_${COMPONENT_TYPE}_integration.py"
fi

# Stop services
docker-compose down

# Step 10: Prepare for deployment
section "Preparing for Deployment"

# Initialize git repository
git init
git add .
git commit -m "Integrate ${COMPONENT_TYPE} component into agent-scaffold"

echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Push this repository to GitHub:"
echo -e "   git remote add origin https://github.com/Your-Org/integrated-agent-${COMPONENT_TYPE}"
echo -e "   git push -u origin main"
echo -e ""
echo -e "2. Create a pull request to the main deployment repository"
echo -e ""
echo -e "3. After PR approval, CI/CD will build, test, and deploy to Kubernetes dev namespace"

# Return to original directory
cd ..

section "Integration Complete"
echo -e "${GREEN}Successfully integrated ${COMPONENT_TYPE} component into agent-scaffold.${NC}"
echo -e "${YELLOW}Integration directory:${NC} ${WORK_DIR}/${INTEGRATION_DIR}"
echo -e "${BLUE}Developer container:${NC} ${DEVELOPER_IMAGE}"
echo -e ""
echo -e "${YELLOW}API Discovery Results:${NC}"
echo -e "- Primary Endpoint: ${PRIMARY_METHOD} ${PRIMARY_ENDPOINT}"
echo -e "- Health Endpoint: ${HEALTH_ENDPOINT}"
echo -e "- Full API details available in: ${WORK_DIR}/${INTEGRATION_DIR}/${API_DISCOVERY_FILE}"
echo -e ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Review the integration in ${WORK_DIR}/${INTEGRATION_DIR}"
echo -e "2. Create a new git repository with the integrated code"
echo -e "3. Submit for review and deployment"

exit 0 