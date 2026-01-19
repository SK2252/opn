"""
File resolution module for auto-discovering input files based on patterns.
Uses glob matching to find Excel templates and Word templates.
Migrated from orchestrator service into Repi.
"""

import glob
import os
from typing import Dict, Optional, List
from pathlib import Path


class FileResolver:
    """Resolves file paths based on client name and wave number patterns."""
    
    def __init__(self, base_path: str):
        """
        Initialize file resolver.
        
        Args:
            base_path: Base directory to search for files
        """
        self.base_path = Path(base_path).resolve()
        
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")
    
    def resolve_files(
        self, 
        client_name: str, 
        wave_number: str, 
        patterns: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """
        Resolve file paths using glob patterns.
        
        Args:
            client_name: Client identifier (e.g., "CEP")
            wave_number: Wave identifier (e.g., "W6")
            patterns: Dictionary of file type to pattern mappings
        
        Returns:
            Dictionary mapping file types to resolved absolute paths
            
        Example:
            patterns = {
                "excel": "{client_name} {wave_number}*.xlsx",
                "template": "*Template*.docx"
            }
            
            Returns:
            {
                "excel": "/absolute/path/to/CEP W6 OPNNEG TEMPLATE.xlsx",
                "template": "/absolute/path/to/OpenNeg_CEP_Template.docx"
            }
        """
        resolved = {}
        
        for file_type, pattern in patterns.items():
            # Replace placeholders in pattern
            resolved_pattern = pattern.format(
                client_name=client_name,
                wave_number=wave_number
            )
            
            # Build full search path
            search_path = self.base_path / resolved_pattern
            
            # Find matching files
            matches = glob.glob(str(search_path))
            
            if matches:
                # Use first match and convert to absolute path
                resolved[file_type] = str(Path(matches[0]).resolve())
            else:
                resolved[file_type] = None
        
        return resolved
    
    def validate_resolved_files(
        self, 
        resolved: Dict[str, Optional[str]], 
        required: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate that all required files were resolved.
        
        Args:
            resolved: Dictionary of resolved file paths
            required: List of required file types
        
        Returns:
            Tuple of (is_valid, missing_files)
        """
        missing = []
        
        for file_type in required:
            if file_type not in resolved or resolved[file_type] is None:
                missing.append(file_type)
        
        is_valid = len(missing) == 0
        return is_valid, missing
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Get information about a resolved file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary with file metadata
        """
        if not file_path or not os.path.exists(file_path):
            return {
                "exists": False,
                "path": file_path,
                "size": None,
                "name": None
            }
        
        stat = os.stat(file_path)
        return {
            "exists": True,
            "path": file_path,
            "size": stat.st_size,
            "name": os.path.basename(file_path)
        }
