#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Create data directory if it doesn't exist
mkdir -p data

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}= WroughtAI Agent-Scaffolding Integration Test Suite =${NC}"
echo -e "${BLUE}====================================================${NC}"
echo -e "This test suite verifies that your service can be integrated with the WroughtAI Agent-Scaffolding framework."
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed. Installing test dependencies...${NC}"
    pip install -r requirements.txt
fi

echo -e "${BLUE}=== PHASE 1: Basic API Standards Tests ===${NC}"
echo -e "Testing if your API follows the required standards for integration"
pytest test_api_standards.py -v
API_STATUS=$?

echo -e "\n${BLUE}=== PHASE 2: Example Service Functionality Tests ===${NC}"
echo -e "Testing if the example service works correctly as a standalone service"
pytest test_example_service.py -v
SERVICE_STATUS=$?

echo -e "\n${BLUE}=== PHASE 3: Agent-Scaffolding Integration Tests ===${NC}"
echo -e "Testing specific requirements for Agent-Scaffolding integration"
pytest test_scaffold_integration.py::test_service_exposes_required_endpoints test_scaffold_integration.py::test_requirements_txt test_scaffold_integration.py::test_scaffolding_integration_checklist -v
SCAFFOLD_STATUS=$?

# Check if docker is available
if command -v docker &> /dev/null; then
    echo -e "\n${BLUE}=== PHASE 4: Docker Configuration Tests ===${NC}"
    echo -e "Testing if Docker configuration meets Agent-Scaffolding requirements"
    
    echo -e "${YELLOW}Docker is available. Would you like to run Docker integration tests? [y/N]${NC}"
    read -p "" -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # First run basic Dockerfile tests that don't require running containers
        pytest test_scaffold_integration.py::test_dockerfile_scaffolding_compatibility -v
        
        echo -e "\nWould you like to run tests that build and run Docker containers? [y/N]"
        echo -e "(This may take a few minutes and requires Docker to be running)"
        read -p "" -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "Running Docker container tests..."
            # Set the environment variable to enable Docker integration tests
            TEST_DOCKER_INTEGRATION=1 pytest test_docker_integration.py -v
            DOCKER_STATUS=$?
            
            # Also run the scaffold Docker network binding test
            TEST_DOCKER_INTEGRATION=1 pytest test_scaffold_integration.py::test_docker_network_binding -v
        fi
    else
        echo -e "${YELLOW}Skipping Docker tests.${NC}"
    fi
else
    echo -e "\n${YELLOW}Docker is not available. Skipping Docker integration tests.${NC}"
fi

# Print summary
echo -e "\n${BLUE}==========================================${NC}"
echo -e "${BLUE}=        INTEGRATION TEST SUMMARY        =${NC}"
echo -e "${BLUE}==========================================${NC}"

if [ $API_STATUS -eq 0 ]; then
    echo -e "API Standards:           ${GREEN}PASSED${NC}"
else
    echo -e "API Standards:           ${RED}FAILED${NC}"
fi

if [ $SERVICE_STATUS -eq 0 ]; then
    echo -e "Service Functionality:   ${GREEN}PASSED${NC}"
else
    echo -e "Service Functionality:   ${RED}FAILED${NC}"
fi

if [ $SCAFFOLD_STATUS -eq 0 ]; then
    echo -e "Scaffolding Integration: ${GREEN}PASSED${NC}"
else
    echo -e "Scaffolding Integration: ${RED}FAILED${NC}"
fi

if [ -n "$DOCKER_STATUS" ]; then
    if [ $DOCKER_STATUS -eq 0 ]; then
        echo -e "Docker Configuration:    ${GREEN}PASSED${NC}"
    else
        echo -e "Docker Configuration:    ${RED}FAILED${NC}"
    fi
fi

echo -e "\n${BLUE}=== INTEGRATION INSTRUCTIONS ===${NC}"
echo -e "To integrate your service with the Agent-Scaffolding framework:"
echo -e "1. Ensure your service has a /health endpoint that returns status information"
echo -e "2. Expose your service ports on 0.0.0.0 (not localhost/127.0.0.1)"
echo -e "3. Package your service in a Docker container using the provided templates"
echo -e "4. Clone the Agent-Scaffolding repository from https://github.com/WroughtAI/Agent-Scaffolding"
echo -e "5. Follow the integration guide in the scaffold documentation"

echo -e "\n${GREEN}Test suite completed.${NC}" 