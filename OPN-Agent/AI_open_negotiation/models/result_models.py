"""
Result Models for the Document Agent System.

Contains dataclasses for validation results, generation statistics,
and processing outcomes with comprehensive error tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """
    Result of data validation operations.
    
    Attributes:
        is_valid: Whether validation passed
        errors: List of critical errors that block processing
        warnings: List of non-critical warnings
        validated_records: Count of records that passed validation
        total_records: Total records examined
        
    Example:
        >>> result = ValidationResult(
        ...     is_valid=True,
        ...     errors=[],
        ...     warnings=["2 rows with missing optional data"],
        ...     validated_records=98,
        ...     total_records=100
        ... )
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_records: int = 0
    total_records: int = 0
    
    def add_error(self, error: str) -> None:
        """Add an error and mark validation as failed."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning (does not affect validity)."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "validated_records": self.validated_records,
            "total_records": self.total_records,
        }


@dataclass
class GenerationStats:
    """
    Statistics for document generation operations.
    
    Attributes:
        total_records: Total records to process
        successful: Count of successfully generated documents
        failed: Count of failed generation attempts
        skipped: Count of skipped records (e.g., missing data)
        duration_seconds: Time taken for generation
        output_files: List of generated file paths
        
    Example:
        >>> stats = GenerationStats(
        ...     total_records=100,
        ...     successful=95,
        ...     failed=2,
        ...     skipped=3,
        ...     duration_seconds=45.2
        ... )
        >>> stats.success_rate
        95.0
    """
    total_records: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    output_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.successful / self.total_records) * 100
    
    @property
    def is_complete_success(self) -> bool:
        """Check if all records were processed successfully."""
        return self.failed == 0 and self.skipped == 0
    
    def add_success(self, file_path: Optional[str] = None) -> None:
        """Record a successful generation."""
        self.successful += 1
        if file_path:
            self.output_files.append(file_path)
    
    def add_failure(self, error: str) -> None:
        """Record a failed generation with error."""
        self.failed += 1
        self.errors.append(error)
    
    def add_skipped(self) -> None:
        """Record a skipped record."""
        self.skipped += 1
    
    def merge(self, other: "GenerationStats") -> "GenerationStats":
        """Merge statistics from another GenerationStats instance."""
        return GenerationStats(
            total_records=self.total_records + other.total_records,
            successful=self.successful + other.successful,
            failed=self.failed + other.failed,
            skipped=self.skipped + other.skipped,
            duration_seconds=self.duration_seconds + other.duration_seconds,
            output_files=self.output_files + other.output_files,
            errors=self.errors + other.errors,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for serialization."""
        return {
            "total_records": self.total_records,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": round(self.success_rate, 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "output_files_count": len(self.output_files),
            "errors": self.errors,
        }


@dataclass
class ProcessingResult:
    """
    Final result of document processing pipeline.
    
    Attributes:
        status: Overall processing status (SUCCESS, FAILED, PARTIAL_FAILURE)
        output_folder: Path to final output folder
        stats: Generation statistics
        validation_result: Validation result if applicable
        errors: List of all errors encountered
        warnings: List of all warnings
        started_at: Processing start timestamp
        completed_at: Processing completion timestamp
        
    Example:
        >>> result = ProcessingResult(
        ...     status="SUCCESS",
        ...     output_folder="output/merged",
        ...     stats=GenerationStats(total_records=100, successful=100)
        ... )
    """
    status: str
    output_folder: Optional[str] = None
    stats: Optional[GenerationStats] = None
    validation_result: Optional[ValidationResult] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total processing duration in seconds."""
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()
    
    def mark_completed(self, status: str = "SUCCESS") -> None:
        """Mark processing as completed with timestamp."""
        self.status = status
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for API response."""
        result = {
            "status": self.status,
            "output_folder": self.output_folder,
            "duration_seconds": round(self.duration_seconds, 2),
            "errors": self.errors,
            "warnings": self.warnings,
        }
        
        if self.stats:
            result["stats"] = self.stats.to_dict()
        
        if self.validation_result:
            result["validation"] = self.validation_result.to_dict()
        
        return result
