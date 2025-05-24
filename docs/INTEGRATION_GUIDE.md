# Service Integration Guide

This guide provides detailed instructions for integrating your Docker-based microservices with the scaffold framework.

## Integration Process Overview

1. **Prepare your service**
   - Implement required REST endpoints
   - Create a service contract
   - Prepare Docker configuration

2. **Run the integration script**
   - Copy contracts to the scaffold framework
   - Update configuration files
   - Add service to Docker Compose

3. **Verify the integration**
   - Run health checks
   - Test the integration
   - Deploy to production

## Step 1: Prepare Your Service

### 1.1 Required REST Endpoints

Your service must implement these standard endpoints:

#### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "your-service-name",
        "version": "1.0.0"
    }
```

#### File Upload Endpoint (if applicable)

```python
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
):
    """Process an uploaded file."""
    # Implementation details...
    return {
        "status": "success",
        "service": "your-service-name",
        "results": [...]
    }
```

### 1.2 Create a Service Contract

Create a Python class that extends `BaseRESTAdapter` and implements methods for each of your service's endpoints:

```python
from typing import Dict, Any, Optional
import os
from .base_rest_adapter import BaseRESTAdapter

class YourServiceContract(BaseRESTAdapter):
    """Service contract for your service."""
    
    def __init__(self):
        url = os.getenv("YOUR_SERVICE_URL", "http://your-service:8000")
        super().__init__(url)
    
    def health_check(self) -> Dict[str, str]:
        """Check if your service is healthy."""
        return self.call("/health", {}, method="GET")
    
    def your_method(self, param1: str) -> Dict[str, Any]:
        """Example method for your service."""
        data = {"param1": param1}
        return self.call("/your-endpoint", data)
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a file with your service."""
        return self.upload_file("/upload", file_path)
```

Save this file as `your_service_contract.py`.

### 1.3 Prepare Docker Configuration

Ensure your Dockerfile includes:

1. Health check configuration
2. Proper port exposure
3. Installation of required dependencies

```dockerfile
FROM python:3.10-slim

# Standard setup...

# Expose the service port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Step 2: Run the Integration Script

### 2.1 Basic Integration

Run the integration script with your service details:

```bash
cd scripts
./integration_setup.sh \
  --service-name=your-service \
  --service-port=8000 \
  --contract=../path/to/your_service_contract.py
```

### 2.2 Advanced Options

For more complex integrations, additional options are available:

```bash
./integration_setup.sh \
  --service-name=your-service \
  --service-port=8000 \
  --contract=../path/to/your_service_contract.py \
  --scaffold-dir=../../other-scaffold-location
```

## Step 3: Verify the Integration

### 3.1 Run Health Checks

Use the health check script to verify all services are running properly:

```bash
cd scripts
./health_check.sh
```

Or check a specific service:

```bash
./health_check.sh --service=your-service
```

### 3.2 Test the Integration

Use the example code to test your integration:

```python
from scaffold.clients.your_service_contract import YourServiceContract

# Initialize the service
service = YourServiceContract()

# Check health
health = service.health_check()
print(f"Service health: {health}")

# Use your service methods
result = service.your_method("test parameter")
print(f"Method result: {result}")
```

## Troubleshooting

### Common Issues

1. **Service not found**: Check the service name and port in docker-compose.yml
2. **Connection refused**: Ensure your service is running and exposing the correct port
3. **Health check failing**: Verify the /health endpoint is implemented correctly

### Debugging Tools

- Check service logs: `docker-compose logs -f your-service`
- Verify network connectivity: `docker network inspect scaffold-network`
- Test endpoints directly: `curl http://localhost:8000/health`

## Best Practices

1. **Standardized responses**: All endpoints should return consistent JSON structures
2. **Error handling**: Implement proper error handling and return appropriate status codes
3. **Logging**: Add comprehensive logging to your service
4. **Documentation**: Document your service contract and endpoints
5. **Testing**: Write tests for your service contract

## Advanced Integration

### Custom Authentication

If your service requires authentication:

```python
def your_authenticated_method(self, token: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Call an authenticated endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    return self.call("/secured-endpoint", data, headers=headers)
```

### Using WebSockets

For real-time communication:

```python
async def connect_websocket(self, callback):
    """Connect to WebSocket endpoint."""
    # Implementation details...
```

## Additional Resources

- [Service Contract Pattern Documentation](../SERVICE_CONTRACT_GUIDE.md)
- [Example Service Implementation](../examples/example_service)
- [Template Files](../templates) 