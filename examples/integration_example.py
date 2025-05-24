from typing import Dict, Any, Optional, List
import os
import requests
import logging
import time
import json
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


class DataProcessorContract(BaseRESTAdapter):
    """
    Service contract for the example data processor service.
    """
    
    def __init__(self):
        # Get URL from environment or use default
        url = os.getenv("DATA_PROCESSOR_URL", "http://localhost:8000")
        super().__init__(url)
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if the data processor service is healthy and available.
        
        Returns:
            Dict: Service health status
        """
        return self.call("/health", {}, method="GET")
    
    def get_statistics(self, columns: List[str]) -> Dict[str, Any]:
        """
        Get statistics for specified columns in the dataset.
        
        Args:
            columns: List of column names to analyze
            
        Returns:
            Dict: Column statistics
        """
        data = {"columns": columns}
        return self.call("/get-stats", data)
    
    def process_file(self, file_path: str, calculate_stats: bool = True) -> Dict[str, Any]:
        """
        Process a data file.
        
        Args:
            file_path: Path to the CSV or Excel file
            calculate_stats: Whether to calculate statistics for numeric columns
            
        Returns:
            Dict: Processing results with data summary
        """
        options = json.dumps({"calculate_stats": calculate_stats})
        additional_data = {"options": options}
        return self.upload_file("/upload", file_path, additional_data)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Initialize the service contract
    data_processor = DataProcessorContract()
    
    # Check service health
    health = data_processor.health_check()
    print(f"Service health: {health}")
    
    # Example: Get statistics for specific columns
    stats = data_processor.get_statistics(["column1", "column2"])
    print(f"Column statistics: {stats}")
    
    # Example: Process a data file
    # First create a sample CSV file
    with open("sample_data.csv", "w") as f:
        f.write("column1,column2,column3\n")
        f.write("1,2,3\n")
        f.write("4,5,6\n")
        f.write("7,8,9\n")
    
    # Process the file
    results = data_processor.process_file("sample_data.csv")
    print(f"File processing results: {results}")
    
    # Clean up the sample file
    os.unlink("sample_data.csv") 