#!/bin/bash

# Health Check Script
# This script checks the health of integrated services.

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
DOCKER_COMPOSE_FILE="../docker-compose.yml"
TIMEOUT=5

# Print usage information
print_usage() {
    echo "Usage: $0 [--compose-file=PATH] [--timeout=SECONDS]"
    echo ""
    echo "Options:"
    echo "  --compose-file=PATH    Path to docker-compose.yml file (default: ../docker-compose.yml)"
    echo "  --timeout=SECONDS      Timeout in seconds for health checks (default: 5)"
    echo "  --service=NAME         Check only specific service (optional)"
    exit 1
}

# Parse command line arguments
SPECIFIC_SERVICE=""
for arg in "$@"; do
    case $arg in
        --compose-file=*)
        DOCKER_COMPOSE_FILE="${arg#*=}"
        shift
        ;;
        --timeout=*)
        TIMEOUT="${arg#*=}"
        shift
        ;;
        --service=*)
        SPECIFIC_SERVICE="${arg#*=}"
        shift
        ;;
        --help)
        print_usage
        ;;
        *)
        # Unknown option
        echo -e "${RED}Error: Unknown option: $arg${NC}"
        print_usage
        ;;
    esac
done

# Check if docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo -e "${RED}Error: Docker Compose file not found at $DOCKER_COMPOSE_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}Checking service health...${NC}"

# Get services and their ports from docker-compose.yml
if [ -z "$SPECIFIC_SERVICE" ]; then
    # Get all services with exposed ports
    SERVICES=$(grep -A 5 "ports:" "$DOCKER_COMPOSE_FILE" | grep -B 5 "\"[0-9]*:[0-9]*\"" | grep -E "^  [a-zA-Z0-9_-]+:" | sed 's/://' | tr -d ' ')
else
    # Check only the specified service
    SERVICES="$SPECIFIC_SERVICE"
fi

# Initialize counters
HEALTHY_COUNT=0
TOTAL_COUNT=0

# Check each service
for SERVICE in $SERVICES; do
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
    # Find the port mapping for this service
    PORT_LINE=$(grep -A 5 "^  $SERVICE:" "$DOCKER_COMPOSE_FILE" | grep -E "[0-9]+:[0-9]+" | head -1)
    if [ -z "$PORT_LINE" ]; then
        echo -e "${YELLOW}⚠ Service $SERVICE does not expose any ports, skipping health check${NC}"
        continue
    fi
    
    # Extract the host port
    HOST_PORT=$(echo "$PORT_LINE" | grep -Eo "[0-9]+:" | tr -d ':')
    
    echo -e "Checking health of ${YELLOW}$SERVICE${NC} on port ${YELLOW}$HOST_PORT${NC}..."
    
    # Try to connect to the health endpoint
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT http://localhost:$HOST_PORT/health 2>/dev/null || echo "Failed")
    
    if [ "$HEALTH_RESPONSE" == "200" ]; then
        echo -e "  ${GREEN}✓ $SERVICE is healthy (HTTP 200)${NC}"
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    else
        echo -e "  ${RED}✗ $SERVICE is not healthy (Response: $HEALTH_RESPONSE)${NC}"
        echo -e "    Try: curl http://localhost:$HOST_PORT/health"
    fi
done

# Print summary
echo ""
echo -e "${GREEN}Health check summary:${NC}"
echo -e "  $HEALTHY_COUNT/$TOTAL_COUNT services are healthy"

if [ $HEALTHY_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${GREEN}All services are healthy!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some services are not healthy. Please check the logs.${NC}"
    echo -e "Run: docker-compose logs -f <service-name>"
    exit 1
fi 