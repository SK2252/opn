"""
File Utilities for the Document Agent System.

Provides safe file operations including copying, merging,
path sanitization, and extension validation.
"""

import os
import re
import shutil
from typing import List, Optional, Set


# Allowed file extensions for processing
ALLOWED_EXTENSIONS: Set[str] = {".xls", ".xlsx", ".doc", ".docx", ".pdf"}


def is_allowed_file(filename: str, allowed_extensions: Optional[Set[str]] = None) -> bool:
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: Name or path of the file
        allowed_extensions: Set of allowed extensions (with leading dot)
        
    Returns:
        True if file extension is allowed
        
    Example:
        >>> is_allowed_file("document.pdf")
        True
        >>> is_allowed_file("script.py")
        False
    """
    extensions = allowed_extensions or ALLOWED_EXTENSIONS
    ext = os.path.splitext(filename)[1].lower()
    return ext in extensions


def safe_filename(value: str, replacement: str = "_") -> str:
    """
    Convert a string to a safe filename.
    
    Removes or replaces characters that are invalid in filenames.
    
    Args:
        value: String to convert
        replacement: Character to replace invalid chars with
        
    Returns:
        Safe filename string
        
    Example:
        >>> safe_filename("Report: Q1/2024")
        'Report__Q1_2024'
    """
    # Replace invalid filename characters
    invalid_chars = r'[\\/:"*?<>|]'
    result = re.sub(invalid_chars, replacement, str(value).strip())
    
    # Remove consecutive replacement chars
    while replacement + replacement in result:
        result = result.replace(replacement + replacement, replacement)
    
    # Remove leading/trailing replacement chars
    return result.strip(replacement)


def safe_folder_name(value: str) -> str:
    """
    Convert a string to a safe folder name.
    
    More restrictive than safe_filename - only allows alphanumeric and underscores.
    
    Args:
        value: String to convert
        
    Returns:
        Safe folder name string
        
    Example:
        >>> safe_folder_name("Provider #123")
        'Provider_123'
    """
    return "".join(c if c.isalnum() else "_" for c in str(value).strip())


def safe_copy(
    src_path: str,
    dest_folder: str,
    overwrite: bool = False
) -> str:
    """
    Copy a file with automatic renaming if destination exists.
    
    Args:
        src_path: Source file path
        dest_folder: Destination folder
        overwrite: If True, overwrite existing file
        
    Returns:
        Path to the copied file
        
    Raises:
        FileNotFoundError: If source file doesn't exist
        
    Example:
        >>> safe_copy("report.pdf", "output")
        'output/report.pdf'
        >>> safe_copy("report.pdf", "output")  # File exists
        'output/report_1.pdf'
    """
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source file not found: {src_path}")
    
    os.makedirs(dest_folder, exist_ok=True)
    
    base, ext = os.path.splitext(os.path.basename(src_path))
    final_path = os.path.join(dest_folder, base + ext)
    
    if not overwrite:
        counter = 1
        while os.path.exists(final_path):
            final_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
            counter += 1
    
    shutil.copy2(src_path, final_path)
    return final_path


def merge_folders(
    folder1: str,
    folder2: str,
    output_folder: str,
    allowed_extensions: Optional[Set[str]] = None
) -> int:
    """
    Merge files from two folders into a single output folder.
    
    Preserves directory structure and handles name conflicts
    by auto-renaming.
    
    Args:
        folder1: First source folder
        folder2: Second source folder
        output_folder: Destination folder
        allowed_extensions: Set of allowed extensions (filters files)
        
    Returns:
        Number of files copied
        
    Example:
        >>> merge_folders("groups", "notices", "merged")
        42
    """
    extensions = allowed_extensions or ALLOWED_EXTENSIONS
    copied_count = 0
    
    os.makedirs(output_folder, exist_ok=True)
    
    for root_folder in [folder1, folder2]:
        if not os.path.exists(root_folder):
            continue
        
        for root, _, files in os.walk(root_folder):
            rel_path = os.path.relpath(root, root_folder)
            dest_subfolder = os.path.join(output_folder, rel_path)
            os.makedirs(dest_subfolder, exist_ok=True)
            
            for file in files:
                if is_allowed_file(file, extensions):
                    src_path = os.path.join(root, file)
                    try:
                        safe_copy(src_path, dest_subfolder)
                        copied_count += 1
                    except Exception:
                        pass
    
    return copied_count


def ensure_directory(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The directory path
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB, or 0 if file doesn't exist
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0.0


def list_files_by_extension(
    directory: str,
    extensions: Optional[Set[str]] = None,
    recursive: bool = True
) -> List[str]:
    """
    List all files with specified extensions in a directory.
    
    Args:
        directory: Directory to search
        extensions: Set of extensions to include
        recursive: Whether to search subdirectories
        
    Returns:
        List of file paths
    """
    extensions = extensions or ALLOWED_EXTENSIONS
    files = []
    
    if not os.path.exists(directory):
        return files
    
    if recursive:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if is_allowed_file(filename, extensions):
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) and is_allowed_file(filename, extensions):
                files.append(file_path)
    
    return files


def clean_directory(directory: str, extensions: Optional[Set[str]] = None) -> int:
    """
    Remove files with specified extensions from a directory.
    
    Args:
        directory: Directory to clean
        extensions: Extensions to remove (if None, removes all allowed extensions)
        
    Returns:
        Number of files removed
    """
    extensions = extensions or ALLOWED_EXTENSIONS
    removed = 0
    
    for file_path in list_files_by_extension(directory, extensions):
        try:
            os.remove(file_path)
            removed += 1
        except Exception:
            pass
    
    return removed
