"""
Base Agent for the Document Agent System.

Provides an abstract base class for all agents with common functionality
including logging, configuration, retry logic, and error handling.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar

from AI_open_negotiation.models.task_models import DocumentTask, TaskStatus


T = TypeVar("T")


@dataclass
class AgentConfig:
    """
    Configuration for agent behavior.
    
    Attributes:
        max_retries: Maximum retry attempts for failed operations
        retry_delay_seconds: Initial delay between retries
        retry_backoff_multiplier: Multiplier for exponential backoff
        timeout_seconds: Maximum time for operation completion
        enable_parallel_processing: Whether to enable parallel processing
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0
    timeout_seconds: int = 300
    enable_parallel_processing: bool = True
    log_level: str = "INFO"
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all document processing agents.
    
    Provides common functionality including:
    - Structured logging with agent name prefix
    - Configuration management
    - Retry logic with exponential backoff
    - Error handling and reporting
    - Async execution support
    
    Subclasses must implement the `execute` method.
    
    Example:
        >>> class MyAgent(BaseAgent):
        ...     async def execute(self, task: DocumentTask) -> DocumentTask:
        ...         # Implementation here
        ...         task.mark_completed()
        ...         return task
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent with name and configuration.
        
        Args:
            name: Human-readable name for the agent
            config: Configuration dictionary (converted to AgentConfig)
        """
        self.name = name
        self.config = self._parse_config(config or {})
        self.logger = self._setup_logger()
        self._start_time: Optional[datetime] = None
    
    def _parse_config(self, config: Dict[str, Any]) -> AgentConfig:
        """Parse dictionary config into AgentConfig dataclass."""
        return AgentConfig(
            max_retries=config.get("max_retries", 3),
            retry_delay_seconds=config.get("retry_delay_seconds", 1.0),
            retry_backoff_multiplier=config.get("retry_backoff_multiplier", 2.0),
            timeout_seconds=config.get("timeout_seconds", 300),
            enable_parallel_processing=config.get("enable_parallel_processing", True),
            log_level=config.get("log_level", "INFO"),
            custom_settings=config.get("custom_settings", {}),
        )
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up structured logger for the agent.
        
        Returns:
            Configured logger instance with agent name prefix.
        """
        logger = logging.getLogger(f"Agent.{self.name}")
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        
        # Add handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"%(asctime)s [{self.name}] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def execute(self, task: DocumentTask) -> DocumentTask:
        """
        Execute the agent's primary task.
        
        Must be implemented by subclasses.
        
        Args:
            task: The document task to process
            
        Returns:
            The processed task with updated status and metadata
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    async def execute_with_retry(self, task: DocumentTask) -> DocumentTask:
        """
        Execute task with automatic retry on failure.
        
        Uses exponential backoff for retry delays.
        
        Args:
            task: The document task to process
            
        Returns:
            The processed task, possibly after retries
        """
        last_error: Optional[Exception] = None
        
        while task.can_retry():
            try:
                self.logger.info(f"Executing task {task.task_id} (attempt {task.retry_count + 1})")
                result = await self.execute(task)
                
                if result.status == TaskStatus.COMPLETED:
                    return result
                elif result.status == TaskStatus.FAILED and result.can_retry():
                    task.increment_retry()
                    delay = self._calculate_retry_delay(task.retry_count)
                    self.logger.warning(f"Task failed, retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    return result
                    
            except Exception as e:
                last_error = e
                self.logger.error(f"Exception during execution: {e}")
                
                if task.can_retry():
                    task.increment_retry()
                    delay = self._calculate_retry_delay(task.retry_count)
                    self.logger.warning(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    task.mark_failed(str(e))
                    return task
        
        # Max retries exceeded
        error_msg = str(last_error) if last_error else "Max retries exceeded"
        task.mark_failed(error_msg)
        self.logger.error(f"Task {task.task_id} failed after {task.retry_count} retries")
        return task
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry using exponential backoff.
        
        Args:
            attempt: Current retry attempt number
            
        Returns:
            Delay in seconds before next retry
        """
        return self.config.retry_delay_seconds * (
            self.config.retry_backoff_multiplier ** (attempt - 1)
        )
    
    async def run_with_timeout(
        self,
        coro: Callable[..., T],
        *args,
        timeout: Optional[int] = None,
        **kwargs
    ) -> T:
        """
        Run a coroutine with timeout.
        
        Args:
            coro: Coroutine function to execute
            *args: Positional arguments for the coroutine
            timeout: Timeout in seconds (uses config default if None)
            **kwargs: Keyword arguments for the coroutine
            
        Returns:
            Result of the coroutine
            
        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        timeout = timeout or self.config.timeout_seconds
        return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
    
    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def log_debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def start_timer(self) -> None:
        """Start the execution timer."""
        self._start_time = datetime.now()
    
    def get_elapsed_seconds(self) -> float:
        """
        Get elapsed time since timer started.
        
        Returns:
            Elapsed time in seconds, or 0 if timer not started.
        """
        if self._start_time is None:
            return 0.0
        return (datetime.now() - self._start_time).total_seconds()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
