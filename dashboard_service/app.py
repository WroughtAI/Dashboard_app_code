"""
Dashboard Service Application
FastAPI-based dashboard service that provides real-time monitoring and control.
Based on dashboard_agent_impl.md implementation.
Enhanced to receive agent messages via REST interface for scaffolding integration.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Optional, Any, Union
import json
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel, Field
from enum import Enum
import uvicorn
import os
import tempfile
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dashboard Service API",
    description="Dashboard service that provides real-time monitoring and control, integrates with the Scaffold Framework and receives agent messages",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums for message types and presentation methods
class MessageType(str, Enum):
    COMPLIANCE = "compliance"
    STATUS = "status"
    THROUGHPUT = "throughput"
    ALERT = "alert"
    INFORMATIONAL = "informational"

class PresentationMethod(str, Enum):
    CHART = "chart"
    TABLE = "table"
    GAUGE = "gauge"
    TEXT = "text"
    GRAPH = "graph"
    METRIC = "metric"
    LIST = "list"
    BADGE = "badge"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Pydantic models for agent messages
class DashboardMessage(BaseModel):
    """Base model for all dashboard messages from agents."""
    title: str = Field(..., description="Display title for the message")
    type: MessageType = Field(..., description="Type of message")
    value: Union[str, int, float, Dict[str, Any], List[Any]] = Field(..., description="The actual data value")
    presentation_method: PresentationMethod = Field(..., description="How to display this data")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Message timestamp")
    source_agent: Optional[str] = Field(None, description="Agent that sent this message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class ComplianceMessage(DashboardMessage):
    """Compliance-specific message with domain and status."""
    type: MessageType = Field(default=MessageType.COMPLIANCE, description="Message type")
    domain: Optional[str] = Field(None, description="Compliance domain (e.g., 'supply_chain', 'physical_security')")
    status: Optional[str] = Field(None, description="Compliance status (e.g., 'compliant', 'non_compliant')")
    test_id: Optional[str] = Field(None, description="Associated test identifier")

class StatusMessage(DashboardMessage):
    """Status message for system/agent health."""
    type: MessageType = Field(default=MessageType.STATUS, description="Message type")
    component: Optional[str] = Field(None, description="System component name")
    health_status: Optional[str] = Field(None, description="Health status (e.g., 'healthy', 'degraded', 'failed')")

class ThroughputMessage(DashboardMessage):
    """Throughput/performance metrics message."""
    type: MessageType = Field(default=MessageType.THROUGHPUT, description="Message type")
    metric_name: Optional[str] = Field(None, description="Performance metric name")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    target_value: Optional[float] = Field(None, description="Target or expected value")

class AlertMessage(DashboardMessage):
    """Alert message for important notifications."""
    type: MessageType = Field(default=MessageType.ALERT, description="Message type")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    category: Optional[str] = Field(None, description="Alert category")
    action_required: Optional[bool] = Field(False, description="Whether immediate action is required")
    expires_at: Optional[datetime] = Field(None, description="When alert expires")

class InformationalMessage(DashboardMessage):
    """General informational message."""
    type: MessageType = Field(default=MessageType.INFORMATIONAL, description="Message type")
    category: Optional[str] = Field(None, description="Information category")
    priority: Optional[str] = Field("normal", description="Display priority")

# Response models
class MessageResponse(BaseModel):
    """Standard response for message operations."""
    status: str
    service: str
    message_id: Optional[str] = None
    timestamp: datetime

# Global data storage (in production this would be a database)
dashboard_data = {
    "agents": [],
    "llm_stats": {
        "total_requests": 0,
        "success_rate": 0.95,
        "average_latency": 150
    },
    "vector_status": {
        "collections": 0,
        "total_vectors": 0,
        "status": "healthy"
    },
    "activities": [],
    "compliance_results": [],
    "messages": {
        "compliance": [],
        "status": [],
        "throughput": [],
        "alerts": [],
        "informational": []
    },
    "active_alerts": [],
    "recent_messages": []
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# Pydantic models for existing endpoints
class TestRunRequest(BaseModel):
    test_id: str

class TestScheduleRequest(BaseModel):
    test_id: str
    schedule: str

class TestEnableRequest(BaseModel):
    test_id: str
    enabled: bool

# Helper functions
def store_message(message: DashboardMessage) -> str:
    """Store a message and return its ID."""
    message_id = str(uuid.uuid4())
    message_dict = message.dict()
    message_dict["message_id"] = message_id
    message_dict["timestamp"] = message.timestamp.isoformat()
    
    # Store in appropriate category
    dashboard_data["messages"][message.type].append(message_dict)
    
    # Store in recent messages (last 100)
    dashboard_data["recent_messages"].insert(0, message_dict)
    if len(dashboard_data["recent_messages"]) > 100:
        dashboard_data["recent_messages"] = dashboard_data["recent_messages"][:100]
    
    # Handle alerts specially
    if message.type == MessageType.ALERT:
        alert_dict = message_dict.copy()
        if hasattr(message, 'expires_at') and message.expires_at:
            alert_dict["expires_at"] = message.expires_at.isoformat()
        dashboard_data["active_alerts"].insert(0, alert_dict)
        # Keep only active alerts (not expired)
        dashboard_data["active_alerts"] = [
            alert for alert in dashboard_data["active_alerts"]
            if not alert.get("expires_at") or datetime.fromisoformat(alert["expires_at"]) > datetime.utcnow()
        ]
    
    return message_id

async def broadcast_message_update(message: DashboardMessage, message_id: str):
    """Broadcast message updates to connected WebSocket clients."""
    update = {
        "type": "new_message",
        "message_type": message.type,
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": message.dict()
    }
    await manager.broadcast(update)

# Health check endpoint (required by scaffold integration)
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint required by scaffold framework."""
    return {
        "status": "healthy",
        "service": "dashboard-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# Enhanced Dashboard UI
@app.get("/", response_class=HTMLResponse)
async def dashboard_root():
    """Root dashboard endpoint with enhanced UI for agent messages and real-time updates."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agent Dashboard Service</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .header { 
                background: rgba(255,255,255,0.15); 
                color: white; 
                padding: 30px; 
                border-radius: 15px; 
                margin-bottom: 20px; 
                backdrop-filter: blur(10px);
                text-align: center;
            }
            .header h1 { margin: 0 0 10px 0; font-size: 2.5em; }
            .header p { margin: 0; opacity: 0.9; font-size: 1.1em; }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .card { 
                background: rgba(255,255,255,0.95); 
                padding: 25px; 
                border-radius: 12px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1); 
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .status { padding: 15px; margin: 10px 0; border-radius: 8px; font-weight: 500; }
            .healthy { background: linear-gradient(45deg, #4CAF50, #45a049); color: white; }
            .warning { background: linear-gradient(45deg, #ff9800, #f57c00); color: white; }
            .danger { background: linear-gradient(45deg, #f44336, #d32f2f); color: white; }
            .info { background: linear-gradient(45deg, #2196F3, #1976D2); color: white; }
            
            .metric { text-align: center; padding: 15px; }
            .metric-value { 
                font-size: 3em; 
                font-weight: bold; 
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .metric-label { color: #666; margin-top: 5px; font-size: 1.1em; }
            
            .endpoint-list { list-style: none; padding: 0; }
            .endpoint-list li { 
                padding: 12px 16px; 
                margin: 8px 0; 
                background: linear-gradient(45deg, #f8f9fa, #e9ecef); 
                border-radius: 8px; 
                transition: all 0.3s ease;
                border-left: 4px solid #667eea;
            }
            .endpoint-list li:hover { 
                transform: translateX(5px); 
                box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
            }
            .endpoint-list a { 
                text-decoration: none; 
                color: #495057; 
                font-weight: 500;
                display: flex;
                align-items: center;
            }
            .endpoint-list a:hover { color: #667eea; }
            
            .messages-section { 
                background: rgba(255,255,255,0.95); 
                border-radius: 12px; 
                padding: 25px; 
                margin-top: 20px;
                backdrop-filter: blur(10px);
            }
            
            .message-container { 
                max-height: 400px; 
                overflow-y: auto; 
                border: 1px solid #e9ecef; 
                border-radius: 8px; 
                padding: 15px; 
                background: #fafafa; 
            }
            
            .message-item { 
                background: white; 
                border-radius: 8px; 
                padding: 15px; 
                margin-bottom: 10px; 
                border-left: 4px solid #667eea; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            .message-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
            
            .message-title { font-weight: bold; color: #333; margin-bottom: 5px; }
            .message-value { color: #666; margin-bottom: 8px; }
            .message-meta { 
                font-size: 0.85em; 
                color: #999; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
            }
            
            .message-type { 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 0.75em; 
                font-weight: bold; 
                text-transform: uppercase; 
            }
            .type-compliance { background: #e8f5e8; color: #2e7d32; }
            .type-status { background: #e3f2fd; color: #1976d2; }
            .type-throughput { background: #fff3e0; color: #f57c00; }
            .type-alert { background: #ffebee; color: #d32f2f; }
            .type-informational { background: #f3e5f5; color: #7b1fa2; }
            
            .severity-critical { border-left-color: #d32f2f !important; }
            .severity-high { border-left-color: #ff5722 !important; }
            .severity-medium { border-left-color: #ff9800 !important; }
            .severity-low { border-left-color: #4caf50 !important; }
            
            .loading { text-align: center; color: #666; padding: 20px; }
            .update-indicator { 
                position: fixed; 
                top: 20px; 
                right: 20px; 
                background: #4caf50; 
                color: white; 
                padding: 10px 15px; 
                border-radius: 20px; 
                font-size: 0.9em;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            .update-indicator.show { opacity: 1; }
            
            .refresh-btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                margin: 10px 5px;
            }
            .refresh-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
            
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            .fade-in { animation: fadeIn 0.5s ease-out; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Agent Dashboard Service</h1>
                <p>Real-time monitoring and control for agent scaffolding system</p>
                <div style="margin-top: 15px;">
                    <button class="refresh-btn" onclick="refreshMessages()">🔄 Refresh Messages</button>
                    <button class="refresh-btn" onclick="clearMessages()">🗑️ Clear Display</button>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h2>🏥 Service Health</h2>
                    <div class="status healthy">
                        <h3>Status: Online & Ready</h3>
                        <p>Dashboard service is running and ready to receive agent messages.</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📊 Live Metrics</h2>
                    <div class="metric">
                        <div class="metric-value" id="agentCount">0</div>
                        <div class="metric-label">Active Agents</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="messageCount">0</div>
                        <div class="metric-label">Recent Messages</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔗 API Endpoints</h2>
                    <ul class="endpoint-list">
                        <li><a href="/docs" target="_blank">📚 API Documentation</a></li>
                        <li><a href="/health" target="_blank">💚 Health Check</a></li>
                        <li><a href="/messages/recent" target="_blank">📨 Recent Messages</a></li>
                        <li><a href="/messages/alerts" target="_blank">🚨 Active Alerts</a></li>
                        <li><a href="/agent-status" target="_blank">👥 Agent Status</a></li>
                        <li><a href="/compliance/summary" target="_blank">✅ Compliance Summary</a></li>
                    </ul>
                </div>
                
                <div class="card">
                    <h2>🎯 Message Types</h2>
                    <div class="status info">
                        <strong>📋 Compliance:</strong> Domain-specific compliance results<br><br>
                        <strong>💚 Status:</strong> System and agent health information<br><br>
                        <strong>⚡ Throughput:</strong> Performance metrics and KPIs<br><br>
                        <strong>🚨 Alerts:</strong> Critical notifications and warnings<br><br>
                        <strong>📝 Informational:</strong> General updates and logs
                    </div>
                </div>
            </div>
            
            <div class="messages-section">
                <h2>📨 Recent Agent Messages</h2>
                <p>Live feed of messages from agents - updates automatically every 5 seconds</p>
                <div class="message-container" id="messagesContainer">
                    <div class="loading">Loading messages...</div>
                </div>
            </div>
        </div>
        
        <div class="update-indicator" id="updateIndicator">
            📨 New messages received!
        </div>
        
        <script>
            let lastMessageCount = 0;
            
            function formatTimestamp(timestamp) {
                const date = new Date(timestamp);
                return date.toLocaleTimeString() + ' ' + date.toLocaleDateString();
            }
            
            function getMessageTypeClass(type) {
                return 'type-' + type.toLowerCase();
            }
            
            function getSeverityClass(message) {
                if (message.severity) {
                    return 'severity-' + message.severity.toLowerCase();
                }
                return '';
            }
            
            function createMessageElement(message) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message-item fade-in ${getSeverityClass(message)}`;
                
                const typeClass = getMessageTypeClass(message.type);
                const timestamp = formatTimestamp(message.timestamp);
                
                messageDiv.innerHTML = `
                    <div class="message-title">${message.title}</div>
                    <div class="message-value">${message.value}</div>
                    <div class="message-meta">
                        <span>
                            <span class="message-type ${typeClass}">${message.type}</span>
                            ${message.source_agent ? '• Agent: ' + message.source_agent : ''}
                            ${message.presentation_method ? '• Display: ' + message.presentation_method : ''}
                        </span>
                        <span>${timestamp}</span>
                    </div>
                `;
                
                return messageDiv;
            }
            
            async function updateMetrics() {
                try {
                    const [agentResponse, messageResponse] = await Promise.all([
                        fetch('/agent-status'),
                        fetch('/messages/recent?limit=20')
                    ]);
                    
                    const agentData = await agentResponse.json();
                    const messageData = await messageResponse.json();
                    
                    document.getElementById('agentCount').textContent = agentData.results?.count || 0;
                    document.getElementById('messageCount').textContent = messageData.results?.length || 0;
                    
                    return messageData.results || [];
                } catch (error) {
                    console.error('Error updating metrics:', error);
                    return [];
                }
            }
            
            async function updateMessages() {
                try {
                    const messages = await updateMetrics();
                    const container = document.getElementById('messagesContainer');
                    
                    if (messages.length === 0) {
                        container.innerHTML = '<div class="loading">No messages yet. Send some messages to see them appear here!</div>';
                        return;
                    }
                    
                    // Check if new messages arrived
                    if (messages.length > lastMessageCount && lastMessageCount > 0) {
                        showUpdateIndicator();
                    }
                    lastMessageCount = messages.length;
                    
                    // Clear and populate with latest messages
                    container.innerHTML = '';
                    messages.forEach(message => {
                        container.appendChild(createMessageElement(message));
                    });
                    
                } catch (error) {
                    console.error('Error updating messages:', error);
                    document.getElementById('messagesContainer').innerHTML = 
                        '<div class="loading">Error loading messages. Check console for details.</div>';
                }
            }
            
            function showUpdateIndicator() {
                const indicator = document.getElementById('updateIndicator');
                indicator.classList.add('show');
                setTimeout(() => {
                    indicator.classList.remove('show');
                }, 2000);
            }
            
            function refreshMessages() {
                updateMessages();
                showUpdateIndicator();
            }
            
            function clearMessages() {
                document.getElementById('messagesContainer').innerHTML = 
                    '<div class="loading">Display cleared. New messages will appear here.</div>';
            }
            
            // Initial load
            updateMessages();
            
            // Update every 5 seconds
            setInterval(updateMessages, 5000);
            
            // Also update metrics more frequently
            setInterval(updateMetrics, 2000);
            
            console.log('🚀 Dashboard loaded! Messages will update every 5 seconds.');
            console.log('📡 WebSocket connection available at /ws/dashboard');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Agent Message Endpoints
@app.post("/messages/compliance", response_model=MessageResponse)
async def receive_compliance_message(message: ComplianceMessage):
    """Receive compliance messages from agents."""
    try:
        message_id = store_message(message)
        await broadcast_message_update(message, message_id)
        
        logger.info(f"Received compliance message: {message.title} from {message.source_agent}")
        
        return MessageResponse(
            status="success",
            service="dashboard-service",
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing compliance message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages/status", response_model=MessageResponse)
async def receive_status_message(message: StatusMessage):
    """Receive status messages from agents."""
    try:
        message_id = store_message(message)
        await broadcast_message_update(message, message_id)
        
        logger.info(f"Received status message: {message.title} from {message.source_agent}")
        
        return MessageResponse(
            status="success",
            service="dashboard-service",
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing status message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages/throughput", response_model=MessageResponse)
async def receive_throughput_message(message: ThroughputMessage):
    """Receive throughput/performance messages from agents."""
    try:
        message_id = store_message(message)
        await broadcast_message_update(message, message_id)
        
        logger.info(f"Received throughput message: {message.title} from {message.source_agent}")
        
        return MessageResponse(
            status="success",
            service="dashboard-service",
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing throughput message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages/alert", response_model=MessageResponse)
async def receive_alert_message(message: AlertMessage):
    """Receive alert messages from agents."""
    try:
        message_id = store_message(message)
        await broadcast_message_update(message, message_id)
        
        logger.warning(f"Received {message.severity} alert: {message.title} from {message.source_agent}")
        
        return MessageResponse(
            status="success",
            service="dashboard-service",
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing alert message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages/informational", response_model=MessageResponse)
async def receive_informational_message(message: InformationalMessage):
    """Receive informational messages from agents."""
    try:
        message_id = store_message(message)
        await broadcast_message_update(message, message_id)
        
        logger.info(f"Received informational message: {message.title} from {message.source_agent}")
        
        return MessageResponse(
            status="success",
            service="dashboard-service",
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing informational message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Message Retrieval Endpoints
@app.get("/messages/recent")
async def get_recent_messages(limit: int = 50):
    """Get recent messages of all types."""
    try:
        recent = dashboard_data["recent_messages"][:limit]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": recent,
            "total": len(recent),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/messages/alerts")
async def get_active_alerts():
    """Get currently active alerts."""
    try:
        # Filter out expired alerts
        now = datetime.utcnow()
        active_alerts = [
            alert for alert in dashboard_data["active_alerts"]
            if not alert.get("expires_at") or datetime.fromisoformat(alert["expires_at"]) > now
        ]
        
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": active_alerts,
            "total": len(active_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/messages/{message_type}")
async def get_messages_by_type(message_type: MessageType, limit: int = 100):
    """Get messages of a specific type."""
    try:
        messages = dashboard_data["messages"].get(message_type, [])[-limit:]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": list(reversed(messages)),  # Most recent first
            "total": len(messages),
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting {message_type} messages: {e}")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

# Enhanced agent status endpoint
@app.get("/agent-status")
async def get_agent_status():
    """Get current agent status."""
    try:
        # Mock data - in production this would come from actual agent system
        agents = [
            {"id": "agent1", "name": "Dashboard Agent", "status": "active", "last_seen": datetime.utcnow().isoformat()},
            {"id": "agent2", "name": "Compliance Agent", "status": "active", "last_seen": datetime.utcnow().isoformat()},
            {"id": "agent3", "name": "Bias Agent", "status": "inactive", "last_seen": (datetime.utcnow() - timedelta(minutes=5)).isoformat()}
        ]
        dashboard_data["agents"] = agents
        
        # Add message counts per agent
        agent_message_counts = {}
        for message in dashboard_data["recent_messages"]:
            agent = message.get("source_agent", "unknown")
            agent_message_counts[agent] = agent_message_counts.get(agent, 0) + 1
        
        for agent in agents:
            agent["message_count"] = agent_message_counts.get(agent["name"], 0)
        
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "count": len(agents),
                "agents": agents,
                "message_counts": agent_message_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.exception("Failed to get agent status")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

# Keep existing endpoints for backward compatibility
@app.get("/llm-usage")
async def get_llm_usage():
    """Get LLM usage statistics."""
    try:
        # Mock data with some variance
        dashboard_data["llm_stats"]["total_requests"] += 1
        stats = dashboard_data["llm_stats"]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "total_requests": stats["total_requests"],
                "success_rate": stats["success_rate"],
                "average_latency": stats["average_latency"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.exception("Failed to get LLM usage")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/vector-status")
async def get_vector_status():
    """Get vector store status."""
    try:
        # Mock data
        collections = [
            {"name": "documents", "vectors_count": 1234},
            {"name": "embeddings", "vectors_count": 5678}
        ]
        total_vectors = sum(c["vectors_count"] for c in collections)
        
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "collections": len(collections),
                "total_vectors": total_vectors,
                "status": "healthy" if collections else "empty",
                "collections_detail": collections,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.exception("Failed to get vector store status")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/recent-activity")
async def get_recent_activity():
    """Get recent system activity."""
    try:
        # Generate mock activities
        activities = [
            {
                "type": "llm_request",
                "agent": "agent1",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                "status": "success",
                "details": f"Processed request #{100 - i}"
            }
            for i in range(10)
        ]
        dashboard_data["activities"] = activities
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "activities": activities
            }
        }
    except Exception as e:
        logger.exception("Failed to get recent activity")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/llm-history")
async def get_llm_history():
    """Get LLM interaction history."""
    try:
        history = [
            {
                "time": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                "agent": f"agent{i % 3 + 1}",
                "type": "completion",
                "status": "success",
                "tokens": 150 + (i * 10),
                "model": "gpt-4"
            }
            for i in range(20)
        ]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "history": history
            }
        }
    except Exception as e:
        logger.exception("Failed to get LLM history")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/vector-collections")
async def get_vector_collections():
    """Get vector store collections."""
    try:
        collections = [
            {"name": "documents", "vectors": 1234, "status": "active"},
            {"name": "embeddings", "vectors": 5678, "status": "active"},
            {"name": "knowledge_base", "vectors": 9012, "status": "active"}
        ]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "collections": collections
            }
        }
    except Exception as e:
        logger.exception("Failed to get vector collections")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.post("/vector-search")
async def search_vectors(query: str):
    """Search vector store."""
    try:
        # Mock search results
        results = [
            {
                "id": f"doc_{i}",
                "score": 0.95 - (i * 0.1),
                "payload": {
                    "title": f"Document {i}",
                    "content": f"Content related to query: {query}"
                }
            }
            for i in range(5)
        ]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "query": query,
                "results": results
            }
        }
    except Exception as e:
        logger.exception("Failed to search vectors")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/package-status")
async def get_package_status():
    """Get package health status."""
    try:
        packages = [
            {
                "name": "dashboard-service",
                "status": "healthy",
                "version": "1.0.0",
                "last_check": datetime.utcnow().isoformat()
            },
            {
                "name": "fastapi",
                "status": "healthy",
                "version": "0.115.0",
                "last_check": datetime.utcnow().isoformat()
            },
            {
                "name": "uvicorn",
                "status": "healthy",
                "version": "0.24.0",
                "last_check": datetime.utcnow().isoformat()
            }
        ]
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "packages": packages
            }
        }
    except Exception as e:
        logger.exception("Failed to get package status")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

# File upload endpoint (following scaffold pattern)
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Process an uploaded file for dashboard configuration or data import.
    
    Args:
        file: Uploaded file (JSON, CSV, etc.)
        options: Optional processing parameters as JSON string
        
    Returns:
        Dict: Processing results
    """
    try:
        # Parse options if provided
        process_options = {}
        if options:
            process_options = json.loads(options)
            
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
        
        try:
            # Process the file based on type
            if file.filename.endswith('.json'):
                # Process as JSON configuration
                with open(temp_path, 'r') as f:
                    data = json.load(f)
                
                summary = {
                    "file_type": "json",
                    "keys": list(data.keys()) if isinstance(data, dict) else [],
                    "size_bytes": len(content),
                    "processed": True
                }
            else:
                # Generic file processing
                summary = {
                    "file_type": "unknown",
                    "size_bytes": len(content),
                    "processed": True
                }
                
            return {
                "status": "success",
                "service": "dashboard-service",
                "filename": file.filename,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {
                "status": "error",
                "service": "dashboard-service",
                "error": f"Error processing file: {str(e)}"
            }
        finally:
            # Cleanup temporary file
            os.unlink(temp_path)
            
    except json.JSONDecodeError:
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": "Invalid options format"
        }
    except Exception as e:
        logger.error(f"Error processing file upload: {e}")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

# Compliance endpoints
@app.get("/compliance/test-results")
async def get_compliance_test_results(limit: int = 100):
    """Get recent compliance test results."""
    try:
        # Include both mock data and real compliance messages
        compliance_messages = dashboard_data["messages"]["compliance"][-limit//2:]
        
        # Mock compliance results
        mock_results = [
            {
                "test_id": f"test_{i}",
                "domain": ["supply_chain", "physical_security", "explainable_ai"][i % 3],
                "status": "passed" if i % 4 != 0 else "failed",
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "details": f"Test result details for test {i}"
            }
            for i in range(min(limit//2, 25))
        ]
        
        # Combine real and mock data
        all_results = compliance_messages + mock_results
        dashboard_data["compliance_results"] = all_results
        
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": {
                "results": all_results,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.exception("Failed to get compliance test results")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

@app.get("/compliance/summary")
async def get_compliance_summary():
    """Get overall compliance summary."""
    try:
        # Calculate summary from actual compliance messages
        compliance_messages = dashboard_data["messages"]["compliance"]
        
        domain_stats = {}
        for msg in compliance_messages:
            domain = msg.get("domain", "unknown")
            if domain not in domain_stats:
                domain_stats[domain] = {"passed": 0, "failed": 0, "total": 0}
            
            status = msg.get("status", "unknown")
            if status in ["passed", "compliant"]:
                domain_stats[domain]["passed"] += 1
            elif status in ["failed", "non_compliant"]:
                domain_stats[domain]["failed"] += 1
            domain_stats[domain]["total"] += 1
        
        # Add default domains with mock data if no real data
        default_domains = {
            "supply_chain": {"status": "compliant", "last_run": datetime.utcnow().isoformat(), "pass_rate": 0.95},
            "physical_security": {"status": "compliant", "last_run": datetime.utcnow().isoformat(), "pass_rate": 0.92},
            "explainable_ai": {"status": "needs_attention", "last_run": datetime.utcnow().isoformat(), "pass_rate": 0.87}
        }
        
        # Update with real data
        for domain, stats in domain_stats.items():
            if stats["total"] > 0:
                pass_rate = stats["passed"] / stats["total"]
                status = "compliant" if pass_rate >= 0.9 else "needs_attention" if pass_rate >= 0.7 else "non_compliant"
                default_domains[domain] = {
                    "status": status,
                    "last_run": datetime.utcnow().isoformat(),
                    "pass_rate": pass_rate
                }
        
        summary = {
            "overall_status": "compliant",
            "domains": default_domains,
            "recent_failures": [],
            "upcoming_tests": [],
            "total_messages": len(compliance_messages),
            "active_alerts": len(dashboard_data["active_alerts"])
        }
        
        return {
            "status": "success",
            "service": "dashboard-service",
            "results": summary
        }
        
    except Exception as e:
        logger.exception("Failed to get compliance summary")
        return {
            "status": "error",
            "service": "dashboard-service",
            "error": str(e)
        }

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            update = {
                "type": "status_update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "agents": len(dashboard_data.get("agents", [])),
                    "llm_requests": dashboard_data["llm_stats"]["total_requests"],
                    "compliance_status": "healthy",
                    "recent_messages": len(dashboard_data["recent_messages"]),
                    "active_alerts": len(dashboard_data["active_alerts"]),
                    "message_counts": {
                        "compliance": len(dashboard_data["messages"]["compliance"]),
                        "status": len(dashboard_data["messages"]["status"]),
                        "throughput": len(dashboard_data["messages"]["throughput"]),
                        "alerts": len(dashboard_data["messages"]["alert"]),
                        "informational": len(dashboard_data["messages"]["informational"])
                    }
                }
            }
            await websocket.send_json(update)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 