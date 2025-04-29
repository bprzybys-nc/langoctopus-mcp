import json
import os
import requests
from typing import Any, Dict, List

class LambdaMcpAdapter:
    """
    Adapter class for interacting with MCP services deployed as AWS Lambda functions
    behind API Gateway.
    """
    
    def __init__(self, base_url: str = None):
        """
        Initialize the adapter with the base URL for the API Gateway.
        
        Args:
            base_url: Base URL of the API Gateway. If not provided, will use environment 
                     variable API_GATEWAY_URL or default to localhost.
        """
        self.base_url = base_url or os.environ.get('API_GATEWAY_URL', 'http://localhost:3000')
        
        # Remove trailing slash if present
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
    
    def get_math_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available math tools.
        
        Returns:
            List of tool descriptions compatible with langchain tools format.
        """
        return [
            {
                "name": "add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "subtract",
                "description": "Subtract b from a",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "divide",
                "description": "Divide a by b",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "Numerator"},
                        "b": {"type": "integer", "description": "Denominator (cannot be zero)"}
                    },
                    "required": ["a", "b"]
                }
            }
        ]
    
    def get_weather_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available weather tools.
        
        Returns:
            List of tool descriptions compatible with langchain tools format.
        """
        return [
            {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or location name"}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast for a location for the next few days",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or location name"},
                        "days": {"type": "integer", "description": "Number of days for forecast"}
                    },
                    "required": ["location"]
                }
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available tools from both math and weather services.
        
        Returns:
            Combined list of all tools.
        """
        return self.get_math_tools() + self.get_weather_tools()
    
    def invoke_math(self, operation: str, parameters: Dict[str, Any]) -> str:
        """
        Invoke a math operation.
        
        Args:
            operation: The operation name (add, multiply, subtract, divide)
            parameters: The parameters for the operation
            
        Returns:
            The result of the operation
            
        Raises:
            Exception: If the API call fails
        """
        url = f"{self.base_url}/math"
        payload = {
            "operation": operation,
            "parameters": parameters
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', 'Unknown error')
            raise Exception(f"Math API error: {error_msg}")
        
        return response.json().get('result')
    
    def invoke_weather(self, operation: str, parameters: Dict[str, Any]) -> str:
        """
        Invoke a weather operation.
        
        Args:
            operation: The operation name (get_weather, get_forecast)
            parameters: The parameters for the operation
            
        Returns:
            The result of the operation
            
        Raises:
            Exception: If the API call fails
        """
        url = f"{self.base_url}/weather"
        payload = {
            "operation": operation,
            "parameters": parameters
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', 'Unknown error')
            raise Exception(f"Weather API error: {error_msg}")
        
        return response.json().get('result')
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """
        Execute a tool by name.
        
        Args:
            tool_name: The name of the tool to execute
            **kwargs: The parameters for the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If the tool is not found
        """
        if tool_name in ['add', 'multiply', 'subtract', 'divide']:
            return self.invoke_math(tool_name, kwargs)
        elif tool_name in ['get_weather', 'get_forecast']:
            return self.invoke_weather(tool_name, kwargs)
        else:
            raise ValueError(f"Unknown tool: {tool_name}") 