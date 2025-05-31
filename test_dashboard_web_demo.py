#!/usr/bin/env python3
"""
Dashboard Web Interface Demo
Demonstrates sending messages to the dashboard and viewing them on the web interface.
"""

import time
import json
import webbrowser
from datetime import datetime, timedelta
from dashboard_service_contract import DashboardServiceContract

def dashboard_web_demo():
    """Demonstrate the dashboard web interface with live message sending."""
    
    print("🌐 Dashboard Web Interface Demo")
    print("=" * 60)
    
    # Initialize the contract
    dashboard_url = "http://localhost:8000"
    contract = DashboardServiceContract(dashboard_url)
    
    # Test health check first
    print("\n1. Checking dashboard service health...")
    try:
        health = contract.health_check()
        print(f"✅ Dashboard service is {health['status']}")
    except Exception as e:
        print(f"❌ Dashboard service is not running: {e}")
        print("Please start the dashboard service first:")
        print("cd dashboard_service && uvicorn app:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # Open the dashboard in the browser
    print(f"\n2. Opening dashboard web interface...")
    print(f"🌐 Dashboard URL: {dashboard_url}")
    print(f"📚 API Documentation: {dashboard_url}/docs")
    print(f"📨 Recent Messages: {dashboard_url}/messages/recent")
    
    try:
        webbrowser.open(dashboard_url)
        print("✅ Dashboard opened in your default browser")
    except Exception as e:
        print(f"⚠️  Could not auto-open browser: {e}")
        print(f"Please manually open: {dashboard_url}")
    
    print("\n" + "⏰ DEMO INSTRUCTIONS" + "=" * 45)
    print("1. Keep the dashboard web page open in your browser")
    print("2. Watch the 'Recent Messages' count update in real-time")
    print("3. Check /messages/recent endpoint to see new messages")
    print("4. Observe different message types and presentation methods")
    print("=" * 60)
    
    input("\nPress ENTER when you have the dashboard open and ready...")
    
    # Demo 1: Send a critical alert
    print("\n🚨 DEMO 1: Sending Critical Alert")
    print("-" * 40)
    
    alert_result = contract.send_alert_message(
        title="🔴 Critical System Alert",
        value="Database connection pool exhausted - immediate action required!",
        presentation_method="text",
        severity="critical",
        category="infrastructure",
        action_required=True,
        expires_at=datetime.utcnow() + timedelta(hours=2),
        source_agent="monitoring_agent",
        metadata={
            "affected_services": ["api", "web", "mobile"],
            "connection_pool_size": 100,
            "current_connections": 100,
            "error_rate": "25%"
        }
    )
    
    print(f"✅ Critical alert sent! Message ID: {alert_result['message_id']}")
    print(f"💡 Check the dashboard - you should see this alert appear!")
    print(f"🔗 Direct link: {dashboard_url}/messages/alerts")
    
    time.sleep(2)
    
    # Demo 2: Send compliance status
    print("\n📋 DEMO 2: Sending Compliance Status")
    print("-" * 40)
    
    compliance_result = contract.send_compliance_message(
        title="🛡️ Supply Chain Security Audit",
        value="compliant",
        presentation_method="badge",
        domain="supply_chain",
        status="compliant",
        test_id="sc_audit_2024_001",
        source_agent="compliance_agent",
        metadata={
            "audit_score": 95,
            "duration": "2 hours",
            "vendor_checks": 15,
            "vulnerabilities_found": 0
        }
    )
    
    print(f"✅ Compliance message sent! Message ID: {compliance_result['message_id']}")
    print(f"💡 This should appear as a compliance badge on the dashboard!")
    
    time.sleep(2)
    
    # Demo 3: Send performance metrics
    print("\n📊 DEMO 3: Sending Performance Metrics")
    print("-" * 40)
    
    performance_result = contract.send_throughput_message(
        title="⚡ API Response Time",
        value=156.7,
        presentation_method="gauge",
        metric_name="avg_response_time",
        unit="milliseconds",
        target_value=100.0,
        source_agent="performance_agent",
        metadata={
            "p95_latency": 245,
            "p99_latency": 380,
            "total_requests": 15420,
            "error_count": 12
        }
    )
    
    print(f"✅ Performance metric sent! Message ID: {performance_result['message_id']}")
    print(f"💡 This should show as a gauge visualization!")
    
    time.sleep(2)
    
    # Demo 4: Send system status
    print("\n💚 DEMO 4: Sending System Health Status")
    print("-" * 40)
    
    status_result = contract.send_status_message(
        title="🏥 Database Cluster Health",
        value="healthy",
        presentation_method="badge",
        component="postgresql_cluster",
        health_status="healthy",
        source_agent="health_monitor",
        metadata={
            "primary_node": "healthy",
            "replica_nodes": 3,
            "cpu_usage": 35,
            "memory_usage": 62,
            "disk_usage": 45
        }
    )
    
    print(f"✅ Health status sent! Message ID: {status_result['message_id']}")
    print(f"💡 This should appear as a green health badge!")
    
    time.sleep(2)
    
    # Demo 5: Send informational update
    print("\n📝 DEMO 5: Sending Informational Update")
    print("-" * 40)
    
    info_result = contract.send_informational_message(
        title="📦 System Backup Completed",
        value="Daily backup operation completed successfully with 2.3GB archived",
        presentation_method="text",
        category="maintenance",
        priority="normal",
        source_agent="backup_service",
        metadata={
            "backup_size": "2.3GB",
            "duration": "45 minutes",
            "files_archived": 15847,
            "location": "s3://prod-backups/daily/2024-05-31/"
        }
    )
    
    print(f"✅ Informational message sent! Message ID: {info_result['message_id']}")
    print(f"💡 This should appear as regular informational text!")
    
    time.sleep(2)
    
    # Demo 6: Send multiple alerts with different severities
    print("\n🚨 DEMO 6: Sending Multiple Alert Severities")
    print("-" * 50)
    
    # High severity alert
    high_alert = contract.send_alert_message(
        title="🟠 High Memory Usage Warning",
        value="Memory usage exceeded 85% threshold on production server",
        presentation_method="gauge",
        severity="high",
        category="performance",
        action_required=True,
        source_agent="system_monitor",
        metadata={
            "server": "prod-web-01",
            "memory_used": "6.8GB",
            "memory_total": "8GB",
            "usage_percent": 85
        }
    )
    
    # Medium severity alert  
    medium_alert = contract.send_alert_message(
        title="🟡 API Rate Limit Approaching",
        value="API rate limit at 75% of maximum threshold",
        presentation_method="metric",
        severity="medium",
        category="api",
        action_required=False,
        source_agent="api_gateway",
        metadata={
            "current_rate": 750,
            "limit": 1000,
            "window": "1 hour",
            "top_clients": ["client_a", "client_b", "client_c"]
        }
    )
    
    print(f"✅ High severity alert sent! Message ID: {high_alert['message_id']}")
    print(f"✅ Medium severity alert sent! Message ID: {medium_alert['message_id']}")
    print(f"💡 Check the alerts section - you should see different severity levels!")
    
    # Show current status
    print("\n📈 DEMO SUMMARY")
    print("-" * 40)
    
    try:
        recent_messages = contract.get_recent_messages(limit=10)
        total_messages = recent_messages.get('total', 0)
        
        active_alerts = contract.get_active_alerts()
        total_alerts = active_alerts.get('total', 0)
        
        print(f"📊 Total messages sent in demo: 6")
        print(f"📨 Recent messages in system: {total_messages}")
        print(f"🚨 Active alerts: {total_alerts}")
        
        print(f"\n🔗 URLs to check:")
        print(f"   • Dashboard Home: {dashboard_url}")
        print(f"   • Recent Messages: {dashboard_url}/messages/recent")
        print(f"   • Active Alerts: {dashboard_url}/messages/alerts")
        print(f"   • API Documentation: {dashboard_url}/docs")
        
    except Exception as e:
        print(f"⚠️  Could not retrieve summary: {e}")
    
    print("\n" + "🎯 DASHBOARD FEATURES TO EXPLORE" + "=" * 30)
    print("1. Real-time Metrics: Watch agent count and message count update")
    print("2. Message Types: Each message has different presentation methods")
    print("3. API Endpoints: Click links to see raw JSON data")
    print("4. Live Updates: The dashboard updates every 10 seconds")
    print("5. Alert Management: Alerts expire automatically")
    print("6. WebSocket: Real-time updates via WebSocket connection")
    
    print("\n" + "💡 NEXT STEPS" + "=" * 45)
    print("• Refresh the dashboard page to see all messages")
    print("• Try the API documentation at /docs")
    print("• Send your own messages using the service contract")
    print("• Monitor real-time updates in the browser console")
    print("• Check WebSocket connection at /ws/dashboard")
    
    print("\n🎉 Dashboard Web Demo Complete!")
    print("The dashboard is now populated with sample data and ready for integration!")

def quick_message_test():
    """Quick test to send a single message and show dashboard link."""
    
    print("🚀 Quick Message Test")
    print("=" * 30)
    
    contract = DashboardServiceContract("http://localhost:8000")
    
    # Send a simple test message
    result = contract.send_alert_message(
        title="🧪 Test Alert Message",
        value="This is a test message sent from the quick test function",
        presentation_method="text",
        severity="low",
        category="testing",
        source_agent="test_script"
    )
    
    print(f"✅ Test message sent! Message ID: {result['message_id']}")
    print(f"🌐 View dashboard: http://localhost:8000")
    print(f"📨 View message: http://localhost:8000/messages/recent")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_message_test()
    else:
        dashboard_web_demo() 