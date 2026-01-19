"""
Kernel Configuration for Semantic Kernel.

Provides kernel initialization with configurable AI services,
environment-based configuration, and execution settings.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from dotenv import load_dotenv

# Load environment variables
# Load environment variables (Centralized in opn/)
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))


@dataclass
class SystemConfig:
    """
    System configuration loaded from environment variables.
    
    Attributes:
        api_key: OpenAI API key
        model_id: AI model identifier
        log_level: Logging level
        max_retries: Maximum retry attempts
        timeout: Operation timeout in seconds
        enable_parallel: Enable parallel processing
        enable_ai: Enable AI features
    """
    api_key: str = field(default_factory=lambda: os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", ""))
    model_id: str = field(default_factory=lambda: os.getenv("GROK_MODEL") or os.getenv("AI_MODEL_ID", "gpt-4o-mini"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    timeout: int = field(default_factory=lambda: int(os.getenv("TIMEOUT", "300")))
    enable_parallel: bool = field(
        default_factory=lambda: os.getenv("ENABLE_PARALLEL_PROCESSING", "true").lower() == "true"
    )
    enable_ai: bool = field(
        default_factory=lambda: os.getenv("ENABLE_AI", "true").lower() == "true"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "model_id": self.model_id,
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "enable_parallel": self.enable_parallel,
            "enable_ai": self.enable_ai,
        }


def create_kernel(
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    config: Optional[SystemConfig] = None
) -> Kernel:
    """
    Create and configure a Semantic Kernel instance.
    
    Args:
        api_key: OpenAI API key (or from environment/config)
        model_id: AI model to use (or from environment/config)
        config: SystemConfig instance
        
    Returns:
        Configured Kernel instance
        
    Example:
        >>> kernel = create_kernel()
        >>> # or with explicit config
        >>> kernel = create_kernel(api_key="sk-...", model_id="gpt-4o")
    """
    # Load config
    if config is None:
        config = SystemConfig()
    
    # Use provided values or fall back to config
    api_key = api_key or config.api_key
    model_id = model_id or config.model_id
    
    # Create kernel
    kernel = Kernel()
    
    # Add Chat Completion Service if API key is available
    if api_key:
        # Determine if this is a Groq key
        is_groq = api_key.startswith("gsk_")
        
        # Configure service arguments
        service_args = {
            "service_id": "chat",
            "ai_model_id": model_id,
            "api_key": api_key,
        }
        
        # Add Groq base URL if using Groq key
        if is_groq:
            service_args["base_url"] = "https://api.groq.com/openai/v1"
            
        chat_service = OpenAIChatCompletion(**service_args)
        kernel.add_service(chat_service)
    
    return kernel


def get_execution_settings(
    max_tokens: int = 2000,
    temperature: float = 0.7,
    enable_function_calling: bool = True
):
    """
    Get execution settings for chat completion.
    
    Args:
        max_tokens: Maximum tokens in response
        temperature: Response temperature (0-1)
        enable_function_calling: Whether to enable function calling
        
    Returns:
        Execution settings object
    """
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
    
    settings = OpenAIChatPromptExecutionSettings(
        max_tokens=max_tokens,
        temperature=temperature,
    )
    
    if enable_function_calling:
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    
    return settings


# Global config instance
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get or create the global configuration."""
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config


def load_config_from_env() -> SystemConfig:
    """Force reload configuration from environment."""
    global _config
    _config = SystemConfig()
    return _config
