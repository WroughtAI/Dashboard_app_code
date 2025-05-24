#!/bin/bash

# Integration Setup Script
# This script automates the process of integrating your service with the scaffold framework.

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SCAFFOLD_DIR="../scaffold"  # Path to the scaffold framework directory
SERVICE_NAME=""             # Your service name
SERVICE_PORT=""             # Your service port
SERVICE_CONTRACT=""         # Your service contract file

# Print usage information
print_usage() {
    echo "Usage: $0 --service-name=NAME --service-port=PORT --contract=PATH [--scaffold-dir=DIR]"
    echo ""
    echo "Options:"
    echo "  --service-name=NAME     Name of your service (required)"
    echo "  --service-port=PORT     Port your service runs on (required)"
    echo "  --contract=PATH         Path to your service contract file (required)"
    echo "  --scaffold-dir=DIR      Path to scaffold framework directory (default: ../scaffold)"
    exit 1
}

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --service-name=*)
        SERVICE_NAME="${arg#*=}"
        shift
        ;;
        --service-port=*)
        SERVICE_PORT="${arg#*=}"
        shift
        ;;
        --contract=*)
        SERVICE_CONTRACT="${arg#*=}"
        shift
        ;;
        --scaffold-dir=*)
        SCAFFOLD_DIR="${arg#*=}"
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

# Check required parameters
if [ -z "$SERVICE_NAME" ] || [ -z "$SERVICE_PORT" ] || [ -z "$SERVICE_CONTRACT" ]; then
    echo -e "${RED}Error: Missing required parameters${NC}"
    print_usage
fi

# Convert service name to uppercase for environment variable
SERVICE_NAME_UPPER=$(echo $SERVICE_NAME | tr '[:lower:]' '[:upper:]' | tr '-' '_')

echo -e "${GREEN}Starting integration of $SERVICE_NAME with the scaffold framework...${NC}"

# Step 1: Check if scaffold directory exists
if [ ! -d "$SCAFFOLD_DIR" ]; then
    echo -e "${RED}Error: Scaffold directory not found at $SCAFFOLD_DIR${NC}"
    echo "Please specify the correct path using --scaffold-dir=PATH"
    exit 1
fi

# Step 2: Check if service contract file exists
if [ ! -f "$SERVICE_CONTRACT" ]; then
    echo -e "${RED}Error: Service contract file not found at $SERVICE_CONTRACT${NC}"
    exit 1
fi

# Step 3: Create clients directory in scaffold if it doesn't exist
CLIENTS_DIR="$SCAFFOLD_DIR/src/scaffold/clients"
mkdir -p "$CLIENTS_DIR"
echo -e "${GREEN}✓ Clients directory created/verified${NC}"

# Step 4: Copy base REST adapter if needed
if [ ! -f "$CLIENTS_DIR/base_rest_adapter.py" ]; then
    cp "$(dirname "$0")/../templates/service_contract_template.py" "$CLIENTS_DIR/base_rest_adapter.py"
    # Remove the example service contract class from the file
    sed -i '' '/class YourServiceContract/,$d' "$CLIENTS_DIR/base_rest_adapter.py"
    echo -e "${GREEN}✓ Base REST adapter copied to scaffold${NC}"
else
    echo -e "${YELLOW}ℹ Base REST adapter already exists, skipping${NC}"
fi

# Step 5: Copy service contract to scaffold
CONTRACT_FILENAME=$(basename "$SERVICE_CONTRACT")
cp "$SERVICE_CONTRACT" "$CLIENTS_DIR/$CONTRACT_FILENAME"
echo -e "${GREEN}✓ Service contract copied to scaffold${NC}"

# Step 6: Update scaffold config
CONFIG_FILE="$SCAFFOLD_DIR/src/scaffold/config.py"
if [ -f "$CONFIG_FILE" ]; then
    # Check if service URL already exists in config
    if grep -q "${SERVICE_NAME_UPPER}_SERVICE_URL" "$CONFIG_FILE"; then
        echo -e "${YELLOW}ℹ Service URL already exists in config, skipping${NC}"
    else
        # Add service URL to config
        echo "" >> "$CONFIG_FILE"
        echo "# $SERVICE_NAME service URL" >> "$CONFIG_FILE"
        echo "${SERVICE_NAME_UPPER}_SERVICE_URL: str = \"http://$SERVICE_NAME:$SERVICE_PORT\"" >> "$CONFIG_FILE"
        echo -e "${GREEN}✓ Service URL added to config${NC}"
    fi
else
    echo -e "${RED}Error: Config file not found at $CONFIG_FILE${NC}"
    exit 1
fi

# Step 7: Update docker-compose.yml
DOCKER_COMPOSE_FILE="$SCAFFOLD_DIR/docker-compose.yml"
if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    # Check if service already exists in docker-compose
    if grep -q "  $SERVICE_NAME:" "$DOCKER_COMPOSE_FILE"; then
        echo -e "${YELLOW}ℹ Service already exists in docker-compose, skipping${NC}"
    else
        # Add service to docker-compose
        SERVICE_INDENT="  "
        NESTED_INDENT="    "
        
        # Find the position to insert (before the last service or networks section)
        INSERT_LINE=$(grep -n "networks:" "$DOCKER_COMPOSE_FILE" | head -1 | cut -d: -f1)
        
        # Create temporary file with service definition
        TEMP_FILE=$(mktemp)
        echo "$SERVICE_INDENT$SERVICE_NAME:" >> "$TEMP_FILE"
        echo "$NESTED_INDENT"build: >> "$TEMP_FILE"
        echo "$NESTED_INDENT  context: ./$SERVICE_NAME" >> "$TEMP_FILE"
        echo "$NESTED_INDENT  dockerfile: Dockerfile" >> "$TEMP_FILE"
        echo "$NESTED_INDENT"container_name: $SERVICE_NAME >> "$TEMP_FILE"
        echo "$NESTED_INDENT"ports: >> "$TEMP_FILE"
        echo "$NESTED_INDENT  - \"$SERVICE_PORT:$SERVICE_PORT\"" >> "$TEMP_FILE"
        echo "$NESTED_INDENT"networks: >> "$TEMP_FILE"
        echo "$NESTED_INDENT  - scaffold-network" >> "$TEMP_FILE"
        echo "$NESTED_INDENT"restart: unless-stopped >> "$TEMP_FILE"
        echo "" >> "$TEMP_FILE"
        
        # Insert service definition into docker-compose.yml
        sed -i '' "${INSERT_LINE}i\\
$(cat "$TEMP_FILE")
" "$DOCKER_COMPOSE_FILE"
        
        rm "$TEMP_FILE"
        echo -e "${GREEN}✓ Service added to docker-compose${NC}"
    fi
else
    echo -e "${RED}Error: Docker Compose file not found at $DOCKER_COMPOSE_FILE${NC}"
    exit 1
fi

# Step 8: Verify service health endpoint
echo -e "${YELLOW}Verifying service health endpoint...${NC}"
if [ -d "./$SERVICE_NAME" ]; then
    # Check if service has a health endpoint
    HEALTH_FILES=$(grep -r "def health" "./$SERVICE_NAME" --include="*.py" | wc -l)
    if [ "$HEALTH_FILES" -gt 0 ]; then
        echo -e "${GREEN}✓ Health endpoint found${NC}"
    else
        echo -e "${RED}Warning: No health endpoint found in service. Please add a /health endpoint.${NC}"
    fi
else
    echo -e "${YELLOW}ℹ Service directory not found locally, skipping health endpoint check${NC}"
fi

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Integration completed successfully!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "1. Start your services: ${YELLOW}docker-compose up -d${NC}"
echo -e "2. Check logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "3. Test your integration with the examples"
echo ""
echo -e "For more information, see the documentation." 