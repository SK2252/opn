"""
FastAPI application for orchestrator service.
Provides single endpoint that coordinates routing and execution.
Provides single endpoint that coordinates routing and execution.
# Reload trigger v2
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from orchestrator import Orchestrator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Orchestrator Service",
    description="Middleware service that coordinates between Repi (routing) and OPN-Agent (execution)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = Orchestrator(
    repi_url=os.getenv("REPI_URL", "http://localhost:8001"),
    registry_path="agent_registry.json",
    repi_timeout=int(os.getenv("REPI_TIMEOUT", "30"))
)


class ProcessRequest(BaseModel):
    """Request model for /process endpoint."""
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    repi_url: str
    registry_loaded: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns service status and configuration info.
    """
    return {
        "status": "healthy",
        "service": "orchestrator",
        "repi_url": os.getenv("REPI_URL", "http://localhost:8001"),
        "registry_loaded": orchestrator.registry is not None
    }


@app.post("/process")
async def process_query(request: ProcessRequest):
    """
    Main processing endpoint.
    
    Coordinates routing (via Repi) and execution (via OPN-Agent).
    
    Args:
        request: ProcessRequest with query, optional session_id and context
    
    Returns:
        Combined result containing:
        - routing_decision: Agent and parameter extraction
        - file_resolution: Auto-discovered file paths
        - execution_result: Output from agent execution
    
    Examples:
        >>> POST /process
        >>> {
        >>>   "query": "Create document for CEP Wave 6"
        >>> }
        
        Response:
        {
          "status": "SUCCESS",
          "routing_decision": {...},
          "file_resolution": {...},
          "execution_result": {...}
        }
    """
    try:
        result = await orchestrator.process(
            query=request.query,
            session_id=request.session_id,
            context=request.context
        )
        
        # If awaiting user input (clarification/confirmation), return immediately
        if result["status"] == "AWAITING_USER_INPUT":
            return result
        
        # If failed, raise HTTP exception
        if result["status"] == "FAILED":
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Processing failed",
                    "errors": result.get("errors", [])
                }
            )
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "error": str(e)
            }
        )


@app.get("/registry")
async def get_registry():
    """
    Get current agent registry configuration.
    Useful for debugging and validation.
    """
    return orchestrator.registry


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("ORCHESTRATOR_PORT", "8002"))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
