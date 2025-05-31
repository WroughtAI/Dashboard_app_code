#!/bin/bash
# Script to set up Python environment for Bias Reporting Agent
# This installs all the necessary packages used during testing and development

# Create a virtual environment (optional - uncomment to use)
# python -m venv test_env
# source test_env/bin/activate

echo "Installing dependencies for Bias Reporting Agent..."

# Base dependencies for data processing
pip install numpy==1.26.0 pandas==2.1.1

# Web service and API dependencies
pip install fastapi==0.104.1 httpx==0.25.0 uvicorn==0.23.2 pydantic==2.5.0 pydantic-settings==2.1.0
pip install python-multipart==0.0.6 requests==2.31.0

# Testing dependencies
pip install pytest==7.4.0 pytest-mock==3.11.1 pytest-cov==4.1.0

# Templating and rendering
pip install jinja2==3.1.2

# Configuration and schemas
pip install pyyaml==6.0.1 jsonschema==4.19.1

# Communication and networking
pip install websockets==11.0.3

# Vector database and ML fairness tools
pip install qdrant-client==1.7.0 fairlearn==0.9.0

# Create necessary directories if they don't exist
mkdir -p agent-shell-clean/src/agents/__pycache__
mkdir -p agent-shell-clean/tests/agents
mkdir -p agent-shell-clean/tests/services
mkdir -p agent-shell-clean/tests/integration
mkdir -p agent-shell-clean/tests/e2e

# Create __init__.py files if they don't exist
for dir in agent-shell-clean/src/agents agent-shell-clean/tests agent-shell-clean/tests/agents agent-shell-clean/tests/services agent-shell-clean/tests/integration agent-shell-clean/tests/e2e; do
  if [ ! -f "$dir/__init__.py" ]; then
    echo "# Test module for Bias Reporting Agent" > "$dir/__init__.py"
    echo "Created $dir/__init__.py"
  fi
done

echo "Environment setup complete!"
echo "To run tests, use: cd agent-shell-clean && python tests/run_all_tests.py" 