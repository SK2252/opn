"""
Data Formatters for the Document Agent System.

Provides formatting utilities for currency, dates, and other data types.
"""

from datetime import datetime
from typing import Any, Optional, Union

import pandas as pd


def format_currency(value: Any, default: str = "N/A") -> str:
    """
    Format a value as US currency.
    
    Handles various input formats including strings with $ and commas,
    numeric values, and special cases like NaN and N/A.
    
    Args:
        value: Value to format
        default: Default value for invalid/missing data
        
    Returns:
        Formatted currency string (e.g., "$1,234.56")
        
    Example:
        >>> format_currency(1234.5)
        '$1,234.50'
        >>> format_currency("$1,234.56")
        '$1,234.56'
        >>> format_currency(None)
        'N/A'
    """
    # Handle NA/None/NaN values
    if pd.isna(value) or value is None:
        return default
    
    value_str = str(value).strip()
    
    # Handle explicit N/A
    if value_str.upper() == "N/A":
        return default
    
    try:
        # Remove existing currency symbols and commas
        cleaned = value_str.replace("$", "").replace(",", "").strip()
        numeric_value = float(cleaned)
        return f"${numeric_value:,.2f}"
    except (ValueError, TypeError):
        return value_str


def format_date(
    value: Any,
    output_format: str = "%b %d, %Y",
    input_formats: Optional[list] = None,
    default: str = "N/A"
) -> str:
    """
    Format a date value to a specified format.
    
    Attempts to parse the date using multiple common formats
    before applying the output format.
    
    Args:
        value: Date value to format
        output_format: strftime format string for output
        input_formats: List of input format strings to try
        default: Default value for invalid dates
        
    Returns:
        Formatted date string
        
    Example:
        >>> format_date("2024-01-15")
        'Jan 15, 2024'
        >>> format_date(datetime(2024, 1, 15))
        'Jan 15, 2024'
    """
    if pd.isna(value) or value is None:
        return default
    
    # If already a datetime, format directly
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime(output_format)
    
    # Try parsing with pandas
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime(output_format)
    except Exception:
        pass
    
    # Try common input formats
    input_formats = input_formats or [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
    ]
    
    value_str = str(value).strip()
    
    for fmt in input_formats:
        try:
            parsed = datetime.strptime(value_str, fmt)
            return parsed.strftime(output_format)
        except ValueError:
            continue
    
    return default


def format_npi(value: Any, default: str = "N/A") -> str:
    """
    Format an NPI (National Provider Identifier).
    
    NPIs should be 10 digits. This function validates and formats.
    
    Args:
        value: NPI value
        default: Default for invalid NPIs
        
    Returns:
        Formatted NPI string
        
    Example:
        >>> format_npi(1234567890)
        '1234567890'
        >>> format_npi("123456789")
        'N/A'  # Too short
    """
    if pd.isna(value) or value is None:
        return default
    
    # Convert to string and strip
    npi_str = str(value).strip()
    
    # Remove any non-digit characters
    npi_digits = "".join(c for c in npi_str if c.isdigit())
    
    # NPI should be exactly 10 digits
    if len(npi_digits) == 10:
        return npi_digits
    
    return default


def format_percentage(
    value: Any,
    decimal_places: int = 2,
    default: str = "N/A"
) -> str:
    """
    Format a value as a percentage.
    
    Args:
        value: Numeric value (0-100 or 0-1)
        decimal_places: Number of decimal places
        default: Default for invalid values
        
    Returns:
        Formatted percentage string
        
    Example:
        >>> format_percentage(0.75)
        '75.00%'
        >>> format_percentage(75)
        '75.00%'
    """
    if pd.isna(value) or value is None:
        return default
    
    try:
        num_value = float(value)
        
        # If value is between 0 and 1, multiply by 100
        if 0 <= num_value <= 1:
            num_value *= 100
        
        return f"{num_value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return default


def format_phone(value: Any, default: str = "N/A") -> str:
    """
    Format a phone number to (XXX) XXX-XXXX format.
    
    Args:
        value: Phone number value
        default: Default for invalid phones
        
    Returns:
        Formatted phone string
        
    Example:
        >>> format_phone("1234567890")
        '(123) 456-7890'
    """
    if pd.isna(value) or value is None:
        return default
    
    # Extract digits only
    phone_str = str(value).strip()
    digits = "".join(c for c in phone_str if c.isdigit())
    
    # Handle 10-digit phones
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Handle 11-digit phones (with leading 1)
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    
    return phone_str if phone_str else default


def clean_string(value: Any, default: str = "") -> str:
    """
    Clean a string value for safe use.
    
    Strips whitespace, handles None/NaN, and optionally removes
    special characters.
    
    Args:
        value: String value
        default: Default for None/NaN
        
    Returns:
        Cleaned string
    """
    if pd.isna(value) or value is None:
        return default
    
    return str(value).strip()


def truncate_string(
    value: str,
    max_length: int,
    suffix: str = "..."
) -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        value: String to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated string
        
    Example:
        >>> truncate_string("Hello World", 8)
        'Hello...'
    """
    if len(value) <= max_length:
        return value
    
    return value[:max_length - len(suffix)] + suffix
