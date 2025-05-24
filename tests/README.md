# WroughtAI Agent-Scaffolding Integration Tests

This directory contains tests to verify that your service can be integrated with the WroughtAI Agent-Scaffolding framework.

## Test Overview

The test suite is divided into several parts:

1. **API Standards Tests** - Verify that your API follows the required standards for integration
2. **Example Service Functionality Tests** - Test if the example service works correctly as a standalone service
3. **Agent-Scaffolding Integration Tests** - Verify specific requirements for Agent-Scaffolding integration
4. **Docker Configuration Tests** - Test if your Docker configuration meets Agent-Scaffolding requirements

## Running the Tests

To run the tests, simply execute the test runner script:

```bash
# Make the script executable (if needed)
chmod +x run_tests.sh

# Run the tests
./run_tests.sh
```

## Test Requirements

The tests require the following:

- Python 3.7+
- pytest
- Docker (optional, for container tests)

All Python dependencies can be installed with:

```bash
pip install -r requirements.txt
```

## Integration Requirements

To ensure successful integration with the WroughtAI Agent-Scaffolding framework, your service must:

1. Expose a `/health` endpoint that returns status information in the format:
   ```json
   {
     "status": "healthy",
     "service": "your-service-name",
     "version": "1.0.0"
   }
   ```

2. Expose your service ports on `0.0.0.0` (not localhost/127.0.0.1) to allow external access

3. Package your service in a Docker container with appropriate configuration:
   - Specify a base image
   - Expose necessary ports
   - Use the proper entry point command

4. Follow REST API standards for consistency in request/response formats

## Test Files

- `test_api_standards.py` - Tests for API standards compliance
- `test_example_service.py` - Tests for the example service functionality
- `test_docker_integration.py` - Tests for Docker integration
- `test_scaffold_integration.py` - Tests specifically for Agent-Scaffolding integration

## Manual Integration Testing

For complete integration testing with the actual Agent-Scaffolding:

1. Clone the Agent-Scaffolding repository:
   ```bash
   git clone https://github.com/WroughtAI/Agent-Scaffolding.git
   ```

2. Follow the setup instructions in the Agent-Scaffolding documentation

3. Run the integration test with:
   ```bash
   TEST_INTEGRATION=1 pytest test_example_service.py::test_service_integration -v
   ``` 