"""
PDF Loader 工具函数
包含文件哈希计算等实用功能
"""

import hashlib
import logging
from typing import Union
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    计算文件的SHA-256哈希值
    
    Args:
        file_path (Union[str, Path]): 文件路径
        chunk_size (int): 读取文件的块大小，默认8KB
        
    Returns:
        str: 文件的SHA-256哈希值（十六进制字符串）
        
    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件读取错误
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            # 分块读取文件以处理大文件
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        
        file_hash = sha256_hash.hexdigest()
        logger.debug(f"文件 {file_path} 的哈希值: {file_hash}")
        return file_hash
        
    except IOError as e:
        logger.error(f"读取文件失败 {file_path}: {str(e)}")
        raise IOError(f"无法读取文件 {file_path}: {str(e)}")


def is_duplicate_document(file_path: Union[str, Path]) -> tuple[bool, str]:
    """
    检查文件是否为重复文档
    
    Args:
        file_path (Union[str, Path]): 文件路径
        
    Returns:
        tuple[bool, str]: (是否重复, 文件哈希值)
    """
    try:
        file_hash = calculate_file_hash(file_path)
        
        # 导入在这里避免循环导入
        from .models import PDFDocument
        
        # 检查数据库中是否已存在相同哈希的文档
        exists = PDFDocument.exists_by_file_hash(file_hash)
        
        return exists, file_hash
        
    except Exception as e:
        logger.error(f"检查文档重复性失败: {str(e)}")
        return False, ""


def get_existing_document_by_hash(file_hash: str):
    """
    根据文件哈希值获取已存在的文档
    
    Args:
        file_hash (str): 文件哈希值
        
    Returns:
        PDFDocument or None: 已存在的文档对象或None
    """
    try:
        from .models import PDFDocument
        return PDFDocument.get_by_file_hash(file_hash)
    except Exception as e:
        logger.error(f"根据哈希值查找文档失败: {str(e)}")
        return None