"""
Core orchestrator logic.
Coordinates between Repi (routing) and OPN-Agent (execution).
"""

import json
import httpx
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
from file_resolver import FileResolver


class Orchestrator:
    """
    Main orchestrator class.
    Handles routing, file resolution, and agent execution.
    """
    
    def __init__(
        self, 
        repi_url: str, 
        registry_path: str,
        repi_timeout: int = 30
    ):
        """
        Initialize orchestrator.
        
        Args:
            repi_url: URL of Repi routing service
            registry_path: Path to agent registry JSON
            repi_timeout: Timeout for Repi calls in seconds
        """
        self.repi_url = repi_url
        self.repi_timeout = repi_timeout
        self.registry = self._load_registry(registry_path)
        
        # Initialize file resolver if base path exists
        base_path = self.registry.get("agents", [{}])[0].get(
            "file_resolution", {}
        ).get("base_path")
        
        if base_path:
            self.file_resolver = FileResolver(base_path)
        else:
            self.file_resolver = None
    
    def _load_registry(self, registry_path: str) -> Dict:
        """Load agent registry from JSON file."""
        with open(registry_path, 'r') as f:
            return json.load(f)
    
    def _convert_to_serializable(self, obj):
        """
        Convert numpy/pandas types to Python native types for JSON serialization.
        
        Args:
            obj: Any object that might contain numpy/pandas types
        
        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, dict):
            return {key: self._convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def _find_agent_config(
        self, 
        agent_name: str, 
        subagent_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find agent configuration in registry.
        
        Args:
            agent_name: Name of the agent
            subagent_name: Optional subagent name
        
        Returns:
            Agent configuration dict or None
        """
        for agent in self.registry.get("agents", []):
            if agent["agent_name"] == agent_name:
                # If subagent specified, check if it matches
                if subagent_name and agent.get("subagent_name") != subagent_name:
                    continue
                return agent
        return None
    
    async def call_repi(
        self, 
        query: str, 
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Call Repi routing service.
        
        Args:
            query: User query string
            session_id: Optional session ID for conversation continuity
        
        Returns:
            Routing response from Repi
        
        Raises:
            httpx.HTTPError: If Repi call fails
        """
        async with httpx.AsyncClient() as client:
            payload = {"query": query}
            if session_id:
                payload["session_id"] = session_id
            
            response = await client.post(
                f"{self.repi_url}/chat/chat",
                params=payload,
                timeout=self.repi_timeout
            )
            response.raise_for_status()
            return response.json()
    
    def _resolve_file_paths(
        self, 
        agent_config: Dict, 
        params: Dict
    ) -> Dict[str, Optional[str]]:
        """
        Resolve file paths based on agent configuration and parameters.
        
        Args:
            agent_config: Agent configuration from registry
            params: Extracted parameters (client_name, wave_number, etc.)
        
        Returns:
            Dictionary mapping file types to resolved paths
        """
        if not self.file_resolver:
            return {}
        
        file_config = agent_config.get("file_resolution", {})
        
        if not file_config.get("enabled", False):
            return {}
        
        patterns = file_config.get("patterns", {})
        client_name = params.get("client_name", "")
        wave_number = params.get("wave_number", "")
        
        return self.file_resolver.resolve_files(
            client_name=client_name,
            wave_number=wave_number,
            patterns=patterns
        )
    
    def _build_agent_payload(
        self, 
        agent_config: Dict, 
        resolved_files: Dict, 
        params: Dict
    ) -> Dict:
        """
        Build payload for agent execution.
        
        Args:
            agent_config: Agent configuration
            resolved_files: Resolved file paths
            params: Extracted parameters
        
        Returns:
            Payload dictionary for agent API call
        """
        payload_mapping = agent_config.get("payload_mapping", {})
        payload = {}
        
        for key, value in payload_mapping.items():
            # Handle non-string values directly (booleans, integers, etc.)
            if not isinstance(value, str):
                payload[key] = value
                continue
            
            # Handle file path mappings
            if value.startswith("resolved_"):
                file_type = value.replace("resolved_", "").replace("_path", "")
                payload[key] = resolved_files.get(file_type)
            
            # Handle string templates with parameter substitution
            elif "{" in value:
                payload[key] = value.format(**params)
            
            # Handle static string values
            else:
                payload[key] = value
        
        return payload
    
    async def call_agent(
        self, 
        agent_config: Dict, 
        payload: Dict
    ) -> Dict:
        """
        Execute agent endpoint.
        
        Args:
            agent_config: Agent configuration
            payload: Prepared payload
        
        Returns:
            Agent execution result
        
        Raises:
            httpx.HTTPError: If agent call fails
        """
        endpoint = agent_config["endpoint"]
        timeout = agent_config.get("timeout", 300)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Get JSON response and convert numpy/pandas types
            result = response.json()
            result = self._convert_to_serializable(result)
            return result
    
    async def process(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main processing pipeline.
        
        Workflow:
        1. Call Repi for routing
        2. Handle clarification/confirmation if needed
        3. Resolve file paths
        4. Call agent endpoint
        5. Return combined result
        
        Args:
            query: User query
            session_id: Optional session ID
            context: Optional additional context
        
        Returns:
            Complete processing result with routing and execution data
        """
        result = {
            "status": "PENDING",
            "routing_decision": None,
            "file_resolution": None,
            "execution_result": None,
            "errors": []
        }
        
        try:
            # Step 1: Get routing from Repi
            routing_response = await self.call_repi(query, session_id)
            result["routing_decision"] = routing_response
            
            response_type = routing_response.get("type")
            
            # Step 2: Handle non-routing responses (pass through to user)
            if response_type in ["clarification", "confirmation", "agent_inquiry", "invalid_query"]:
                result["status"] = "AWAITING_USER_INPUT"
                result["message"] = routing_response.get("response", "")
                return result
            
            # Step 3: Extract routing information
            if response_type != "routing":
                result["status"] = "FAILED"
                result["errors"].append(f"Unexpected response type: {response_type}")
                return result
            
            routing_data = json.loads(routing_response.get("routing", "{}"))
            agent_name = routing_data.get("agent")
            subagent_name = routing_data.get("subagent")
            
            # Extract parameters
            params = {
                "client_name": routing_data.get("client_name", ""),
                "wave_number": routing_data.get("wave_number", ""),
                "agent_name": agent_name,
                "subagent_name": subagent_name or ""
            }
            
            # Step 4: Find agent configuration
            agent_config = self._find_agent_config(agent_name, subagent_name)
            
            if not agent_config:
                result["status"] = "FAILED"
                result["errors"].append(f"No configuration found for agent: {agent_name}")
                return result
            
            # Step 5: Resolve file paths
            resolved_files = self._resolve_file_paths(agent_config, params)
            result["file_resolution"] = resolved_files
            
            # Validate required files
            file_config = agent_config.get("file_resolution", {})
            if file_config.get("enabled"):
                required_params = file_config.get("required_params", [])
                
                # Check if required parameters are present
                missing_params = [p for p in required_params if not params.get(p)]
                if missing_params:
                    result["status"] = "FAILED"
                    result["errors"].append(
                        f"Missing required parameters: {', '.join(missing_params)}"
                    )
                    return result
                
                # Validate file resolution
                patterns = file_config.get("patterns", {})
                is_valid, missing = self.file_resolver.validate_resolved_files(
                    resolved_files, 
                    list(patterns.keys())
                )
                
                if not is_valid:
                    result["status"] = "FAILED"
                    result["errors"].append(
                        f"Could not resolve required files: {', '.join(missing)}"
                    )
                    result["file_resolution"]["missing"] = missing
                    return result
            
            # Step 6: Build agent payload
            payload = self._build_agent_payload(agent_config, resolved_files, params)
            
            # Step 7: Call agent
            execution_result = await self.call_agent(agent_config, payload)
            result["execution_result"] = execution_result
            result["status"] = "SUCCESS"
            
            return result
        
        except httpx.HTTPError as e:
            result["status"] = "FAILED"
            result["errors"].append(f"HTTP error: {str(e)}")
            return result
        
        except Exception as e:
            result["status"] = "FAILED"
            result["errors"].append(f"Unexpected error: {str(e)}")
            return result
