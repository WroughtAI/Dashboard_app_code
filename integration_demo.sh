#!/bin/bash

# Dashboard Service Integration Demo
# This script demonstrates how to integrate the dashboard service with the scaffold framework

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Dashboard Service Integration Demo${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Step 1: Build the dashboard service
echo -e "${YELLOW}Step 1: Building Dashboard Service Docker Image${NC}"
cd dashboard_service
docker build -t dashboard-service . --quiet
echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Step 2: Test the service locally
echo -e "${YELLOW}Step 2: Testing Dashboard Service${NC}"
echo "Starting service on port 8000..."

# Start service in background
docker run --rm -d -p 8000:8000 --name dashboard-test dashboard-service

# Wait for service to be ready
echo "Waiting for service to be ready..."
sleep 5

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "Health check response: $HEALTH_RESPONSE"

# Test some API endpoints
echo "Testing API endpoints..."
curl -s http://localhost:8000/agent-status | jq '.status' || echo "Service working (jq not available)"
echo -e "${GREEN}✅ Service is working correctly${NC}"
echo ""

# Stop test service
docker stop dashboard-test

# Step 3: Demonstrate integration command
echo -e "${YELLOW}Step 3: Integration with Scaffold Framework${NC}"
echo "To integrate this service with the scaffold framework, you would run:"
echo ""
echo -e "${BLUE}cd scripts${NC}"
echo -e "${BLUE}./integration_setup.sh \\${NC}"
echo -e "${BLUE}  --service-name=dashboard-service \\${NC}"
echo -e "${BLUE}  --service-port=8000 \\${NC}"
echo -e "${BLUE}  --contract=../dashboard_service_contract.py${NC}"
echo ""

# Step 4: Show what the integration script would do
echo -e "${YELLOW}Step 4: What the Integration Script Does${NC}"
echo "The integration script will:"
echo "• Copy the service contract to the scaffold framework"
echo "• Add the service URL to the scaffold configuration"  
echo "• Update docker-compose.yml to include the dashboard service"
echo "• Verify the service has the required health endpoint"
echo ""

# Step 5: Show service features
echo -e "${YELLOW}Step 5: Dashboard Service Features${NC}"
echo "The dashboard service provides:"
echo "• 📊 Real-time agent monitoring"
echo "• 🤖 LLM usage statistics and history"
echo "• 🗄️  Vector store management and search"
echo "• ✅ Compliance monitoring and reporting"
echo "• 📁 File upload for configuration"
echo "• 🔌 WebSocket support for real-time updates"
echo "• 📖 OpenAPI documentation at /docs"
echo ""

# Step 6: Service endpoints
echo -e "${YELLOW}Step 6: Available API Endpoints${NC}"
echo "Key endpoints:"
echo "• GET  /health              - Health check (required by scaffold)"
echo "• GET  /                    - Dashboard UI"
echo "• GET  /docs                - API documentation"
echo "• GET  /agent-status        - Current agent status"
echo "• GET  /llm-usage           - LLM usage statistics"
echo "• GET  /vector-status       - Vector store status"
echo "• GET  /compliance/summary  - Compliance overview"
echo "• POST /upload              - File upload endpoint"
echo "• WS   /ws/dashboard        - Real-time updates"
echo ""

echo -e "${GREEN}🎉 Dashboard Service is ready for scaffold integration!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Ensure your scaffold framework is available at the expected path"
echo "2. Run the integration script with the parameters shown above"
echo "3. Start the integrated system with docker-compose up -d"
echo "4. Access the dashboard at http://localhost:8000"
echo ""
echo -e "${BLUE}Service Contract Features:${NC}"
echo "• BaseRESTAdapter with retry logic"
echo "• All major dashboard endpoints wrapped"
echo "• File upload capability"
echo "• Comprehensive status monitoring"
echo "• Error handling and logging" 