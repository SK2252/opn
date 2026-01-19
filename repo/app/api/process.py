"""
Unified process endpoint for routing + execution.
"""

from fastapi import APIRouter
from app.api.chat import chat
from app.services.orchestration_service import process_query
from app.schemas import ProcessRequest, ProcessResponse
from app.logger import logger

router = APIRouter(tags=["Process"])

@router.post(
    "/process",
    response_model=ProcessResponse,
    summary="Unified routing and execution",
    description="Single endpoint that handles intent routing and immediately executes the target agent"
)
async def process(request: ProcessRequest):
    """
    Unified Endpoint: Routing + Execution
    
    1. Calls Repo routing engine (same as /chat)
    2. If routing is successful, automatically executes the target agent
    3. Returns combined result
    
    **Args:**
    - `request`: ProcessRequest with query and context
    
    **Returns:**
    - `ProcessResponse`: Combined routing and execution results
    """
    logger.info(f"[PROCESS] Starting unified processing for query: {request.query}")
    
    # Step 1: Get routing decision (reuse existing chat logic)
    # Note: chat() is synchronous, so we call it directly
    routing_result = chat(query=request.query, session_id=request.session_id)
    
    # Check if we got a Pydantic model response (FastAPI might return dict or model)
    # The chat function implementation returns a dict, but let's be safe.
    if hasattr(routing_result, "dict"):
        routing_result = routing_result.dict()
    
    logger.info(f"[PROCESS] Routing result type: {routing_result.get('type')}")
    
    # Inject default base_path for file resolution if not provided
    context = request.context or {}
    if "base_path" not in context:
        # Default to OPN-Agent's input folder (relative to repo/app/api)
        import os
        context["base_path"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../OPN-Agent/AI_open_negotiation/Data/Input")
        )
        logger.info(f"[PROCESS] Using default base_path: {context['base_path']}")
    
    # Step 2: Orchestrate execution based on routing
    result = await process_query(
        query=request.query,
        routing_result=routing_result,
        session_id=request.session_id,
        context=context
    )
    
    logger.info(f"[PROCESS] Completed with status: {result['status']}")
    
    return result
