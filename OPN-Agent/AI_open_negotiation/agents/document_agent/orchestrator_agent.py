"""
Orchestrator Agent for the Document Agent System.

Main controller that coordinates all other agents in the document
processing pipeline with parallel execution and error aggregation.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from AI_open_negotiation.agents.document_agent.base_agent import BaseAgent
from AI_open_negotiation.agents.document_agent.validation_agent import ValidationAgent
from AI_open_negotiation.agents.document_agent.generation_agents import (
    GroupGenerationAgent,
    NoticeGenerationAgent,
    MergeAgent,
)
from AI_open_negotiation.models.task_models import DocumentTask, DocumentType, TaskStatus
from AI_open_negotiation.models.result_models import (
    GenerationStats,
    ProcessingResult,
    ValidationResult,
)


class OrchestratorAgent(BaseAgent):
    """
    Master orchestrator that coordinates the document processing pipeline.
    
    Pipeline stages:
    1. Validation - Pre-processing data validation
    2. Generation - Parallel document generation (Groups + Notices)
    3. Post-processing - Merge outputs from all generators
    
    Features:
    - Parallel execution of independent agents
    - Error aggregation and partial success handling
    - Comprehensive statistics tracking
    - Configurable pipeline stages
    
    Example:
        >>> config = {
        ...     'max_retries': 3,
        ...     'enable_parallel_processing': True
        ... }
        >>> orchestrator = OrchestratorAgent(config)
        >>> result = await orchestrator.process_document_request({
        ...     'excel_path': 'data.xlsx',
        ...     'template_docx': 'template.docx',
        ...     'merged_output_folder': 'output/merged'
        ... })
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the OrchestratorAgent with sub-agents.
        
        Args:
            config: Configuration dictionary for all agents
        """
        super().__init__("Orchestrator", config)
        
        # Initialize sub-agents
        agent_config = config or {}
        self.agents = {
            'validator': ValidationAgent("ValidationAgent", agent_config),
            'group_generator': GroupGenerationAgent("GroupGenerator", agent_config),
            'notice_generator': NoticeGenerationAgent("NoticeGenerator", agent_config),
            'merger': MergeAgent("MergeAgent", agent_config),
        }
        
        self.log_info("Orchestrator initialized with all sub-agents")
    
    async def execute(self, task: DocumentTask) -> DocumentTask:
        """
        Execute the full document processing pipeline.
        
        Args:
            task: Master task with all configuration
            
        Returns:
            Task with aggregated results from all stages
        """
        self.start_timer()
        task.mark_in_progress()
        self.log_info(f"Starting orchestrated pipeline for task {task.task_id}")
        
        try:
            result = await self.process_document_request(task.input_data)
            
            task.metadata["result"] = result
            
            if result["status"] == "SUCCESS":
                task.mark_completed(result)
            elif result["status"] == "PARTIAL_FAILURE":
                task.mark_partial_failure(
                    "; ".join(result.get("errors", [])),
                    result
                )
            else:
                task.mark_failed("; ".join(result.get("errors", ["Unknown error"])))
            
            return task
            
        except Exception as e:
            self.log_error(f"Pipeline error: {e}")
            task.mark_failed(str(e))
            return task
    
    async def process_document_request(
        self, 
        document_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for document processing pipeline.
        
        Orchestrates validation, generation, and post-processing
        of Open Negotiation documents with comprehensive error
        handling and statistics tracking.
        
        Args:
            document_config: Configuration dictionary containing:
                - excel_path (str): Path to input Excel file
                - template_docx (str): Path to Word template
                - output_group_folder (str): Output path for groups
                - output_notice_folder (str): Output path for notices
                - merged_output_folder (str): Final merged output path
        
        Returns:
            Dictionary containing:
                - status (str): 'SUCCESS', 'FAILED', or 'PARTIAL_FAILURE'
                - output_folder (str): Path to final output
                - stats (dict): Generation statistics
                - errors (list): Error messages if any
                - warnings (list): Warning messages
                - duration_seconds (float): Total processing time
        
        Raises:
            ValueError: If required config keys are missing
        """
        self.start_timer()
        result = ProcessingResult(status="PENDING")
        
        try:
            # Validate configuration
            self._validate_config(document_config)
            
            # ==================== STAGE 1: VALIDATION ====================
            self.log_info("Stage 1: Validation")
            validation_task = DocumentTask(
                task_id=f"val_{uuid4().hex[:8]}",
                document_type=DocumentType.OPEN_NEG_GROUP,
                input_data=document_config
            )
            
            validation_result = await self.agents['validator'].execute(validation_task)
            
            if validation_result.status == TaskStatus.FAILED:
                result.status = "FAILED"
                result.errors.append(f"Validation failed: {validation_result.error_message}")
                result.validation_result = ValidationResult(
                    is_valid=False,
                    errors=[validation_result.error_message or "Validation failed"]
                )
                result.mark_completed("FAILED")
                return result.to_dict()
            
            # Store validation warnings
            val_data = validation_result.metadata.get("validation_result", {})
            result.validation_result = ValidationResult(
                is_valid=True,
                warnings=val_data.get("warnings", []),
                total_records=val_data.get("total_records", 0),
                validated_records=val_data.get("validated_records", 0)
            )
            result.warnings.extend(val_data.get("warnings", []))
            
            # ==================== STAGE 2: GENERATION ====================
            self.log_info("Stage 2: Document Generation")
            
            # Prepare generation tasks
            group_task = DocumentTask(
                task_id=f"grp_{uuid4().hex[:8]}",
                document_type=DocumentType.OPEN_NEG_GROUP,
                input_data=document_config
            )
            
            notice_task = DocumentTask(
                task_id=f"ntc_{uuid4().hex[:8]}",
                document_type=DocumentType.OPEN_NEG_NOTICE,
                input_data=document_config
            )
            
            # Execute in parallel or sequential based on config
            if self.config.enable_parallel_processing:
                self.log_info("Executing generators in parallel")
                generation_results = await asyncio.gather(
                    self.agents['group_generator'].execute_with_retry(group_task),
                    self.agents['notice_generator'].execute_with_retry(notice_task),
                    return_exceptions=True
                )
            else:
                self.log_info("Executing generators sequentially")
                generation_results = [
                    await self.agents['group_generator'].execute_with_retry(group_task),
                    await self.agents['notice_generator'].execute_with_retry(notice_task),
                ]
            
            # Aggregate generation results
            combined_stats = GenerationStats()
            has_failures = False
            
            for gen_result in generation_results:
                if isinstance(gen_result, Exception):
                    result.errors.append(str(gen_result))
                    has_failures = True
                elif isinstance(gen_result, DocumentTask):
                    if gen_result.status == TaskStatus.FAILED:
                        result.errors.append(gen_result.error_message or "Generation failed")
                        has_failures = True
                    elif gen_result.status == TaskStatus.PARTIAL_FAILURE:
                        result.warnings.append(gen_result.error_message or "Partial failure")
                        has_failures = True
                    
                    # Merge statistics
                    stats_data = gen_result.metadata.get("stats", {})
                    gen_stats = GenerationStats(
                        total_records=stats_data.get("total_records", 0),
                        successful=stats_data.get("successful", 0),
                        failed=stats_data.get("failed", 0),
                        skipped=stats_data.get("skipped", 0),
                        duration_seconds=stats_data.get("duration_seconds", 0),
                        errors=stats_data.get("errors", [])
                    )
                    combined_stats = combined_stats.merge(gen_stats)
            
            result.stats = combined_stats
            
            # Check if all generation failed
            if combined_stats.successful == 0 and combined_stats.total_records > 0:
                result.status = "FAILED"
                result.errors.append("All document generation failed")
                result.mark_completed("FAILED")
                return result.to_dict()
            
            # ==================== STAGE 3: MERGE ====================
            self.log_info("Stage 3: Merging Outputs")
            
            merge_task = DocumentTask(
                task_id=f"mrg_{uuid4().hex[:8]}",
                document_type=DocumentType.MERGED_OUTPUT,
                input_data=document_config
            )
            
            merge_result = await self.agents['merger'].execute(merge_task)
            
            if merge_result.status == TaskStatus.FAILED:
                result.warnings.append(f"Merge failed: {merge_result.error_message}")
                # Continue - individual files are still available
            else:
                result.output_folder = document_config.get("merged_output_folder")
            
            # ==================== FINALIZE ====================
            if has_failures:
                result.status = "PARTIAL_FAILURE"
            else:
                result.status = "SUCCESS"
            
            result.mark_completed(result.status)
            
            self.log_info(
                f"Pipeline completed: {result.status} | "
                f"{combined_stats.successful} docs | "
                f"{self.get_elapsed_seconds():.1f}s"
            )
            
            return result.to_dict()
            
        except Exception as e:
            self.log_error(f"Pipeline error: {e}")
            result.status = "FAILED"
            result.errors.append(str(e))
            result.mark_completed("FAILED")
            return result.to_dict()
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate required configuration keys.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If required keys are missing
        """
        required_keys = ["excel_path"]
        missing = [k for k in required_keys if k not in config]
        
        if missing:
            raise ValueError(f"Missing required configuration keys: {missing}")
        
        # Set defaults for output folders
        if "output_group_folder" not in config:
            config["output_group_folder"] = "output/groups"
        if "output_notice_folder" not in config:
            config["output_notice_folder"] = "output/notices"
        if "merged_output_folder" not in config:
            config["merged_output_folder"] = "output/merged"
    
    async def get_agent_status(self) -> Dict[str, str]:
        """
        Get status of all sub-agents.
        
        Returns:
            Dictionary with agent name -> status
        """
        return {name: "ready" for name in self.agents.keys()}
