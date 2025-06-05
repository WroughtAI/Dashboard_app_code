from typing import Dict, Any, Optional, List, Union
import os
import requests
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class BaseRESTAdapter:
    """
    Base adapter for REST API services with retry logic and file upload handling.
    """
    
    def __init__(self, base_url: str, max_retries: int = 3, timeout: int = 30):
        """
        Initialize the REST adapter.
        
        Args:
            base_url: Base URL for the service
            max_retries: Maximum number of retries for failed requests
            timeout: Timeout in seconds for requests
        """
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
    
    def call(self, endpoint: str, data: Dict[str, Any] = None, method: str = "POST", **kwargs) -> Dict[str, Any]:
        """
        Make a REST call to the service.
        
        Args:
            endpoint: The endpoint path (e.g., '/agent-status')
            data: The data to send (for POST/PUT requests)
            method: HTTP method ('GET', 'POST', 'PUT', 'DELETE')
            **kwargs: Additional arguments for the requests call
            
        Returns:
            Dict: Response data
            
        Raises:
            Exception: If the request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, params=data, timeout=self.timeout, **kwargs)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=data, timeout=self.timeout, **kwargs)
                elif method.upper() == "PUT":
                    response = self.session.put(url, json=data, timeout=self.timeout, **kwargs)
                elif method.upper() == "DELETE":
                    response = self.session.delete(url, json=data, timeout=self.timeout, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"status": "success", "text": response.text}
                    
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    logger.error(f"Request to {url} failed after {self.max_retries + 1} attempts: {e}")
                    raise Exception(f"Request failed: {e}")
                else:
                    logger.warning(f"Request to {url} failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return {"status": "error", "error": "Max retries exceeded"}
    
    def upload_file(self, endpoint: str, file_path: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload a file to the service.
        
        Args:
            endpoint: API endpoint to call
            file_path: Path to the file to upload
            additional_data: Additional data to send with the file
            
        Returns:
            Dict: Response from the service
        """
        url = f"{self.base_url}{endpoint}"
        retry_count = 0
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_path}",
                "service": self.__class__.__name__
            }
        
        while retry_count < self.max_retries:
            try:
                files = {'file': (file_path.name, open(file_path, 'rb'))}
                data = additional_data or {}
                
                response = self.session.post(url, files=files, data=data, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self.logger.error(f"Failed to upload file to {url}: {e}")
                    return {
                        "status": "error",
                        "error": str(e),
                        "service": self.__class__.__name__
                    }
                
                # Exponential backoff
                wait_time = 2 ** retry_count
                self.logger.warning(f"Retrying upload to {url} in {wait_time} seconds...")
                time.sleep(wait_time)


class DashboardServiceContract(BaseRESTAdapter):
    """
    Service contract for the Dashboard Service.
    
    Provides methods to interact with the dashboard service including
    agent monitoring, LLM usage tracking, vector store management,
    and compliance monitoring.
    """
    
    def __init__(self, dashboard_url: str = "http://localhost:8000"):
        super().__init__(dashboard_url)
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if the dashboard service is healthy and available.
        
        Returns:
            Dict: Service health status
        """
        return self.call("/health", {}, method="GET")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get current agent status and count.
        
        Returns:
            Dict: Agent status information including active/inactive agents
        """
        return self.call("/agent-status", {}, method="GET")
    
    def get_llm_usage(self) -> Dict[str, Any]:
        """
        Get LLM usage statistics.
        
        Returns:
            Dict: LLM usage statistics including total requests, success rate, latency
        """
        return self.call("/llm-usage", {}, method="GET")
    
    def get_vector_status(self) -> Dict[str, Any]:
        """
        Get vector store status and collections information.
        
        Returns:
            Dict: Vector store status including collections count and health
        """
        return self.call("/vector-status", {}, method="GET")
    
    def get_recent_activity(self) -> Dict[str, Any]:
        """
        Get recent system activity logs.
        
        Returns:
            Dict: Recent activities across the system
        """
        return self.call("/recent-activity", {}, method="GET")
    
    def get_llm_history(self) -> Dict[str, Any]:
        """
        Get LLM interaction history.
        
        Returns:
            Dict: Historical LLM interactions and usage patterns
        """
        return self.call("/llm-history", {}, method="GET")
    
    def get_vector_collections(self) -> Dict[str, Any]:
        """
        Get detailed information about vector store collections.
        
        Returns:
            Dict: Detailed vector collections information
        """
        return self.call("/vector-collections", {}, method="GET")
    
    def search_vectors(self, query: str) -> Dict[str, Any]:
        """
        Search the vector store with a query.
        
        Args:
            query: Search query string
            
        Returns:
            Dict: Search results from vector store
        """
        data = {"query": query}
        return self.call("/vector-search", data)
    
    def get_package_status(self) -> Dict[str, Any]:
        """
        Get status of system packages and dependencies.
        
        Returns:
            Dict: Package health status information
        """
        return self.call("/package-status", {}, method="GET")
    
    def get_compliance_test_results(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get recent compliance test results.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            Dict: Recent compliance test results
        """
        data = {"limit": limit}
        return self.call("/compliance/test-results", data, method="GET")
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get overall compliance summary and status.
        
        Returns:
            Dict: Compliance summary across all domains
        """
        return self.call("/compliance/summary", {}, method="GET")
    
    def upload_dashboard_config(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload a configuration file to the dashboard service.
        
        Args:
            file_path: Path to the configuration file to upload
            options: Optional processing parameters
            
        Returns:
            Dict: Upload processing results
        """
        import json
        additional_data = {}
        if options:
            additional_data['options'] = json.dumps(options)
        
        return self.upload_file("/upload", file_path, additional_data)
    
    def get_dashboard_status(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard status including all subsystems.
        
        Returns:
            Dict: Complete dashboard status overview
        """
        try:
            # Gather status from multiple endpoints
            agent_status = self.get_agent_status()
            llm_usage = self.get_llm_usage()
            vector_status = self.get_vector_status()
            compliance_summary = self.get_compliance_summary()
            
            return {
                "status": "success",
                "service": "moa-agent-reporting-dashboard",
                "results": {
                    "agent_status": agent_status.get("results", {}),
                    "llm_usage": llm_usage.get("results", {}),
                    "vector_status": vector_status.get("results", {}),
                    "compliance_summary": compliance_summary.get("results", {}),
                    "timestamp": agent_status.get("results", {}).get("timestamp")
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive dashboard status: {e}")
            return {
                "status": "error",
                "service": "moa-agent-reporting-dashboard",
                "error": str(e)
            }

    # Agent Message Endpoints
    def send_compliance_message(self, 
                               title: str,
                               value: Union[str, int, float, Dict[str, Any], List[Any]],
                               presentation_method: str,
                               domain: Optional[str] = None,
                               status: Optional[str] = None,
                               test_id: Optional[str] = None,
                               source_agent: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a compliance message to the dashboard.
        
        Args:
            title: Display title for the message
            value: The actual data value
            presentation_method: How to display this data (chart, table, gauge, etc.)
            domain: Compliance domain (e.g., 'supply_chain', 'physical_security')
            status: Compliance status (e.g., 'compliant', 'non_compliant')
            test_id: Associated test identifier
            source_agent: Agent that sent this message
            metadata: Additional metadata
            
        Returns:
            Dict: Response with message_id and status
        """
        message_data = {
            "title": title,
            "value": value,
            "presentation_method": presentation_method,
            "domain": domain,
            "status": status,
            "test_id": test_id,
            "source_agent": source_agent,
            "metadata": metadata or {}
        }
        return self.call("/messages/compliance", message_data)

    def send_status_message(self,
                           title: str,
                           value: Union[str, int, float, Dict[str, Any], List[Any]],
                           presentation_method: str,
                           component: Optional[str] = None,
                           health_status: Optional[str] = None,
                           source_agent: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a status message to the dashboard.
        
        Args:
            title: Display title for the message
            value: The actual data value
            presentation_method: How to display this data
            component: System component name
            health_status: Health status (e.g., 'healthy', 'degraded', 'failed')
            source_agent: Agent that sent this message
            metadata: Additional metadata
            
        Returns:
            Dict: Response with message_id and status
        """
        message_data = {
            "title": title,
            "value": value,
            "presentation_method": presentation_method,
            "component": component,
            "health_status": health_status,
            "source_agent": source_agent,
            "metadata": metadata or {}
        }
        return self.call("/messages/status", message_data)

    def send_throughput_message(self,
                               title: str,
                               value: Union[str, int, float, Dict[str, Any], List[Any]],
                               presentation_method: str,
                               metric_name: Optional[str] = None,
                               unit: Optional[str] = None,
                               target_value: Optional[float] = None,
                               source_agent: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a throughput/performance message to the dashboard.
        
        Args:
            title: Display title for the message
            value: The actual data value
            presentation_method: How to display this data
            metric_name: Performance metric name
            unit: Unit of measurement
            target_value: Target or expected value
            source_agent: Agent that sent this message
            metadata: Additional metadata
            
        Returns:
            Dict: Response with message_id and status
        """
        message_data = {
            "title": title,
            "value": value,
            "presentation_method": presentation_method,
            "metric_name": metric_name,
            "unit": unit,
            "target_value": target_value,
            "source_agent": source_agent,
            "metadata": metadata or {}
        }
        return self.call("/messages/throughput", message_data)

    def send_alert_message(self,
                          title: str,
                          value: Union[str, int, float, Dict[str, Any], List[Any]],
                          presentation_method: str,
                          severity: str,
                          category: Optional[str] = None,
                          action_required: Optional[bool] = False,
                          expires_at: Optional[datetime] = None,
                          source_agent: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send an alert message to the dashboard.
        
        Args:
            title: Display title for the message
            value: The actual data value
            presentation_method: How to display this data
            severity: Alert severity level (low, medium, high, critical)
            category: Alert category
            action_required: Whether immediate action is required
            expires_at: When alert expires
            source_agent: Agent that sent this message
            metadata: Additional metadata
            
        Returns:
            Dict: Response with message_id and status
        """
        message_data = {
            "title": title,
            "value": value,
            "presentation_method": presentation_method,
            "severity": severity,
            "category": category,
            "action_required": action_required,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "source_agent": source_agent,
            "metadata": metadata or {}
        }
        return self.call("/messages/alert", message_data)

    def send_informational_message(self,
                                  title: str,
                                  value: Union[str, int, float, Dict[str, Any], List[Any]],
                                  presentation_method: str,
                                  category: Optional[str] = None,
                                  priority: Optional[str] = "normal",
                                  source_agent: Optional[str] = None,
                                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send an informational message to the dashboard.
        
        Args:
            title: Display title for the message
            value: The actual data value
            presentation_method: How to display this data
            category: Information category
            priority: Display priority
            source_agent: Agent that sent this message
            metadata: Additional metadata
            
        Returns:
            Dict: Response with message_id and status
        """
        message_data = {
            "title": title,
            "value": value,
            "presentation_method": presentation_method,
            "category": category,
            "priority": priority,
            "source_agent": source_agent,
            "metadata": metadata or {}
        }
        return self.call("/messages/informational", message_data)

    # Message Retrieval Endpoints
    def get_recent_messages(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent messages of all types."""
        return self.call("/messages/recent", {"limit": limit}, method="GET")

    def get_active_alerts(self) -> Dict[str, Any]:
        """Get currently active alerts."""
        return self.call("/messages/alerts", method="GET")

    def get_messages_by_type(self, message_type: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get messages of a specific type.
        
        Args:
            message_type: Type of messages (compliance, status, throughput, alert, informational)
            limit: Maximum number of messages to return
            
        Returns:
            Dict: Messages of the specified type
        """
        return self.call(f"/messages/{message_type}", {"limit": limit}, method="GET")

    # Convenience methods for common operations
    def report_agent_health(self, agent_name: str, health_status: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Report agent health status.
        
        Args:
            agent_name: Name of the agent
            health_status: Health status (healthy, degraded, failed)
            details: Additional health details
            
        Returns:
            Dict: Response with message_id and status
        """
        return self.send_status_message(
            title=f"{agent_name} Health Status",
            value=health_status,
            presentation_method="badge",
            component=agent_name,
            health_status=health_status,
            source_agent=agent_name,
            metadata=details or {}
        )

    def report_compliance_result(self, domain: str, test_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Report compliance test result.
        
        Args:
            domain: Compliance domain
            test_id: Test identifier
            status: Test status (passed, failed, compliant, non_compliant)
            details: Additional test details
            
        Returns:
            Dict: Response with message_id and status
        """
        return self.send_compliance_message(
            title=f"{domain} Compliance Test",
            value=status,
            presentation_method="badge",
            domain=domain,
            status=status,
            test_id=test_id,
            metadata=details or {}
        )

    def report_performance_metric(self, metric_name: str, value: float, unit: str, target: Optional[float] = None) -> Dict[str, Any]:
        """
        Report performance metric.
        
        Args:
            metric_name: Name of the performance metric
            value: Current value
            unit: Unit of measurement
            target: Target value (if applicable)
            
        Returns:
            Dict: Response with message_id and status
        """
        return self.send_throughput_message(
            title=f"{metric_name} Performance",
            value=value,
            presentation_method="gauge",
            metric_name=metric_name,
            unit=unit,
            target_value=target
        )

    def send_critical_alert(self, title: str, message: str, category: Optional[str] = None, expires_in_hours: int = 24) -> Dict[str, Any]:
        """
        Send a critical alert.
        
        Args:
            title: Alert title
            message: Alert message
            category: Alert category
            expires_in_hours: How many hours until alert expires
            
        Returns:
            Dict: Response with message_id and status
        """
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        return self.send_alert_message(
            title=title,
            value=message,
            presentation_method="text",
            severity="critical",
            category=category,
            action_required=True,
            expires_at=expires_at
        ) 