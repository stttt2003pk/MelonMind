import logging
from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import re

logger = logging.getLogger(__name__)


def format_response(success: bool, data: Any = None, message: str = "", 
                   error_code: str = "") -> Dict[str, Any]:
    """
    格式化API响应
    
    Args:
        success: 是否成功
        data: 响应数据
        message: 响应消息
        error_code: 错误码
        
    Returns:
        格式化的响应字典
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
    验证JSON字符串格式
    
    Args:
        data: 待验证的JSON字符串
        
    Returns:
        是否为有效JSON
    """
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    掩码敏感数据
    
    Args:
        data: 原始数据字典
        sensitive_keys: 敏感字段列表
        
    Returns:
        掩码后的数据字典
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
    从文本中提取IP地址
    
    Args:
        text: 输入文本
        
    Returns:
        IP地址列表
    """
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.findall(ip_pattern, text)


def calculate_execution_time(start_time: datetime, end_time: datetime) -> float:
    """
    计算执行时间（秒）
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        执行时间（秒）
    """
    return (end_time - start_time).total_seconds()


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        分块后的列表
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_get_nested_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    安全获取嵌套字典值
    
    Args:
        data: 字典数据
        keys: 键路径列表
        default: 默认值
        
    Returns:
        获取到的值或默认值
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
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否为有效邮箱
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None