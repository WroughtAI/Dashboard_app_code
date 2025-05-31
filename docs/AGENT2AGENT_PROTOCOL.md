# Agent2Agent Protocol Integration for Bias Reporting Agent

This document describes the requirements for integrating the Bias Reporting Agent with the agent2agent protocol, enabling seamless communication with other agents in the ecosystem.

## Protocol Overview

The agent2agent protocol is a standardized communication interface that allows different AI agents to communicate with each other, share information, and coordinate activities. For the Bias Reporting Agent, this protocol enables:

1. Receiving bias analysis requests from other agents
2. Reporting bias detection results to requesting agents
3. Coordinating with other compliance and security agents in the ecosystem

## Integration Requirements

### 1. Message Format

All messages exchanged through the agent2agent protocol must follow this structure:

```json
{
  "message_id": "unique-message-identifier",
  "sender": "agent-identifier",
  "recipient": "recipient-identifier",
  "message_type": "request|response|notification",
  "timestamp": "ISO-8601-timestamp",
  "content": {
    // Message-specific content
  },
  "metadata": {
    // Optional metadata
  }
}
```

### 2. Required Endpoints

The Bias Reporting Agent must implement the following endpoints to comply with the agent2agent protocol:

#### 2.1 Receive Analysis Request

**Endpoint:** `/api/v1/bias/analyze`  
**Method:** POST  
**Description:** Receives a request to analyze content for bias  
**Request Structure:**

```json
{
  "content_type": "text|data|model",
  "content": "Content to analyze or reference to content",
  "analysis_type": "demographic|location|name|comprehensive",
  "parameters": {
    // Optional parameters specific to the analysis type
  }
}
```

#### 2.2 Get Analysis Status

**Endpoint:** `/api/v1/bias/status/{request_id}`  
**Method:** GET  
**Description:** Get the status of a previously submitted analysis request

#### 2.3 Get Analysis Results

**Endpoint:** `/api/v1/bias/results/{request_id}`  
**Method:** GET  
**Description:** Get the results of a completed analysis

### 3. Integration with Service Contracts

The agent2agent protocol layer must translate between protocol messages and the service contracts provided in the templates. The following mappings should be implemented:

- Map `/api/v1/bias/analyze` requests to appropriate service contract calls:
  - For demographic analysis → BiasDetector and FairLens services
  - For location analysis → BiasDetector service
  - For name analysis → BiasDetector service
  - For comprehensive analysis → All services + Aggregator

### 4. Authentication and Security

All agent2agent communications must include proper authentication. The protocol implementation should:

1. Validate incoming message signatures
2. Sign outgoing messages
3. Enforce access control based on agent identities
4. Log all communications for audit purposes

### 5. Error Handling

The protocol implementation must handle errors gracefully and return standardized error responses:

```json
{
  "error_code": "error-identifier",
  "error_message": "Human-readable error message",
  "timestamp": "ISO-8601-timestamp",
  "request_id": "original-request-id"
}
```

## Integration Steps

1. Create an agent2agent protocol adapter class that implements the required interfaces
2. Register the Bias Reporting Agent with the agent registry
3. Implement message handlers for each supported operation
4. Connect the protocol adapter to the BiasReportAgent implementation
5. Configure authentication and security settings
6. Test the protocol integration with mock agents

## Docker Integration

When deploying in Docker, ensure the following:

1. Expose the agent2agent protocol endpoints (default port: 7000)
2. Configure network settings to allow agent-to-agent communication
3. Include authentication credentials in a secure manner
4. Set up proper logging for protocol interactions

## Testing the Integration

The following tests should be performed to verify protocol integration:

1. Send a valid analysis request and verify proper handling
2. Send malformed requests and verify error handling
3. Test authentication with valid and invalid credentials
4. Test concurrent requests handling
5. Verify proper translation between protocol messages and service calls

## Example Implementation

A basic implementation of the agent2agent protocol adapter might look like:

```python
class BiasAgent2AgentAdapter:
    def __init__(self, bias_agent, config):
        self.bias_agent = bias_agent
        self.config = config
        self.auth_handler = AuthenticationHandler(config)
        
    async def handle_message(self, message):
        # Validate message
        if not self.auth_handler.validate_message(message):
            return self._create_error_response("UNAUTHORIZED", "Invalid authentication")
            
        # Process by message type
        if message["message_type"] == "request":
            return await self._handle_request(message)
        elif message["message_type"] == "response":
            return await self._handle_response(message)
        else:
            return self._create_error_response("INVALID_TYPE", "Unsupported message type")
    
    async def _handle_request(self, message):
        content = message["content"]
        
        if "operation" not in content:
            return self._create_error_response("INVALID_REQUEST", "Missing operation")
            
        # Map to appropriate operations
        if content["operation"] == "analyze_bias":
            result = await self.bias_agent.analyze_content(
                content_type=content.get("content_type", "text"),
                content=content.get("content", ""),
                analysis_type=content.get("analysis_type", "comprehensive")
            )
            return self._create_response(message["message_id"], result)
        
        # Other operations...
        
        return self._create_error_response("UNSUPPORTED", "Unsupported operation")
```

## Conclusion

Implementing the agent2agent protocol for the Bias Reporting Agent enables it to participate in the larger ecosystem of AI agents. By following these integration requirements, developers can create a wrapper that allows the bias analysis services to be seamlessly integrated with the agent scaffold. 