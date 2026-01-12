"""
Models module for the Document Agent System.
Contains dataclasses for tasks, results, and processing status.
"""

from .task_models import TaskStatus, DocumentType, DocumentTask
from .result_models import ValidationResult, GenerationStats, ProcessingResult

__all__ = [
    "TaskStatus",
    "DocumentType", 
    "DocumentTask",
    "ValidationResult",
    "GenerationStats",
    "ProcessingResult",
]
