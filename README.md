# Code Attachment to Scaffold

A template repository with tools and examples for integrating Docker-based microservices with a scaffold framework.

## Purpose

This repository provides a standardized approach for attaching your own Docker-based services with REST interfaces to a microservice scaffolding framework. It includes:

- Templates for service contracts
- Example integration patterns
- Scripts for automating the integration process
- Documentation for best practices

## Repository Structure

```
Code_Attachment_to_scaffold/
├── templates/             # Templates for integration
├── examples/              # Example services and integration code
├── scripts/               # Helper scripts for integration
├── docs/                  # Detailed documentation
└── dashboard_service/     # Complete dashboard service implementation
```

## Dashboard Service

A comprehensive dashboard service that provides real-time monitoring and control for agent scaffolding systems. This service receives and displays various types of messages from agents including compliance results, status updates, performance metrics, alerts, and informational messages.

## 🚀 Features

### Agent Message System
- **Compliance Messages**: Domain-specific compliance results with test tracking
- **Status Messages**: System and agent health information
- **Throughput Messages**: Performance metrics and KPIs  
- **Alert Messages**: Critical notifications with severity levels and expiration
- **Informational Messages**: General updates and operational logs

### Real-time Dashboard
- Modern web UI with live metrics
- WebSocket support for real-time updates
- Interactive API documentation
- Message categorization and filtering

### REST API Interface
- Health check endpoint for scaffolding integration
- Complete CRUD operations for agent messages
- Message retrieval by type and time
- File upload support for configuration

### Data Models
Each message includes:
- **Title**: Display name for the message
- **Type**: Message category (compliance, status, throughput, alert, informational)
- **Value**: The actual data (string, number, object, or array)
- **Presentation Method**: How to display (chart, table, gauge, text, graph, metric, list, badge)
- **Source Agent**: Which agent sent the message
- **Metadata**: Additional context and details

## 📋 Prerequisites

- Python 3.10+
- Docker (for containerization)
- curl or any HTTP client for testing

## 🛠 Installation

### Local Development

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd Dashboard_app_code
   ```

2. **Install dependencies**:
   ```bash
   cd dashboard_service
   pip install -r requirements.txt
   ```

3. **Run the service**:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

1. **Build the container**:
   ```bash
   cd dashboard_service
   docker build -t moa-agent-reporting-dashboard .
   ```

2. **Run the container**:
   ```bash
   docker run -d -p 8000:8000 --name moa-agent-reporting-dashboard moa-agent-reporting-dashboard
   ```

## 📊 API Endpoints

### Health & Info
- `GET /health` - Service health check (required by scaffolding)
- `GET /` - Dashboard web UI
- `GET /docs` - Interactive API documentation

### Agent Message Endpoints
- `POST /messages/compliance` - Send compliance messages
- `POST /messages/status` - Send status messages  
- `POST /messages/throughput` - Send throughput/performance messages
- `POST /messages/alert` - Send alert messages
- `POST /messages/informational` - Send informational messages

### Message Retrieval
- `GET /messages/recent?limit=50` - Get recent messages of all types
- `GET /messages/alerts` - Get active alerts
- `GET /messages/{type}?limit=100` - Get messages by type

### System Monitoring
- `GET /agent-status` - Current agent status
- `GET /llm-usage` - LLM usage statistics
- `GET /vector-status` - Vector store status
- `GET /compliance/summary` - Compliance overview

### Real-time Updates
- `WebSocket /ws/dashboard` - Real-time dashboard updates

## 🔧 Usage Examples

### Using the Service Contract

```python
from dashboard_service_contract import DashboardServiceContract

# Initialize contract
contract = DashboardServiceContract("http://localhost:8000")

# Send compliance message
result = contract.send_compliance_message(
    title="Supply Chain Compliance Check",
    value="compliant",
    presentation_method="badge",
    domain="supply_chain",
    status="compliant",
    test_id="sc_001",
    source_agent="compliance_agent"
)

# Send performance metric
result = contract.send_throughput_message(
    title="API Response Time",
    value=125.5,
    presentation_method="gauge",
    metric_name="response_time",
    unit="ms",
    target_value=100.0,
    source_agent="performance_agent"
)

# Send critical alert
result = contract.send_alert_message(
    title="Database Connection Lost",
    value="Unable to connect to primary database",
    presentation_method="text",
    severity="critical",
    category="infrastructure",
    action_required=True,
    source_agent="monitoring_agent"
)
```

### Using curl

```bash
# Health check
curl -X GET http://localhost:8000/health

# Send compliance message
curl -X POST http://localhost:8000/messages/compliance \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Security Audit",
    "value": "passed",
    "presentation_method": "badge",
    "domain": "physical_security",
    "status": "compliant",
    "source_agent": "security_agent"
  }'

# Get recent messages
curl -X GET http://localhost:8000/messages/recent?limit=10
```

## 🧪 Testing

Run the comprehensive test script:
```bash
python test_agent_messages.py
```

This script demonstrates:
- Health check verification
- Sending all message types
- Message retrieval
- Convenience methods for common operations

## 🐳 Scaffold Integration

The service is designed for integration with the agent scaffolding framework:

```bash
./integration_setup.sh \
  --service-name=moa-agent-reporting-dashboard \
  --service-port=8000 \
  --contract=../dashboard_service_contract.py
```

### Integration Features
- Standard health endpoint for service discovery
- Consistent response format across all endpoints
- Error handling with retry logic
- Service contract pattern for easy agent integration

## 🏗 Architecture

### Message Flow
1. **Agents** send messages via REST API or service contract
2. **Dashboard Service** receives, validates, and stores messages
3. **WebSocket** broadcasts real-time updates to connected clients
4. **Web UI** displays messages with appropriate presentation methods

### Data Storage
- In-memory storage for development (easily replaceable with database)
- Message categorization by type
- Automatic alert expiration handling
- Recent message caching (last 100 messages)

### Message Types & Presentation Methods

| Type | Purpose | Common Presentation Methods |
|------|---------|----------------------------|
| Compliance | Test results, audit outcomes | badge, table, chart |
| Status | Health, operational state | gauge, badge, text |
| Throughput | Performance metrics, KPIs | gauge, metric, chart |
| Alert | Critical notifications | text, badge (severity-based) |
| Informational | General updates, logs | text, list |

## 🛡 Error Handling

- Comprehensive input validation using Pydantic models
- Graceful degradation for missing optional fields
- Retry logic in service contract with exponential backoff
- Detailed error responses with service identification

## 📈 Monitoring & Observability

- Health check endpoint for external monitoring
- Request/response logging
- WebSocket connection management
- Message statistics and trends

## 🔮 Future Enhancements

- Database persistence (PostgreSQL, MongoDB)
- Message queuing (Redis, RabbitMQ)
- Authentication and authorization
- Message retention policies
- Advanced visualization components
- Historical analytics and reporting

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Check the `/docs` endpoint for API documentation
- Review log output for debugging information
- Test with the provided `test_agent_messages.py` script
- Verify health endpoint is accessible for scaffolding integration

## Setup

To set up your environment, run:
```bash
./setup_environment.sh
```

## Getting Started

See [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for detailed instructions on how to integrate your service.

## Features

- Standardized service contract pattern
- Automatic health check verification
- File upload handling
- Error handling and retry logic
- Docker Compose integration
- Complete dashboard service implementation
- WebSocket support for real-time monitoring

## Compliance

This repository provides templates and patterns that support compliance with NIST 800-53, XAI, and other frameworks. See the `docs/` directory for compliance requirements and best practices.

---
**Last updated:** 2025-05-29 