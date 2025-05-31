#!/usr/bin/env python3
"""
Simple Dashboard Web Demo
Sends sample messages and shows how to view them on the web dashboard.
"""

import time
import requests
import json
from datetime import datetime

def send_message(endpoint, data):
    """Send a message to the dashboard API."""
    url = f"http://localhost:8000{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"✅ Message sent to {endpoint}: {result.get('message_id', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Failed to send message to {endpoint}: {e}")
        return False

def demo_dashboard():
    """Demonstrate the dashboard with sample messages."""
    
    print("🌐 Dashboard Web Interface Demo")
    print("=" * 50)
    
    # Check if dashboard is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        health_response.raise_for_status()
        print("✅ Dashboard service is running!")
    except Exception as e:
        print(f"❌ Dashboard service is not available: {e}")
        print("Please start the dashboard service first:")
        print("cd dashboard_service && uvicorn app:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    print("\n📨 Sending sample messages to populate the dashboard...")
    
    # Send compliance message
    compliance_msg = {
        "title": "🛡️ Security Compliance Check",
        "value": "compliant",
        "presentation_method": "badge",
        "domain": "security",
        "status": "compliant",
        "test_id": "sec_audit_001",
        "source_agent": "compliance_bot"
    }
    send_message("/messages/compliance", compliance_msg)
    time.sleep(1)
    
    # Send status message
    status_msg = {
        "title": "💚 Database Health",
        "value": "healthy",
        "presentation_method": "badge",
        "component": "postgresql",
        "health_status": "healthy",
        "source_agent": "health_checker"
    }
    send_message("/messages/status", status_msg)
    time.sleep(1)
    
    # Send throughput message
    throughput_msg = {
        "title": "⚡ API Response Time",
        "value": 125.5,
        "presentation_method": "gauge",
        "metric_name": "avg_response_time",
        "unit": "ms",
        "target_value": 100.0,
        "source_agent": "performance_monitor"
    }
    send_message("/messages/throughput", throughput_msg)
    time.sleep(1)
    
    # Send informational message
    info_msg = {
        "title": "📦 Daily Backup Completed",
        "value": "Backup finished successfully with 2.1GB archived",
        "presentation_method": "text",
        "category": "maintenance",
        "priority": "normal",
        "source_agent": "backup_service"
    }
    send_message("/messages/informational", info_msg)
    time.sleep(1)
    
    # Send degraded status message
    degraded_msg = {
        "title": "⚠️ High Memory Usage",
        "value": "degraded",
        "presentation_method": "gauge",
        "component": "web_server",
        "health_status": "degraded",
        "source_agent": "system_monitor"
    }
    send_message("/messages/status", degraded_msg)
    time.sleep(1)
    
    print("\n🎉 Demo messages sent successfully!")
    
    # Show dashboard information
    print("\n" + "🌐 DASHBOARD WEB INTERFACE" + "=" * 30)
    print("📍 URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📨 Recent Messages: http://localhost:8000/messages/recent")
    
    print("\n" + "💡 WHAT TO DO NEXT" + "=" * 35)
    print("1. 🌐 Open http://localhost:8000 in your web browser")
    print("2. 👀 Watch the 'Recent Messages' section at the bottom")
    print("3. 🔄 Click 'Refresh Messages' to see the latest updates")
    print("4. 📊 Notice how the 'Recent Messages' count has increased")
    print("5. 🎯 Observe different message types with color coding:")
    print("   • 📋 COMPLIANCE (green) - Compliance test results")
    print("   • 💚 STATUS (blue) - System health information") 
    print("   • ⚡ THROUGHPUT (orange) - Performance metrics")
    print("   • 📝 INFORMATIONAL (purple) - General updates")
    
    print("\n" + "🚀 LIVE DEMO FEATURES" + "=" * 32)
    print("• 🔄 Auto-refresh every 5 seconds")
    print("• 📱 Responsive design works on mobile")
    print("• 🎨 Color-coded message types")
    print("• ⏰ Real-time timestamps")
    print("• 🏷️ Agent source attribution")
    print("• 🎭 Presentation method indicators")
    
    print("\n" + "🧪 TRY SENDING YOUR OWN MESSAGES" + "=" * 20)
    print("Use curl to send custom messages:")
    print("""
curl -X POST http://localhost:8000/messages/compliance \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "🧪 My Test Message",
    "value": "This is a custom test message",
    "presentation_method": "text",
    "domain": "testing",
    "status": "passed",
    "source_agent": "my_agent"
  }'
    """)
    
    print("🎊 Dashboard is now ready for agent integration!")

if __name__ == "__main__":
    demo_dashboard() 