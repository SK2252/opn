"""
Advanced Document Plugin for Semantic Kernel.

Provides SK-compatible functions for document processing with
AI guidance, validation, and comprehensive statistics.
"""

import asyncio
import json
from typing import Annotated, Any, Dict, Optional

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from AI_open_negotiation.agents.document_agent.orchestrator_agent import OrchestratorAgent
from AI_open_negotiation.agents.document_agent.validation_agent import ValidationAgent
from AI_open_negotiation.models.task_models import DocumentTask, DocumentType
from AI_open_negotiation.models.result_models import ValidationResult


class AdvancedDocumentPlugin:
    """
    Semantic Kernel plugin for advanced document processing.
    
    Integrates the multi-agent document processing system with
    Semantic Kernel for AI-powered workflows.
    
    Functions:
    - create_documents: Full pipeline execution
    - validate_data: Pre-validation check
    - get_processing_status: Status query
    - analyze_data: AI-powered data analysis
    
    Example:
        >>> kernel = create_kernel(api_key)
        >>> plugin = AdvancedDocumentPlugin(kernel)
        >>> kernel.add_plugin(plugin, "DocumentPlugin")
    """
    
    def __init__(self, kernel: Optional[Kernel] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin with optional kernel and config.
        
        Args:
            kernel: Semantic Kernel instance for AI operations
            config: Configuration for underlying agents
        """
        self.kernel = kernel
        self.config = config or {}
        self._orchestrator: Optional[OrchestratorAgent] = None
        self._validator: Optional[ValidationAgent] = None
        self._last_result: Optional[Dict[str, Any]] = None
    
    @property
    def orchestrator(self) -> OrchestratorAgent:
        """Lazy initialization of orchestrator."""
        if self._orchestrator is None:
            self._orchestrator = OrchestratorAgent(self.config)
        return self._orchestrator
    
    @property
    def validator(self) -> ValidationAgent:
        """Lazy initialization of validator."""
        if self._validator is None:
            self._validator = ValidationAgent("PluginValidator", self.config)
        return self._validator
    
    @kernel_function(
        name="create_documents",
        description="Generate Open Negotiation documents (Excel groups and Word/PDF notices) from input data. Returns JSON with status, stats, and output location."
    )
    async def create_documents(
        self,
        excel_path: Annotated[str, "Path to input Excel file with claim data"],
        template_docx: Annotated[str, "Path to Word template for notices"],
        output_folder: Annotated[str, "Base output folder for all generated documents"],
    ) -> Annotated[str, "JSON string with processing result"]:
        """
        Generate Open Negotiation documents with full pipeline.
        
        Executes the complete document processing pipeline:
        1. Validates input data
        2. Generates group Excel files
        3. Generates notice Word/PDF files
        4. Merges outputs to final folder
        
        Args:
            excel_path: Path to input Excel file
            template_docx: Path to Word template
            output_folder: Base output folder
            
        Returns:
            JSON string containing:
            - status: SUCCESS, FAILED, or PARTIAL_FAILURE
            - output_folder: Path to merged output
            - stats: Generation statistics
            - errors: List of error messages
        """
        document_config = {
            "excel_path": excel_path,
            "template_docx": template_docx,
            "output_group_folder": f"{output_folder}/groups",
            "output_notice_folder": f"{output_folder}/notices",
            "merged_output_folder": f"{output_folder}/merged",
        }
        
        result = await self.orchestrator.process_document_request(document_config)
        self._last_result = result
        
        return json.dumps(result, indent=2, default=str)
    
    @kernel_function(
        name="validate_data",
        description="Validate input Excel data and template before processing. Returns JSON with validation result, errors, and warnings."
    )
    async def validate_data(
        self,
        excel_path: Annotated[str, "Path to input Excel file to validate"],
        template_docx: Annotated[Optional[str], "Optional path to Word template to validate"] = None,
    ) -> Annotated[str, "JSON string with validation result"]:
        """
        Validate input data before processing.
        
        Checks:
        - File existence
        - Required columns
        - Data types and formats
        - Template placeholders
        
        Args:
            excel_path: Path to Excel file
            template_docx: Optional template path
            
        Returns:
            JSON string with validation results
        """
        task = DocumentTask(
            task_id="validation_check",
            document_type=DocumentType.OPEN_NEG_GROUP,
            input_data={
                "excel_path": excel_path,
                "template_docx": template_docx,
            }
        )
        
        result_task = await self.validator.execute(task)
        validation_result = result_task.metadata.get("validation_result", {})
        
        return json.dumps({
            "is_valid": validation_result.get("is_valid", False),
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "total_records": validation_result.get("total_records", 0),
            "validated_records": validation_result.get("validated_records", 0),
        }, indent=2)
    
    @kernel_function(
        name="get_processing_status",
        description="Get the status of the last document processing run."
    )
    def get_processing_status(self) -> Annotated[str, "JSON string with last processing status"]:
        """
        Get status of last processing run.
        
        Returns:
            JSON string with last result or "no previous run"
        """
        if self._last_result is None:
            return json.dumps({"status": "no_previous_run", "message": "No processing has been run yet"})
        
        return json.dumps({
            "status": self._last_result.get("status"),
            "output_folder": self._last_result.get("output_folder"),
            "duration_seconds": self._last_result.get("duration_seconds"),
            "stats": self._last_result.get("stats"),
        }, indent=2)
    
    @kernel_function(
        name="analyze_data",
        description="Analyze Excel data and provide insights about the claims. Useful for understanding data before processing."
    )
    async def analyze_data(
        self,
        excel_path: Annotated[str, "Path to Excel file to analyze"],
    ) -> Annotated[str, "JSON string with data analysis"]:
        """
        Analyze input data and provide insights.
        
        Provides:
        - Record counts
        - Unique providers/plans
        - Data quality metrics
        - Processing estimates
        
        Args:
            excel_path: Path to Excel file
            
        Returns:
            JSON string with analysis results
        """
        import os
        import pandas as pd
        
        if not os.path.exists(excel_path):
            return json.dumps({"error": f"File not found: {excel_path}"})
        
        try:
            df = pd.read_excel(excel_path)
            df.columns = df.columns.str.strip()
            
            analysis = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
            }
            
            # Provider analysis
            if 'ProvOrgNPI' in df.columns:
                analysis["unique_providers"] = df['ProvOrgNPI'].nunique()
            
            # Insurance plan analysis
            if 'InsurancePlanName' in df.columns:
                analysis["unique_insurance_plans"] = df['InsurancePlanName'].nunique()
            
            # Group analysis
            if 'OpenNegGroup' in df.columns:
                analysis["group_files_to_generate"] = df['OpenNegGroup'].notna().sum()
            
            # Notice analysis
            if 'OpenNegNotice' in df.columns:
                unique_notices = df[df['OpenNegNotice'].notna()].drop_duplicates(
                    subset=['ProvOrgNPI', 'Hospital Name', 'OpenNegNotice', 'InsurancePlanName']
                )
                analysis["notice_files_to_generate"] = len(unique_notices)
            
            # Data quality
            null_counts = df.isnull().sum().to_dict()
            analysis["null_value_counts"] = {k: v for k, v in null_counts.items() if v > 0}
            
            # Estimate processing time
            total_files = analysis.get("group_files_to_generate", 0) + analysis.get("notice_files_to_generate", 0)
            analysis["estimated_processing_seconds"] = total_files * 0.5  # Rough estimate
            
            return json.dumps(analysis, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({"error": str(e)})


# Legacy compatibility wrapper
class DocumentSkill(AdvancedDocumentPlugin):
    """
    Legacy compatibility class for existing code.
    
    Wraps AdvancedDocumentPlugin with sync interface for backward compatibility.
    """
    
    @kernel_function(
        name="create_documents",
        description="Generate Open Negotiation documents (legacy interface)"
    )
    def create_documents(self, document_config: dict) -> dict:
        """
        Legacy sync interface for document creation.
        
        Args:
            document_config: Full configuration dictionary
            
        Returns:
            Result dictionary
        """
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async method
        result = loop.run_until_complete(
            self.orchestrator.process_document_request(document_config)
        )
        
        return result
