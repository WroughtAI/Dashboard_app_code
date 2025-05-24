from typing import Dict, Any, Optional, List
import os
import requests
import logging
import time
from pathlib import Path

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
    
    def call(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """
        Make a REST API call with retry logic.
        
        Args:
            endpoint: API endpoint to call
            data: Data to send
            method: HTTP method to use
            
        Returns:
            Dict: Response from the service
        """
        url = f"{self.base_url}{endpoint}"
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                if method.upper() == "GET":
                    response = requests.get(url, params=data, timeout=self.timeout)
                else:
                    response = requests.post(url, json=data, timeout=self.timeout)
                
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self.logger.error(f"Failed to call {url}: {e}")
                    return {
                        "status": "error",
                        "error": str(e),
                        "service": self.__class__.__name__
                    }
                
                # Exponential backoff
                wait_time = 2 ** retry_count
                self.logger.warning(f"Retrying {url} in {wait_time} seconds...")
                time.sleep(wait_time)
    
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
                
                response = requests.post(url, files=files, data=data, timeout=self.timeout)
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


class YourServiceContract(BaseRESTAdapter):
    """
    Service contract for your service.
    
    Replace this with a description of your service's capabilities.
    """
    
    def __init__(self):
        # Get URL from environment or use default
        url = os.getenv("YOUR_SERVICE_URL", "http://your-service:8000")
        super().__init__(url)
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if your service is healthy and available.
        
        Returns:
            Dict: Service health status
        """
        return self.call("/health", {}, method="GET")
    
    def your_method(self, param1: str, param2: int) -> Dict[str, Any]:
        """
        Example method for your service.
        
        Args:
            param1: Description of param1
            param2: Description of param2
            
        Returns:
            Dict: Results from the service
        """
        data = {
            "param1": param1,
            "param2": param2
        }
        return self.call("/your-endpoint", data)
    
    def process_file(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a file with your service.
        
        Args:
            file_path: Path to the file to process
            options: Optional processing parameters
            
        Returns:
            Dict: Processing results
        """
        additional_data = options or {}
        return self.upload_file("/upload", file_path, additional_data) 