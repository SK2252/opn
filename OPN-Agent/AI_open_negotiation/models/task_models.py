"""
Task Models for the Document Agent System.

Contains dataclasses and enums for managing document processing tasks
with comprehensive status tracking and metadata support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    """Status enum for document processing tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_FAILURE = "partial_failure"
    CANCELLED = "cancelled"


class DocumentType(Enum):
    """Types of documents that can be generated."""
    OPEN_NEG_GROUP = "open_neg_group"
    OPEN_NEG_NOTICE = "open_neg_notice"
    EMAIL_DRAFT = "email_draft"
    MERGED_OUTPUT = "merged_output"


@dataclass
class DocumentTask:
    """
    Represents a document processing task with full lifecycle tracking.
    
    Attributes:
        task_id: Unique identifier for the task
        document_type: Type of document being processed
        input_data: Configuration and input data for processing
        status: Current status of the task
        retry_count: Number of retry attempts made
        max_retries: Maximum allowed retry attempts
        metadata: Additional task metadata and results
        error_message: Error details if task failed
        created_at: Timestamp when task was created
        updated_at: Timestamp of last status update
        
    Example:
        >>> task = DocumentTask(
        ...     task_id="doc_001",
        ...     document_type=DocumentType.OPEN_NEG_GROUP,
        ...     input_data={"excel_path": "data.xlsx"}
        ... )
        >>> task.status
        <TaskStatus.PENDING: 'pending'>
    """
    task_id: str
    document_type: DocumentType
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def mark_in_progress(self) -> None:
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def mark_completed(self, stats: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as completed with optional statistics."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now()
        if stats:
            self.metadata["stats"] = stats
    
    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.now()
    
    def mark_partial_failure(self, error: str, stats: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as partially failed with error and partial results."""
        self.status = TaskStatus.PARTIAL_FAILURE
        self.error_message = error
        self.updated_at = datetime.now()
        if stats:
            self.metadata["stats"] = stats
    
    def can_retry(self) -> bool:
        """Check if task can be retried based on retry count."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment retry counter and reset status to pending."""
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
