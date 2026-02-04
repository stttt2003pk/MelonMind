import logging
from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import re

logger = logging.getLogger(__name__)


def format_response(success: bool, data: Any = None, message: str = "", 
                   error_code: str = "") -> Dict[str, Any]:
    """
    Format API response
    
    Args:
        success: Whether the operation was successful
        data: Response data
        message: Response message
        error_code: Error code
        
    Returns:
        Formatted response dictionary
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'data': data,
        'message': message
    }
    
    if error_code:
        response['error_code'] = error_code
        
    return response


def validate_json(data: str) -> bool:
    """
    Validate JSON string format
    
    Args:
        data: JSON string to validate
        
    Returns:
        Whether it's valid JSON
    """
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive data
    
    Args:
        data: Original data dictionary
        sensitive_keys: List of sensitive field names
        
    Returns:
        Data dictionary with masked sensitive fields
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'secret', 'key']
    
    masked_data = data.copy()
    
    for key, value in data.items():
        if isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, sensitive_keys)
        elif any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            masked_data[key] = '***MASKED***'
    
    return masked_data


def extract_ip_addresses(text: str) -> List[str]:
    """
    Extract IP addresses from text
    
    Args:
        text: Input text
        
    Returns:
        List of IP addresses
    """
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.findall(ip_pattern, text)


def calculate_execution_time(start_time: datetime, end_time: datetime) -> float:
    """
    Calculate execution time in seconds
    
    Args:
        start_time: Start time
        end_time: End time
        
    Returns:
        Execution time in seconds
    """
    return (end_time - start_time).total_seconds()


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks
    
    Args:
        lst: Original list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_get_nested_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary value
    
    Args:
        data: Dictionary data
        keys: List of key paths
        default: Default value
        
    Returns:
        Retrieved value or default value
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError):
        return default


def is_valid_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address
        
    Returns:
        Whether it's a valid email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None