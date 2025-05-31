#!/usr/bin/env python3
"""
Test script for Dashboard Agent Message System
Demonstrates how agents would send different types of messages to the dashboard.
"""

import time
import json
from datetime import datetime, timedelta
from dashboard_service_contract import DashboardServiceContract

def test_agent_messages():
    """Test sending various types of agent messages to the dashboard."""
    
    print("🧪 Testing Dashboard Agent Message System")
    print("=" * 50)
    
    # Initialize the contract
    contract = DashboardServiceContract("http://localhost:8000")
    
    # Test 1: Health Check
    print("\n1. Testing health check...")
    try:
        health = contract.health_check()
        print(f"✅ Health check: {health['status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test 2: Compliance Messages
    print("\n2. Testing compliance messages...")
    try:
        compliance_result = contract.send_compliance_message(
            title="Supply Chain Compliance Check",
            value="compliant",
            presentation_method="badge",
            domain="supply_chain", 
            status="compliant",
            test_id="sc_compliance_001",
            source_agent="compliance_agent",
            metadata={"test_duration": "30s", "score": 95}
        )
        print(f"✅ Compliance message sent: {compliance_result['message_id']}")
        
        # Send a non-compliant result
        non_compliance_result = contract.send_compliance_message(
            title="Physical Security Audit",
            value="non_compliant",
            presentation_method="table",
            domain="physical_security",
            status="non_compliant", 
            test_id="ps_audit_002",
            source_agent="security_agent",
            metadata={"violations": 3, "critical_issues": 1}
        )
        print(f"✅ Non-compliance message sent: {non_compliance_result['message_id']}")
        
    except Exception as e:
        print(f"❌ Compliance message failed: {e}")
    
    # Test 3: Status Messages
    print("\n3. Testing status messages...")
    try:
        status_result = contract.send_status_message(
            title="Database Health Status",
            value="healthy",
            presentation_method="gauge",
            component="postgresql_db",
            health_status="healthy",
            source_agent="monitoring_agent",
            metadata={"cpu_usage": 45, "memory_usage": 60, "connections": 23}
        )
        print(f"✅ Status message sent: {status_result['message_id']}")
        
        # Send a degraded status
        degraded_result = contract.send_status_message(
            title="API Gateway Performance",
            value="degraded",
            presentation_method="chart",
            component="api_gateway",
            health_status="degraded",
            source_agent="performance_agent",
            metadata={"response_time_spike": True, "error_rate": 5.2}
        )
        print(f"✅ Degraded status message sent: {degraded_result['message_id']}")
        
    except Exception as e:
        print(f"❌ Status message failed: {e}")
    
    # Test 4: Throughput Messages
    print("\n4. Testing throughput messages...")
    try:
        throughput_result = contract.send_throughput_message(
            title="API Request Throughput",
            value=1250,
            presentation_method="metric",
            metric_name="requests_per_minute",
            unit="req/min",
            target_value=1000,
            source_agent="metrics_agent",
            metadata={"peak_time": "14:30", "trend": "increasing"}
        )
        print(f"✅ Throughput message sent: {throughput_result['message_id']}")
        
        # Send latency metric
        latency_result = contract.send_throughput_message(
            title="Average Response Latency",
            value=125.5,
            presentation_method="gauge",
            metric_name="avg_latency",
            unit="ms",
            target_value=100.0,
            source_agent="performance_agent",
            metadata={"p95_latency": 200, "p99_latency": 350}
        )
        print(f"✅ Latency message sent: {latency_result['message_id']}")
        
    except Exception as e:
        print(f"❌ Throughput message failed: {e}")
    
    # Test 5: Alert Messages
    print("\n5. Testing alert messages...")
    try:
        # Send a critical alert
        alert_result = contract.send_alert_message(
            title="Critical: Database Connection Pool Exhausted",
            value="All database connections are in use. New requests failing.",
            presentation_method="text",
            severity="critical",
            category="infrastructure",
            action_required=True,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            source_agent="monitoring_agent",
            metadata={"affected_services": ["api", "web"], "connection_pool_size": 100}
        )
        print(f"✅ Critical alert sent: {alert_result['message_id']}")
        
        # Send a warning alert
        warning_result = contract.send_alert_message(
            title="Warning: High Memory Usage",
            value="Memory usage at 85% on production server",
            presentation_method="gauge",
            severity="medium",
            category="performance",
            action_required=False,
            source_agent="system_monitor",
            metadata={"server": "prod-web-01", "memory_used": "6.8GB", "memory_total": "8GB"}
        )
        print(f"✅ Warning alert sent: {warning_result['message_id']}")
        
    except Exception as e:
        print(f"❌ Alert message failed: {e}")
    
    # Test 6: Informational Messages  
    print("\n6. Testing informational messages...")
    try:
        info_result = contract.send_informational_message(
            title="Daily Backup Completed",
            value="Backup operation completed successfully",
            presentation_method="text",
            category="maintenance",
            priority="normal",
            source_agent="backup_agent",
            metadata={"backup_size": "2.3GB", "duration": "45 minutes", "location": "s3://backups/daily/"}
        )
        print(f"✅ Informational message sent: {info_result['message_id']}")
        
    except Exception as e:
        print(f"❌ Informational message failed: {e}")
    
    # Test 7: Retrieve Messages
    print("\n7. Testing message retrieval...")
    try:
        recent_messages = contract.get_recent_messages(limit=5)
        print(f"✅ Retrieved {recent_messages['total']} recent messages")
        
        alerts = contract.get_active_alerts()
        print(f"✅ Retrieved {alerts['total']} active alerts")
        
        compliance_messages = contract.get_messages_by_type("compliance", limit=10)
        print(f"✅ Retrieved {compliance_messages['total']} compliance messages")
        
    except Exception as e:
        print(f"❌ Message retrieval failed: {e}")
    
    # Test 8: Convenience Methods
    print("\n8. Testing convenience methods...")
    try:
        # Report agent health
        health_result = contract.report_agent_health(
            agent_name="data_processor",
            health_status="healthy",
            details={"uptime": "5 days", "processed_items": 15000}
        )
        print(f"✅ Agent health reported: {health_result['message_id']}")
        
        # Report compliance result
        compliance_result = contract.report_compliance_result(
            domain="explainable_ai",
            test_id="xai_test_001",
            status="passed",
            details={"explanation_coverage": 95, "bias_score": 0.12}
        )
        print(f"✅ Compliance result reported: {compliance_result['message_id']}")
        
        # Report performance metric
        perf_result = contract.report_performance_metric(
            metric_name="model_accuracy",
            value=0.94,
            unit="percentage",
            target=0.90
        )
        print(f"✅ Performance metric reported: {perf_result['message_id']}")
        
    except Exception as e:
        print(f"❌ Convenience methods failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Agent message testing completed!")
    print("\nTo view the dashboard:")
    print("- Open http://localhost:8000 in your browser")
    print("- Check API docs: http://localhost:8000/docs")
    print("- View recent messages: http://localhost:8000/messages/recent")

if __name__ == "__main__":
    test_agent_messages() 