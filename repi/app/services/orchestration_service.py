"""
Orchestration service - handles unified routing + execution.
Migrated from standalone orchestrator service into Repi.
"""

import json
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

from app.db.database import SessionLocal
from app.models.agent import Agent
from app.services.file_resolver import FileResolver
from app.logger import logger


async def process_query(
    query: str,
    routing_result: Dict[str, Any],
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main orchestration function - routes and executes agent.
    
    Args:
        query: User query string
        routing_result: Result from chat service routing
        session_id: Optional session ID
        context: Optional context (e.g., file paths)
    
    Returns:
        Complete result with routing + execution data
    """
    result = {
        "status": "PENDING",
        "routing_decision": routing_result,
        "file_resolution": None,
        "execution_result": None,
        "message": None,
        "errors": []
    }
    
    try:
        response_type = routing_result.get("type")
        
        # Pass through non-routing responses (clarification, confirmation, etc.)
        if response_type in ["clarification", "confirmation", "agent_inquiry", "invalid_query"]:
            result["status"] = "AWAITING_USER_INPUT"
            result["message"] = routing_result.get("response", "")
            return result
        
        # Extract routing information
        if response_type != "routing":
            result["status"] = "FAILED"
            result["errors"].append(f"Unexpected response type: {response_type}")
            return result
        
        # Parse routing JSON
        routing_data = json.loads(routing_result.get("routing", "{}"))
        agent_name = routing_data.get("agent")
        
        if not agent_name:
            result["status"] = "FAILED"
            result["errors"].append("No agent specified in routing")
            return result
        
        # Extract parameters
        params = {
            "client_name": routing_data.get("client_name", ""),
            "wave_number": routing_data.get("wave_number", ""),
            "agent_name": agent_name,
            "subagent_name": routing_data.get("subagent") or ""
        }
        
        # Find agent in database
        agent = _get_agent_by_name(agent_name)
        
        if not agent:
            result["status"] = "FAILED"
            result["errors"].append(f"Agent not found in database: {agent_name}")
            return result
        
        # Check if agent has endpoint configured
        if not agent.endpoint:
            result["status"] = "FAILED"
            result["errors"].append(f"Agent '{agent_name}' does not have an endpoint configured. Cannot execute.")
            return result
        
        # Resolve files if payload_mapping includes file paths
        resolved_files = {}
        if agent.payload_mapping:
            base_path = context.get("base_path") if context else None
            if base_path:
                resolved_files = _resolve_files(agent, params, base_path)
                result["file_resolution"] = resolved_files
        
        # Build agent payload
        payload = _build_payload(agent, params, resolved_files)
        
        # Call agent endpoint
        execution_result = await _call_agent(agent, payload)
        result["execution_result"] = execution_result
        result["status"] = "SUCCESS"
        
        return result
    
    except Exception as e:
        logger.exception(f"Orchestration error: {str(e)}")
        result["status"] = "FAILED"
        result["errors"].append(f"Unexpected error: {str(e)}")
        return result


def _get_agent_by_name(agent_name: str) -> Optional[Agent]:
    """Fetch agent from database by name."""
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        return agent
    finally:
        db.close()


def _resolve_files(
    agent: Agent, 
    params: Dict[str, str], 
    base_path: str
) -> Dict[str, Optional[str]]:
    """
    Resolve file paths using FileResolver.
    
    Args:
        agent: Agent model with payload_mapping
        params: Extracted parameters (client_name, wave_number)
        base_path: Base directory to search
    
    Returns:
        Dictionary of resolved file paths
    """
    try:
        # Check if payload_mapping contains file patterns
        if not agent.payload_mapping:
            return {}
        
        # Extract file patterns from payload mappingpatterns = {}
        for key, value in agent.payload_mapping.items():
            if isinstance(value, str) and "resolved_" in value:
                # This is a file reference like "resolved_excel_path"
                file_type = value.replace("resolved_", "").replace("_path", "")
                # You would need to have patterns defined somewhere
                # For now, use default patterns
                if file_type == "excel":
                    patterns["excel"] = "{client_name} W{wave_number}*.xlsx"
                elif file_type == "template":
                    patterns["template"] = "*Template*.docx"
        
        if not patterns:
            return {}
        
        resolver = FileResolver(base_path)
        resolved = resolver.resolve_files(
            client_name=params.get("client_name", ""),
            wave_number=params.get("wave_number", ""),
            patterns=patterns
        )
        
        return resolved
    
    except Exception as e:
        logger.warning(f"File resolution failed: {str(e)}")
        return {}


def _build_payload(
    agent: Agent, 
    params: Dict[str, str], 
    resolved_files: Dict[str, Optional[str]]
) -> Dict[str, Any]:
    """
    Build API payload for agent execution.
    
    Args:
        agent: Agent model with payload_mapping
        params: Routing parameters
        resolved_files: Resolved file paths
    
    Returns:
        Payload dictionary for agent API call
    """
    if not agent.payload_mapping:
        return params
    
    payload = {}
    
    for key, value in agent.payload_mapping.items():
        # Handle non-string values directly
        if not isinstance(value, str):
            payload[key] = value
            continue
        
        # Handle file path mappings (resolved_excel_path -> actual path)
        if value.startswith("resolved_"):
            file_type = value.replace("resolved_", "").replace("_path", "")
            payload[key] = resolved_files.get(file_type)
        
        # Handle string templates with parameter substitution
        elif "{" in value:
            try:
                payload[key] = value.format(**params)
            except KeyError as e:
                logger.warning(f"Missing parameter for template '{value}': {str(e)}")
                payload[key] = value
        
        # Handle static string values
        else:
            payload[key] = value
    
    return payload


async def _call_agent(agent: Agent, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute agent API endpoint.
    
    Args:
        agent: Agent model with endpoint and timeout
        payload: Prepared payload for API call
    
    Returns:
        Agent execution result
    """
    timeout = agent.timeout or 300
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                agent.endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
    
    except httpx.HTTPError as e:
        logger.error(f"Agent API call failed: {str(e)}")
        return {
            "status": "FAILED",
            "errors": [f"HTTP error: {str(e)}"]
        }
    
    except Exception as e:
        logger.error(f"Agent execution error: {str(e)}")
        return {
            "status": "FAILED",
            "errors": [f"Unexpected error: {str(e)}"]
        }
