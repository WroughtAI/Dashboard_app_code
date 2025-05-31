"""
Sample Service Contract for User Management Domain
Demonstrates how to integrate Python REST functions with the agent scaffold.
"""
from .base_rest_adapter import BaseRESTAdapter
from agent_shell.config import settings
from typing import Dict, List, Any

class UserServiceContract(BaseRESTAdapter):
    """
    Service contract for user management REST endpoints.
    
    To add a new function:
    1. Developer implements the REST endpoint in their Python app
    2. Integrator adds a method here that calls self.call()
    """
    
    def __init__(self):
        super().__init__(settings.USER_SERVICE_URL)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Dict: Created user data with ID
        """
        return self.call("/create_user", user_data)

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Dict: User data
        """
        return self.call("/get_user", {"user_id": user_id}, method="GET")

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            user_id: The user identifier
            updates: Dictionary of fields to update
            
        Returns:
            Dict: Updated user data
        """
        payload = {"user_id": user_id, "updates": updates}
        return self.call("/update_user", payload)

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Dict: Deletion confirmation
        """
        return self.call("/delete_user", {"user_id": user_id})

    def list_users(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        List users with optional filters.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            List: List of user data
        """
        payload = filters or {}
        return self.call("/list_users", payload, method="GET")

    def validate_user_permissions(self, user_id: str, resource: str, action: str) -> Dict[str, Any]:
        """
        Validate user permissions for a resource/action.
        
        Args:
            user_id: The user identifier
            resource: The resource being accessed
            action: The action being performed
            
        Returns:
            Dict: Permission validation result
        """
        payload = {
            "user_id": user_id,
            "resource": resource,
            "action": action
        }
        return self.call("/validate_permissions", payload) 