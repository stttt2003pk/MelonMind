import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Embedding结果数据结构"""
    text: str
    embedding: List[float]
    model: str
    dimensions: int
    metadata: Dict[str, Any]


class QwenEmbeddingService:
    """Qwen模型Embedding服务"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, 
                 model: str = "text-embedding-v1"):
        """
        初始化Qwen Embedding服务
        
        Args:
            api_key (str, optional): Qwen API密钥
            base_url (str, optional): API基础URL
            model (str): 使用的模型名称
        """
        self.api_key = api_key or getattr(settings, 'QWEN_API_KEY', os.getenv('QWEN_API_KEY'))
        self.base_url = base_url or getattr(settings, 'QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model = model
        self.dimensions = 128  # Qwen默认维度
        
        if not self.api_key:
            raise ValueError("Qwen API密钥未配置，请设置QWEN_API_KEY环境变量或在settings中配置")
        
        # 初始化OpenAI客户端（Qwen兼容OpenAI API格式）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def embed_text(self, text: str, **kwargs) -> EmbeddingResult:
        """
        对单个文本进行embedding
        
        Args:
            text (str): 要嵌入的文本
            **kwargs: 其他参数
            
        Returns:
            EmbeddingResult: Embedding结果
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                **kwargs
            )
            
            embedding = response.data[0].embedding
            
            return EmbeddingResult(
                text=text,
                embedding=embedding,
                model=self.model,
                dimensions=len(embedding),
                metadata={
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Qwen embedding失败: {str(e)}")
            raise Exception(f"文本embedding失败: {str(e)}")
    
    def embed_batch(self, texts: List[str], batch_size: int = 10, **kwargs) -> List[EmbeddingResult]:
        """
        批量对文本进行embedding
        
        Args:
            texts (List[str]): 文本列表
            batch_size (int): 批处理大小
            **kwargs: 其他参数
            
        Returns:
            List[EmbeddingResult]: Embedding结果列表
        """
        results = []
        
        # 分批处理以避免API限制
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.info(f"处理embedding批次 {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts,
                    **kwargs
                )
                
                # 处理批量响应
                for j, data in enumerate(response.data):
                    results.append(EmbeddingResult(
                        text=batch_texts[j],
                        embedding=data.embedding,
                        model=self.model,
                        dimensions=len(data.embedding),
                        metadata={
                            'batch_index': i + j,
                            'usage': {
                                'prompt_tokens': response.usage.prompt_tokens,
                                'total_tokens': response.usage.total_tokens
                            }
                        }
                    ))
                    
            except Exception as e:
                logger.error(f"批量embedding失败 (批次 {i//batch_size + 1}): {str(e)}")
                # 对失败的批次逐个处理
                for j, text in enumerate(batch_texts):
                    try:
                        single_result = self.embed_text(text, **kwargs)
                        single_result.metadata['batch_index'] = i + j
                        single_result.metadata['fallback_single'] = True
                        results.append(single_result)
                    except Exception as single_e:
                        logger.error(f"单个文本embedding失败: {str(single_e)}")
                        # 添加空embedding作为占位符
                        results.append(EmbeddingResult(
                            text=text,
                            embedding=[0.0] * self.dimensions,
                            model=self.model,
                            dimensions=self.dimensions,
                            metadata={
                                'batch_index': i + j,
                                'error': str(single_e),
                                'failed': True
                            }
                        ))
        
        return results
    
    def get_embedding_dimensions(self) -> int:
        """获取embedding维度"""
        return self.dimensions
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        验证embedding的有效性
        
        Args:
            embedding (List[float]): embedding向量
            
        Returns:
            bool: 是否有效
        """
        if not isinstance(embedding, list):
            return False
        
        if len(embedding) != self.dimensions:
            return False
            
        # 检查是否包含有效的数值
        try:
            np_array = np.array(embedding, dtype=np.float32)
            return not np.isnan(np_array).any() and not np.isinf(np_array).any()
        except:
            return False


class MockEmbeddingService:
    """Mock Embedding服务（用于测试）"""
    
    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions
    
    def embed_text(self, text: str, **kwargs) -> EmbeddingResult:
        """生成mock embedding"""
        # 生成随机但一致的embedding（相同文本产生相同embedding）
        import hashlib
        hash_object = hashlib.md5(text.encode())
        seed = int(hash_object.hexdigest()[:8], 16)
        
        np.random.seed(seed % (2**32))
        embedding = np.random.randn(self.dimensions).tolist()
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model='mock-embedding',
            dimensions=self.dimensions,
            metadata={'mock': True}
        )
    
    def embed_batch(self, texts: List[str], **kwargs) -> List[EmbeddingResult]:
        """批量生成mock embedding"""
        return [self.embed_text(text, **kwargs) for text in texts]
    
    def get_embedding_dimensions(self) -> int:
        return self.dimensions


def get_embedding_service(use_mock: bool = False) -> QwenEmbeddingService:
    """
    获取embedding服务实例
    
    Args:
        use_mock (bool): 是否使用mock服务（用于测试）
        
    Returns:
        QwenEmbeddingService: embedding服务实例
    """
    if use_mock or getattr(settings, 'USE_MOCK_EMBEDDING', False):
        return MockEmbeddingService()
    else:
        return QwenEmbeddingService()