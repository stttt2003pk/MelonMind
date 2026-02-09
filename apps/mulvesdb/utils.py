"""
Milvus数据库块级去重工具函数
实现基于复合哈希的内容去重功能
"""
import hashlib
import logging
from typing import List, Dict, Set, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


def calculate_chunk_hash(content: str, document_id: int, chunk_index: int) -> str:
    """
    计算块级复合哈希值
    
    采用复合哈希策略避免不同文件相同内容被误判为重复
    Hash = SHA256(document_id:chunk_index:content)
    
    Args:
        content (str): 块内容文本
        document_id (int): 文档ID
        chunk_index (int): 块索引
        
    Returns:
        str: 64位十六进制哈希值
    """
    if not isinstance(content, str):
        raise TypeError("content must be string")
    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("document_id must be positive integer")
    if not isinstance(chunk_index, int) or chunk_index < 0:
        raise ValueError("chunk_index must be non-negative integer")
    
    # 构造复合内容字符串
    composite_content = f"{document_id}:{chunk_index}:{content}"
    
    # 计算SHA-256哈希
    hash_object = hashlib.sha256(composite_content.encode('utf-8'))
    return hash_object.hexdigest()


def calculate_chunk_hash_simple(content: str) -> str:
    """
    计算简单内容哈希（用于全局去重模式）
    
    Args:
        content (str): 块内容文本
        
    Returns:
        str: 64位十六进制哈希值
    """
    if not isinstance(content, str):
        raise TypeError("content must be string")
    
    hash_object = hashlib.sha256(content.encode('utf-8'))
    return hash_object.hexdigest()


class ChunkDeduplicationManager:
    """块级去重管理器"""
    
    def __init__(self, cache_size: int = 10000):
        """
        初始化去重管理器
        
        Args:
            cache_size (int): LRU缓存大小，默认10000条记录
        """
        self.cache_size = cache_size
        self._hash_cache = set()
        self._stats = {
            'total_checked': 0,
            'duplicates_found': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def is_duplicate(self, hash_value: str) -> bool:
        """
        检查哈希值是否重复
        
        Args:
            hash_value (str): 要检查的哈希值
            
        Returns:
            bool: True表示重复，False表示新内容
        """
        if not isinstance(hash_value, str) or len(hash_value) != 64:
            raise ValueError("Invalid hash value format")
        
        self._stats['total_checked'] += 1
        
        # 检查内存缓存
        if hash_value in self._hash_cache:
            self._stats['cache_hits'] += 1
            self._stats['duplicates_found'] += 1
            return True
        else:
            self._stats['cache_misses'] += 1
            return False
    
    def add_hash(self, hash_value: str) -> bool:
        """
        添加哈希值到去重集合
        
        Args:
            hash_value (str): 要添加的哈希值
            
        Returns:
            bool: True表示添加成功，False表示已存在
        """
        if not isinstance(hash_value, str) or len(hash_value) != 64:
            raise ValueError("Invalid hash value format")
        
        if hash_value in self._hash_cache:
            return False
        
        # 维护缓存大小限制
        if len(self._hash_cache) >= self.cache_size:
            # 移除最早的记录（简单实现，实际可使用OrderedDict）
            oldest_hash = next(iter(self._hash_cache))
            self._hash_cache.remove(oldest_hash)
        
        self._hash_cache.add(hash_value)
        return True
    
    def batch_check_duplicates(self, hash_values: List[str]) -> List[bool]:
        """
        批量检查重复
        
        Args:
            hash_values (List[str]): 哈希值列表
            
        Returns:
            List[bool]: 对应位置的重复检查结果
        """
        return [self.is_duplicate(hash_val) for hash_val in hash_values]
    
    def batch_add_hashes(self, hash_values: List[str]) -> int:
        """
        批量添加哈希值
        
        Args:
            hash_values (List[str]): 哈希值列表
            
        Returns:
            int: 成功添加的数量
        """
        added_count = 0
        for hash_val in hash_values:
            if self.add_hash(hash_val):
                added_count += 1
        return added_count
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取去重统计信息
        
        Returns:
            Dict[str, int]: 统计数据
        """
        stats_copy = self._stats.copy()
        if stats_copy['total_checked'] > 0:
            stats_copy['duplicate_rate'] = round(
                stats_copy['duplicates_found'] / stats_copy['total_checked'] * 100, 2
            )
        else:
            stats_copy['duplicate_rate'] = 0.0
        return stats_copy
    
    def reset_statistics(self):
        """重置统计信息"""
        self._stats = {
            'total_checked': 0,
            'duplicates_found': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._hash_cache.clear()
        logger.info("块级去重缓存已清空")


# 全局单例实例（可根据需要创建多个实例）
_default_dedup_manager = ChunkDeduplicationManager()


def get_default_dedup_manager() -> ChunkDeduplicationManager:
    """获取默认的去重管理器实例"""
    return _default_dedup_manager


def filter_duplicate_chunks(chunks_data: List[Dict], document_id: int, 
                          dedup_manager: Optional[ChunkDeduplicationManager] = None) -> List[Dict]:
    """
    过滤重复的块数据
    
    Args:
        chunks_data (List[Dict]): 块数据列表，每项包含{'content': str, 'chunk_index': int, ...}
        document_id (int): 文档ID
        dedup_manager (ChunkDeduplicationManager, optional): 去重管理器实例
        
    Returns:
        List[Dict]: 过滤后的不重复块数据
    """
    if dedup_manager is None:
        dedup_manager = get_default_dedup_manager()
    
    filtered_chunks = []
    duplicate_count = 0
    
    for chunk in chunks_data:
        # 计算复合哈希
        chunk_hash = calculate_chunk_hash(
            content=chunk['content'],
            document_id=document_id,
            chunk_index=chunk['chunk_index']
        )
        
        # 检查是否重复
        if not dedup_manager.is_duplicate(chunk_hash):
            filtered_chunks.append(chunk)
            dedup_manager.add_hash(chunk_hash)
        else:
            duplicate_count += 1
            logger.debug(f"发现重复块: document_id={document_id}, chunk_index={chunk['chunk_index']}")
    
    if duplicate_count > 0:
        logger.info(f"文档 {document_id} 中过滤掉 {duplicate_count} 个重复块")
    
    return filtered_chunks


# 便捷函数
def quick_dedup_check(content: str, document_id: int, chunk_index: int) -> bool:
    """
    快速去重检查（使用默认管理器）
    
    Args:
        content (str): 块内容
        document_id (int): 文档ID
        chunk_index (int): 块索引
        
    Returns:
        bool: True表示重复，False表示新内容
    """
    chunk_hash = calculate_chunk_hash(content, document_id, chunk_index)
    return get_default_dedup_manager().is_duplicate(chunk_hash)