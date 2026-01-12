"""
AI Document Orchestrator for Semantic Kernel.

Provides AI-powered document processing with natural language
analysis, intelligent error recovery, and interactive mode.
"""

import json
import os
from typing import Any, Dict, List, Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory

from AI_open_negotiation.plugins.document_plugin import AdvancedDocumentPlugin
from AI_open_negotiation.agents.document_agent.orchestrator_agent import OrchestratorAgent


class AIDocumentOrchestrator:
    """
    AI-powered orchestrator for document processing.
    
    Combines Semantic Kernel AI capabilities with the multi-agent
    document processing system for intelligent workflow control.
    
    Features:
    - Natural language analysis of requirements
    - AI-guided validation and error handling
    - Interactive conversation mode
    - Intelligent insights and recommendations
    
    Example:
        >>> orchestrator = AIDocumentOrchestrator(api_key="sk-...")
        >>> result = await orchestrator.process_with_ai_guidance(
        ...     excel_path="data.xlsx",
        ...     template_docx="template.docx",
        ...     output_folder="output"
        ... )
    """
    
    SYSTEM_PROMPT = """You are an AI assistant specialized in document processing for the Open Negotiation system.

Your capabilities:
1. Analyze Excel data for claim processing
2. Validate data quality and completeness
3. Generate Open Negotiation Group Excel files
4. Generate Open Negotiation Notice Word/PDF documents
5. Provide insights and recommendations

When helping users:
- Always validate data before processing
- Explain any errors or warnings clearly
- Provide actionable recommendations
- Track processing progress and statistics

Available functions:
- create_documents: Generate all documents from Excel data
- validate_data: Check data quality before processing
- analyze_data: Get insights about the data
- get_processing_status: Check last processing result"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "gpt-4o-mini",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the AI orchestrator.
        
        Args:
            api_key: OpenAI API key (or from environment)
            model_id: AI model to use
            config: Configuration for agents
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_id = model_id
        self.config = config or {}
        
        # Initialize kernel and plugin
        self.kernel = self._create_kernel()
        self.plugin = AdvancedDocumentPlugin(self.kernel, self.config)
        self.kernel.add_plugin(self.plugin, "DocumentPlugin")
        
        # Initialize chat history
        self.chat_history = ChatHistory(system_message=self.SYSTEM_PROMPT)
    
    def _create_kernel(self) -> Kernel:
        """Create and configure Semantic Kernel."""
        kernel = Kernel()
        
        if self.api_key:
            chat_service = OpenAIChatCompletion(
                service_id="chat",
                ai_model_id=self.model_id,
                api_key=self.api_key,
            )
            kernel.add_service(chat_service)
        
        return kernel
    
    async def process_with_ai_guidance(
        self,
        excel_path: str,
        template_docx: str,
        output_folder: str,
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process documents with AI analysis and guidance.
        
        Workflow:
        1. AI analyzes the input data
        2. AI validates data quality
        3. AI guides document generation
        4. AI provides insights on results
        
        Args:
            excel_path: Path to input Excel file
            template_docx: Path to Word template
            output_folder: Base output folder
            user_instructions: Optional additional instructions
            
        Returns:
            Dictionary with processing result and AI insights
        """
        result = {
            "status": "PENDING",
            "analysis": None,
            "validation": None,
            "processing": None,
            "insights": None,
            "errors": [],
        }
        
        try:
            # Step 1: Analyze data
            print("[AI] Analyzing input data...")
            analysis_result = await self.plugin.analyze_data(excel_path)
            result["analysis"] = json.loads(analysis_result)
            
            if "error" in result["analysis"]:
                result["status"] = "FAILED"
                result["errors"].append(result["analysis"]["error"])
                return result
            
            # Step 2: Validate data
            print("[AI] Validating data quality...")
            validation_result = await self.plugin.validate_data(excel_path, template_docx)
            result["validation"] = json.loads(validation_result)
            
            if not result["validation"].get("is_valid", False):
                result["status"] = "VALIDATION_FAILED"
                result["errors"].extend(result["validation"].get("errors", []))
                
                # Get AI recommendations for fixing issues
                if self.api_key:
                    insights = await self._get_ai_insights(
                        f"Validation failed with errors: {result['validation']['errors']}. "
                        f"What should the user do to fix these issues?"
                    )
                    result["insights"] = insights
                
                return result
            
            # Step 3: Process documents
            print("[AI] Generating documents...")
            if user_instructions:
                print(f"[AI] User instructions: {user_instructions}")
            
            processing_result = await self.plugin.create_documents(
                excel_path=excel_path,
                template_docx=template_docx,
                output_folder=output_folder,
            )
            result["processing"] = json.loads(processing_result)
            result["status"] = result["processing"].get("status", "UNKNOWN")
            
            # Step 4: Get AI insights
            if self.api_key and result["status"] == "SUCCESS":
                insights = await self._get_ai_insights(
                    f"Document processing completed successfully. "
                    f"Analysis: {result['analysis']}. "
                    f"Stats: {result['processing'].get('stats')}. "
                    f"Provide a brief summary and any recommendations."
                )
                result["insights"] = insights
            
            return result
            
        except Exception as e:
            result["status"] = "FAILED"
            result["errors"].append(str(e))
            return result
    
    async def _get_ai_insights(self, prompt: str) -> Optional[str]:
        """
        Get AI insights using the chat service.
        
        Args:
            prompt: Prompt for AI analysis
            
        Returns:
            AI response text or None if unavailable
        """
        if not self.api_key:
            return None
        
        try:
            chat_service = self.kernel.get_service("chat")
            
            # Get execution settings
            settings = chat_service.get_prompt_execution_settings_class()(
                max_tokens=500,
                temperature=0.7,
            )
            
            # Create temporary history for this query
            temp_history = ChatHistory()
            temp_history.add_user_message(prompt)
            
            response = await chat_service.get_chat_message_content(
                chat_history=temp_history,
                settings=settings,
                kernel=self.kernel,
            )
            
            return str(response) if response else None
            
        except Exception as e:
            print(f"[AI] Insights error: {e}")
            return None
    
    async def interactive_document_generation(self) -> None:
        """
        Run interactive document generation mode.
        
        Provides a conversational interface for document processing
        with AI assistance.
        """
        print("\n" + "=" * 60)
        print("🤖 AI Document Processing Assistant")
        print("=" * 60)
        print("\nI can help you process Open Negotiation documents.")
        print("Available commands:")
        print("  - 'analyze <path>' - Analyze Excel data")
        print("  - 'validate <path>' - Validate data")
        print("  - 'process' - Start document generation")
        print("  - 'status' - Check processing status")
        print("  - 'quit' - Exit")
        print("\nOr just tell me what you need in natural language!")
        print("-" * 60)
        
        excel_path = None
        template_path = None
        output_folder = "output"
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("\n👋 Goodbye!")
                    break
                
                # Handle quick commands
                if user_input.lower().startswith('analyze '):
                    path = user_input[8:].strip()
                    result = await self.plugin.analyze_data(path)
                    print(f"\n🤖 Assistant:\n{result}")
                    excel_path = path
                    continue
                
                if user_input.lower().startswith('validate '):
                    path = user_input[9:].strip()
                    result = await self.plugin.validate_data(path, template_path)
                    print(f"\n🤖 Assistant:\n{result}")
                    excel_path = path
                    continue
                
                if user_input.lower() == 'status':
                    result = self.plugin.get_processing_status()
                    print(f"\n🤖 Assistant:\n{result}")
                    continue
                
                if user_input.lower() == 'process':
                    if not excel_path:
                        print("\n🤖 Assistant: Please provide an Excel path first using 'analyze <path>'")
                        continue
                    if not template_path:
                        template_path = input("📄 Template path: ").strip()
                    
                    print("\n🤖 Assistant: Starting document processing...")
                    result = await self.process_with_ai_guidance(
                        excel_path=excel_path,
                        template_docx=template_path,
                        output_folder=output_folder,
                    )
                    print(f"\n{json.dumps(result, indent=2)}")
                    continue
                
                # Use AI for natural language processing
                if self.api_key:
                    self.chat_history.add_user_message(user_input)
                    
                    chat_service = self.kernel.get_service("chat")
                    settings = chat_service.get_prompt_execution_settings_class()(
                        max_tokens=1000,
                        temperature=0.7,
                        function_choice_behavior=FunctionChoiceBehavior.Auto(),
                    )
                    
                    response = await chat_service.get_chat_message_content(
                        chat_history=self.chat_history,
                        settings=settings,
                        kernel=self.kernel,
                    )
                    
                    print(f"\n🤖 Assistant: {response}")
                    self.chat_history.add_assistant_message(str(response))
                else:
                    print("\n🤖 Assistant: AI features require an API key. Use commands instead.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def process_batch(
        self,
        configurations: List[Dict[str, str]],
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process multiple document configurations.
        
        Args:
            configurations: List of config dicts with excel_path, template_docx, output_folder
            parallel: Whether to process in parallel
            
        Returns:
            List of processing results
        """
        import asyncio
        
        async def process_one(config: Dict[str, str]) -> Dict[str, Any]:
            return await self.process_with_ai_guidance(
                excel_path=config["excel_path"],
                template_docx=config["template_docx"],
                output_folder=config["output_folder"],
            )
        
        if parallel:
            results = await asyncio.gather(
                *[process_one(config) for config in configurations],
                return_exceptions=True
            )
            return [
                r if isinstance(r, dict) else {"status": "FAILED", "error": str(r)}
                for r in results
            ]
        else:
            results = []
            for config in configurations:
                result = await process_one(config)
                results.append(result)
            return results
