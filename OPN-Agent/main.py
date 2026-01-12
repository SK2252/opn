"""
AI Open Negotiation Automation System

Production-ready multi-agent document processing system with
Semantic Kernel integration for Open Negotiation documents.

Usage:
    # Start FastAPI server
    uvicorn main:app --reload --port 8000
    
    # Or run directly for examples
    python main.py
"""

import asyncio
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from kernel_config import create_kernel, get_config, SystemConfig
from AI_open_negotiation.plugins.document_plugin import AdvancedDocumentPlugin, DocumentSkill
from AI_open_negotiation.skills.email_skill import EmailSkill
from AI_open_negotiation.agents.document_agent.orchestrator_agent import OrchestratorAgent
from AI_open_negotiation.orchestrators.ai_orchestrator import AIDocumentOrchestrator


# Initialize FastAPI app
app = FastAPI(
    title="AI Open Negotiation Automation",
    description="Multi-agent document processing system with AI capabilities",
    version="2.0.0",
)


# Request models
class WorkflowRequest(BaseModel):
    request_id: str
    agents: list
    document_config: Optional[Dict[str, Any]] = None
    email_config: Optional[Dict[str, Any]] = None


class DocumentRequest(BaseModel):
    request_id: str
    excel_path: str
    template_docx: str
    output_folder: str = "output"
    use_ai: bool = False
    user_instructions: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

def get_output_folder_name(excel_path: str) -> str:
    """
    Extract output folder name from input Excel filename.
    Takes first two words from the filename.
    
    Example: "CEP W6 OPNNEG TEMPLATE.xlsx" -> "CEP W6"
    """
    import os
    filename = os.path.splitext(os.path.basename(excel_path))[0]
    words = filename.split()
    if len(words) >= 2:
        return f"{words[0]} {words[1]}"
    return filename


def generate_output_paths(excel_path: str, base_output_dir: str = None) -> dict:
    """
    Generate output folder paths based on input filename.
    
    Args:
        excel_path: Path to input Excel file
        base_output_dir: Base output directory (default: Data/Output relative to Excel file)
        
    Returns:
        Dictionary with output folder paths
    """
    import os
    
    # Get folder name from input filename (first two words)
    folder_name = get_output_folder_name(excel_path)
    
    # Determine base output directory
    if base_output_dir is None:
        # Use Data/Output relative to the Excel file's parent
        excel_dir = os.path.dirname(excel_path)
        # Go up from Input to Data, then into Output
        data_dir = os.path.dirname(excel_dir)
        base_output_dir = os.path.join(data_dir, "Output")
    
    # Create output paths
    base_path = os.path.join(base_output_dir, folder_name)
    
    return {
        "output_group_folder": os.path.join(base_path, f"{folder_name} OPN GROUP"),
        "output_notice_folder": os.path.join(base_path, f"{folder_name} OPN NOTICE"),
        "merged_output_folder": os.path.join(base_path, f"{folder_name} OPN GROUP & NOTICE"),
    }


# ==================== LEGACY ENDPOINT (Backward Compatible) ====================

@app.post("/run-workflow")
async def run_workflow(input_json: dict):
    """
    Legacy workflow endpoint for backward compatibility.
    
    Supports existing integrations using the original API format.
    If output folders not specified, auto-generates them based on input filename.
    """
    print(f"\n▶ Workflow STARTED | Request ID: {input_json.get('request_id', 'unknown')}")
    
    results = {}
    
    # Document creation using OrchestratorAgent
    if "document_creation" in input_json.get("agents", []):
        try:
            document_config = input_json.get("document_config", {}).copy()
            
            # Auto-generate output paths if not fully specified
            excel_path = document_config.get("excel_path", "")
            if excel_path and not document_config.get("merged_output_folder"):
                auto_paths = generate_output_paths(excel_path)
                document_config.update(auto_paths)
                print(f"📁 Auto-generated output paths based on: {get_output_folder_name(excel_path)}")
            
            orchestrator = OrchestratorAgent({"max_retries": 3})
            result = await orchestrator.process_document_request(document_config)
            results["document_creation"] = result
        except Exception as e:
            results["document_creation"] = {"status": "FAILED", "error": str(e)}
    
    # Email sending
    if "email_sending" in input_json.get("agents", []):
        try:
            kernel = create_kernel()
            kernel.add_plugin(EmailSkill(), plugin_name="email")
            email_plugin = kernel.plugins.get("email")
            if email_plugin:
                email_function = email_plugin["send_emails"]
                results["email_sending"] = email_function(
                    email_config=input_json.get("email_config", {})
                )
        except Exception as e:
            results["email_sending"] = {"status": "FAILED", "error": str(e)}
    
    print("✔ Workflow COMPLETED")
    
    return {
        "request_id": input_json.get("request_id"),
        "status": "COMPLETED",
        "results": results
    }


# ==================== NEW ADVANCED ENDPOINTS ====================

@app.post("/run-advanced-workflow")
async def run_advanced_workflow(request: DocumentRequest):
    """
    Advanced workflow endpoint using multi-agent architecture.
    
    Uses the new OrchestratorAgent for parallel processing,
    validation, and comprehensive error handling.
    """
    print(f"\n▶ Advanced Workflow STARTED | Request ID: {request.request_id}")
    
    try:
        config = get_config()
        
        document_config = {
            "excel_path": request.excel_path,
            "template_docx": request.template_docx,
            "output_group_folder": f"{request.output_folder}/groups",
            "output_notice_folder": f"{request.output_folder}/notices",
            "merged_output_folder": f"{request.output_folder}/merged",
        }
        
        if request.use_ai and config.api_key:
            # Use AI-powered orchestrator
            orchestrator = AIDocumentOrchestrator(
                api_key=config.api_key,
                config=config.to_dict()
            )
            result = await orchestrator.process_with_ai_guidance(
                excel_path=request.excel_path,
                template_docx=request.template_docx,
                output_folder=request.output_folder,
                user_instructions=request.user_instructions
            )
        else:
            # Use standard orchestrator
            orchestrator = OrchestratorAgent(config.to_dict())
            result = await orchestrator.process_document_request(document_config)
        
        print(f"✔ Advanced Workflow COMPLETED | Status: {result.get('status')}")
        
        return {
            "request_id": request.request_id,
            **result
        }
        
    except Exception as e:
        print(f"✖ Workflow FAILED: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate")
async def validate_data(request: DocumentRequest):
    """
    Validate input data before processing.
    """
    plugin = AdvancedDocumentPlugin()
    result = await plugin.validate_data(
        excel_path=request.excel_path,
        template_docx=request.template_docx
    )
    
    return {
        "request_id": request.request_id,
        "validation": result
    }


@app.post("/analyze")
async def analyze_data(request: DocumentRequest):
    """
    Analyze input data and provide insights.
    """
    plugin = AdvancedDocumentPlugin()
    result = await plugin.analyze_data(excel_path=request.excel_path)
    
    import json
    return {
        "request_id": request.request_id,
        "analysis": json.loads(result)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents": ["ValidationAgent", "GroupGenerationAgent", "NoticeGenerationAgent", "MergeAgent"]
    }


# ==================== EXAMPLE FUNCTIONS ====================

async def basic_usage_example():
    """Example: Basic document processing without AI."""
    print("\n" + "=" * 60)
    print("📄 Basic Document Processing Example")
    print("=" * 60)
    
    config = {
        "max_retries": 3,
        "enable_parallel_processing": True,
    }
    
    orchestrator = OrchestratorAgent(config)
    
    document_config = {
        "excel_path": "CEP W6 OPNNEG TEMPLATE.xlsx",
        "template_docx": "OpenNeg_CEP_Template.docx",
        "output_group_folder": "output/groups",
        "output_notice_folder": "output/notices",
        "merged_output_folder": "output/merged",
    }
    
    print("\n⏳ Processing documents...")
    result = await orchestrator.process_document_request(document_config)
    
    print(f"\n✅ Result:")
    print(f"   Status: {result.get('status')}")
    print(f"   Output: {result.get('output_folder')}")
    if result.get("stats"):
        print(f"   Stats: {result['stats'].get('successful', 0)} successful")
    
    return result


async def ai_usage_example():
    """Example: Document processing with AI guidance."""
    print("\n" + "=" * 60)
    print("🤖 AI-Powered Document Processing Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. AI features disabled.")
        print("    Set the environment variable or use basic processing.")
        return
    
    orchestrator = AIDocumentOrchestrator(api_key=api_key)
    
    print("\n⏳ Processing with AI guidance...")
    result = await orchestrator.process_with_ai_guidance(
        excel_path="CEP W6 OPNNEG TEMPLATE.xlsx",
        template_docx="OpenNeg_CEP_Template.docx",
        output_folder="output",
        user_instructions="Focus on data quality and completeness"
    )
    
    print(f"\n✅ Result:")
    print(f"   Status: {result.get('status')}")
    if result.get("analysis"):
        print(f"   Records: {result['analysis'].get('total_rows', 'N/A')}")
    if result.get("insights"):
        print(f"   AI Insights: {result['insights'][:200]}...")
    
    return result


async def interactive_example():
    """Example: Interactive mode with AI assistant."""
    print("\n" + "=" * 60)
    print("💬 Interactive AI Assistant Mode")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Interactive mode limited.")
    
    orchestrator = AIDocumentOrchestrator(api_key=api_key)
    await orchestrator.interactive_document_generation()


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("🚀 AI Open Negotiation Automation System v2.0")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "server":
            # Start the FastAPI server
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000)
        
        elif mode == "basic":
            # Run basic example
            asyncio.run(basic_usage_example())
        
        elif mode == "ai":
            # Run AI example
            asyncio.run(ai_usage_example())
        
        elif mode == "interactive":
            # Run interactive mode
            asyncio.run(interactive_example())
        
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: server, basic, ai, interactive")
    
    else:
        print("\nUsage:")
        print("  python main.py server      - Start FastAPI server")
        print("  python main.py basic       - Run basic processing example")
        print("  python main.py ai          - Run AI-powered example")
        print("  python main.py interactive - Start interactive mode")
        print("\nOr start the server with:")
        print("  uvicorn main:app --reload --port 8000")
