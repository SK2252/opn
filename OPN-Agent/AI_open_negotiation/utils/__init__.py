"""
Utilities module for the Document Agent System.
"""

from .logger import log_info, log_warning, log_error, log_debug, log_critical, setup_logging
from .file_utils import (
    safe_copy,
    safe_filename,
    safe_folder_name,
    merge_folders,
    is_allowed_file,
    ensure_directory,
    list_files_by_extension,
)
from .formatters import (
    format_currency,
    format_date,
    format_npi,
    format_percentage,
    clean_string,
)

__all__ = [
    # Logging
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
    "log_critical",
    "setup_logging",
    # File utilities
    "safe_copy",
    "safe_filename",
    "safe_folder_name",
    "merge_folders",
    "is_allowed_file",
    "ensure_directory",
    "list_files_by_extension",
    # Formatters
    "format_currency",
    "format_date",
    "format_npi",
    "format_percentage",
    "clean_string",
]
