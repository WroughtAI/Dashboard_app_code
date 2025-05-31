# Dashboard Agent Implementation

This document contains the full implementation code for the Dashboard Agent, which was moved to enable agent2agent communication.

## dashboard.py

```python
"""
src/agent_shell/interfaces/dashboard.py
Dashboard interface for Agent Shell, providing real-time monitoring and control.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel

# Local imports
from agent_shell.config import settings
from agent_shell.interfaces.vector_store import client as vector_client
from agent_shell.interfaces.llm_monitor import get_llm_stats
from agent_shell.interfaces.agent2agent import transport as a2a_transport
from agent_shell.compliance_testing import test_suite, TestSchedule

router = APIRouter()
templates = Jinja2Templates(directory="src/agent_shell/templates")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# Dashboard routes
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Real-time status endpoints
@router.get("/agent-status")
async def get_agent_status():
    """Get current agent status."""
    try:
        # Get active agents from A2A transport
        agents = await a2a_transport.get_active_agents()
        return {
            "count": len(agents),
            "agents": agents,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception("Failed to get agent status")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/llm-usage")
async def get_llm_usage():
    """Get LLM usage statistics."""
    try:
        stats = await get_llm_stats()
        return {
            "total_requests": stats["total_requests"],
            "success_rate": stats["success_rate"],
            "average_latency": stats["average_latency"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception("Failed to get LLM usage")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-status")
async def get_vector_status():
    """Get vector store status."""
    try:
        collections = vector_client.get_collections()
        return {
            "collections": len(collections),
            "total_vectors": sum(c["vectors_count"] for c in collections),
            "status": "healthy" if collections else "empty",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception("Failed to get vector store status")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-activity")
async def get_recent_activity():
    """Get recent system activity."""
    try:
        # This would typically come from a database or event log
        activities = [
            {
                "type": "llm_request",
                "agent": "agent1",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                "status": "success"
            }
            for i in range(5)
        ]
        return {"activities": activities}
    except Exception as e:
        logging.exception("Failed to get recent activity")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/llm-history")
async def get_llm_history():
    """Get LLM interaction history."""
    try:
        # This would typically come from a database
        history = [
            {
                "time": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                "agent": f"agent{i % 3 + 1}",
                "type": "completion",
                "status": "success"
            }
            for i in range(10)
        ]
        return {"history": history}
    except Exception as e:
        logging.exception("Failed to get LLM history")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-collections")
async def get_vector_collections():
    """Get vector store collections."""
    try:
        collections = vector_client.get_collections()
        return {
            "collections": [
                {
                    "name": c["name"],
                    "vectors": c["vectors_count"],
                    "status": "active"
                }
                for c in collections
            ]
        }
    except Exception as e:
        logging.exception("Failed to get vector collections")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vector-search")
async def search_vectors(query: str):
    """Search vector store."""
    try:
        results = vector_client.search(
            collection_name="default",
            query_vector=[0.1] * 1536,  # This should be generated from the query
            limit=5
        )
        return {
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]
        }
    except Exception as e:
        logging.exception("Failed to search vectors")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/package-status")
async def get_package_status():
    """Get package health status."""
    try:
        # This would typically check actual package health
        packages = [
            {
                "name": "llm-interface",
                "status": "healthy",
                "version": "1.0.0",
                "last_check": datetime.utcnow().isoformat()
            },
            {
                "name": "vector-store",
                "status": "healthy",
                "version": "1.0.0",
                "last_check": datetime.utcnow().isoformat()
            }
        ]
        return {"packages": packages}
    except Exception as e:
        logging.exception("Failed to get package status")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/dashboard")
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
                    "agents": await get_agent_status(),
                    "llm": await get_llm_usage()
                }
            }
            await websocket.send_json(update)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/compliance/test-results")
async def get_compliance_test_results(limit: int = 100):
    """Get recent compliance test results."""
    try:
        results = test_suite.get_recent_results(limit=limit)
        return {
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception("Failed to get compliance test results")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/domain/{domain}")
async def get_domain_test_results(domain: str, limit: int = 100):
    """Get test results for specific compliance domain."""
    try:
        results = test_suite.get_domain_results(domain=domain, limit=limit)
        return {
            "domain": domain,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception(f"Failed to get {domain} test results")
        raise HTTPException(status_code=500, detail=str(e))

class TestRunRequest(BaseModel):
    test_id: str

@router.post("/compliance/run-test")
async def run_compliance_test(request: TestRunRequest):
    """Run a specific compliance test."""
    try:
        result = await test_suite.run_single_test(request.test_id)
        return {
            "test_id": request.test_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception(f"Failed to run test {request.test_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/run-domain/{domain}")
async def run_domain_tests(domain: str):
    """Run all tests for a compliance domain."""
    try:
        results = await test_suite.run_domain_tests(domain)
        return {
            "domain": domain,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception(f"Failed to run {domain} tests")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/run-all")
async def run_all_compliance_tests():
    """Run all compliance tests."""
    try:
        results = await test_suite.run_all_tests()
        return {
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.exception("Failed to run all compliance tests")
        raise HTTPException(status_code=500, detail=str(e))

class TestScheduleRequest(BaseModel):
    test_id: str
    schedule: str

@router.post("/compliance/set-schedule")
async def set_test_schedule(request: TestScheduleRequest):
    """Set schedule for a compliance test."""
    try:
        schedule_obj = TestSchedule(request.test_id, request.schedule)
        test_suite.set_schedule(schedule_obj)
        return {
            "test_id": request.test_id,
            "schedule": request.schedule,
            "status": "scheduled"
        }
    except Exception as e:
        logging.exception(f"Failed to schedule test {request.test_id}")
        raise HTTPException(status_code=500, detail=str(e))

class TestEnableRequest(BaseModel):
    test_id: str
    enabled: bool

@router.post("/compliance/enable-test")
async def enable_test(request: TestEnableRequest):
    """Enable or disable a compliance test."""
    try:
        test_suite.set_test_enabled(request.test_id, request.enabled)
        return {
            "test_id": request.test_id,
            "enabled": request.enabled
        }
    except Exception as e:
        logging.exception(f"Failed to enable/disable test {request.test_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/summary")
async def get_compliance_summary():
    """Get overall compliance summary."""
    try:
        # Get summary statistics
        summary = {
            "overall_status": "compliant",
            "domains": {},
            "recent_failures": [],
            "upcoming_tests": []
        }
        
        # Check each domain
        domains = ["supply_chain", "physical_security", "explainable_ai", 
                  "perf_reliability", "nist800_53", "rmf", "fedramp"]
        
        for domain in domains:
            domain_results = test_suite.get_domain_results(domain, limit=10)
            if domain_results:
                latest = domain_results[0]
                summary["domains"][domain] = {
                    "status": latest.get("status", "unknown"),
                    "last_run": latest.get("timestamp"),
                    "pass_rate": sum(1 for r in domain_results if r.get("passed", False)) / len(domain_results)
                }
                
                # Check for recent failures
                failures = [r for r in domain_results if not r.get("passed", True)]
                summary["recent_failures"].extend(failures[:3])  # Add up to 3 failures per domain
        
        # Calculate overall status
        domain_statuses = [d["status"] for d in summary["domains"].values()]
        if "failed" in domain_statuses:
            summary["overall_status"] = "non_compliant"
        elif "warning" in domain_statuses:
            summary["overall_status"] = "needs_attention"
        
        return summary
        
    except Exception as e:
        logging.exception("Failed to get compliance summary")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/scheduler-status")
async def get_scheduler_status():
    """Get compliance test scheduler status."""
    try:
        return {
            "running": test_suite.scheduler.is_running if hasattr(test_suite, 'scheduler') else False,
            "scheduled_tests": test_suite.get_scheduled_tests() if hasattr(test_suite, 'get_scheduled_tests') else [],
            "last_run": test_suite.last_scheduled_run if hasattr(test_suite, 'last_scheduled_run') else None
        }
    except Exception as e:
        logging.exception("Failed to get scheduler status")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/start-scheduler")
async def start_scheduler():
    """Start the compliance test scheduler."""
    try:
        if hasattr(test_suite, 'start_scheduler'):
            test_suite.start_scheduler()
        return {"status": "scheduler_started"}
    except Exception as e:
        logging.exception("Failed to start scheduler")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/stop-scheduler")
async def stop_scheduler():
    """Stop the compliance test scheduler."""
    try:
        if hasattr(test_suite, 'stop_scheduler'):
            test_suite.stop_scheduler()
        return {"status": "scheduler_stopped"}
    except Exception as e:
        logging.exception("Failed to stop scheduler")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/report")
async def get_compliance_report():
    """Generate comprehensive compliance report."""
    try:
        from agents.compliance_agent.compliance_agent import ComplianceAgent
        agent = ComplianceAgent("compliance_dashboard")
        report = await agent.generate_compliance_report()
        return report
    except Exception as e:
        logging.exception("Failed to generate compliance report")
        raise HTTPException(status_code=500, detail=str(e))
``` 