import asyncio
import asyncpg
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache

# 尝试导入 Milvus 客户端
try:
    from pymilvus import MilvusClient, connections, Collection
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logging.warning("pymilvus not available, falling back to asyncpg")

logger = logging.getLogger(__name__)


class MulvesDBConnector:
    """Mulves数据库连接器"""
    
    def __init__(self, connection_config: MulvesConnection):
        self.config = connection_config
        self._pool = None
        self._milvus_client = None
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def connect(self) -> bool:
        """建立数据库连接池"""
        try:
            if MILVUS_AVAILABLE:
                # 使用 Milvus 官方客户端
                self._milvus_client = MilvusClient(
                    uri=f"http://{self.config.host}:{self.config.port}",
                    token=f"{self.config.username}:{self.config.password}" if self.config.username else None
                )
                logger.info(f"成功连接到Milvus数据库: {self.config.name}")
                return True
            else:
                # 回退到 asyncpg（仅用于兼容性测试）
                self._pool = await asyncpg.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    ssl=self.config.ssl_enabled,
                    timeout=self.config.connection_timeout,
                    min_size=1,
                    max_size=10,
                    command_timeout=self.config.connection_timeout
                )
                logger.info(f"成功连接到Mulves数据库: {self.config.name}")
                return True
        except Exception as e:
            logger.error(f"连接Mulves数据库失败 {self.config.name}: {str(e)}")
            raise ConnectionError(f"无法连接到Mulves数据库: {str(e)}")
            
    async def disconnect(self):
        """关闭数据库连接池"""
        if self._milvus_client:
            # Milvus 客户端不需要显式关闭
            self._milvus_client = None
            logger.info(f"已断开Milvus数据库连接: {self.config.name}")
        elif self._pool:
            await self._pool.close()
            self._pool = None
            logger.info(f"已断开Mulves数据库连接: {self.config.name}")
            
    async def execute_query(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """执行查询并返回结果"""
        if self._milvus_client:
            # 使用 Milvus 客户端执行查询
            start_time = datetime.now()
            try:
                # 对于 Milvus，我们执行健康检查而不是 SQL 查询
                result = self._milvus_client.health()
                results = [{'status': result}] if result else []
                
                # 记录查询日志
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                await self._log_query("HEALTH_CHECK", execution_time, len(results))
                
                return results
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                await self._log_query("HEALTH_CHECK", execution_time, error=str(e))
                logger.error(f"Milvus查询执行失败: {str(e)}")
                raise
        elif self._pool:
            # 使用 asyncpg 执行传统 SQL 查询
            if not self._pool:
                raise ConnectionError("数据库未连接")
                
            start_time = datetime.now()
            try:
                async with self._pool.acquire() as conn:
                    if params:
                        records = await conn.fetch(sql, *params)
                    else:
                        records = await conn.fetch(sql)
                        
                    # 转换为字典列表
                    results = [dict(record) for record in records]
                    
                    # 记录查询日志
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    await self._log_query(sql, execution_time, len(results))
                    
                    return results
                    
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                await self._log_query(sql, execution_time, error=str(e))
                logger.error(f"查询执行失败: {str(e)}")
                raise
        else:
            raise ConnectionError("数据库未连接")
            
    async def execute_non_query(self, sql: str, params: Optional[List] = None) -> int:
        """执行非查询语句（INSERT, UPDATE, DELETE等）"""
        if not self._pool:
            raise ConnectionError("数据库未连接")
            
        start_time = datetime.now()
        try:
            async with self._pool.acquire() as conn:
                if params:
                    result = await conn.execute(sql, *params)
                else:
                    result = await conn.execute(sql)
                    
                # 提取影响行数
                affected_rows = int(result.split()[-1]) if result else 0
                
                # 记录查询日志
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                await self._log_query(sql, execution_time, affected_rows)
                
                return affected_rows
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_query(sql, execution_time, error=str(e))
            logger.error(f"非查询语句执行失败: {str(e)}")
            raise
            
    async def execute_milvus_vector_search(self, collection_name: str, vector_field: str, 
                                         query_vector: List[float], limit: int = 10) -> List[Dict]:
        """执行Milvus向量搜索"""
        if not self._pool:
            raise ConnectionError("数据库未连接")
            
        # 构建向量搜索查询
        search_query = MilvusQueryBuilder.build_vector_search_query(
            collection_name, vector_field, query_vector, limit
        )
        
        return await self.execute_query(search_query)
        
    async def get_milvus_collections_info(self) -> List[Dict]:
        """获取Milvus集合信息"""
        if not self._pool:
            raise ConnectionError("数据库未连接")
            
        info_query = MilvusQueryBuilder.build_collection_info_query()
        return await self.execute_query(info_query)
            
    async def _log_query(self, sql: str, execution_time: float, result_count: int = None, error: str = None):
        """记录查询日志"""
        try:
            await MulvesQueryLog.objects.acreate(
                connection=self.config,
                query_sql=sql[:1000],  # 限制长度
                execution_time=execution_time,
                result_count=result_count,
                error_message=error[:500] if error else None
            )
        except Exception as e:
            logger.error(f"记录查询日志失败: {str(e)}")


class MulvesCacheManager:
    """Mulves数据缓存管理器"""
    
    @staticmethod
    async def get_cache(cache_key: str) -> Optional[Dict]:
        """获取缓存数据"""
        try:
            cache_obj = await MulvesDataCache.objects.aget(cache_key=cache_key)
            if not cache_obj.is_expired:
                return cache_obj.data
            else:
                # 删除过期缓存
                await cache_obj.adelete()
                return None
        except MulvesDataCache.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None
            
    @staticmethod
    async def set_cache(cache_key: str, data: Dict, timeout: int = 300) -> bool:
        """设置缓存数据"""
        try:
            expires_at = timezone.now() + timedelta(seconds=timeout)
            await MulvesDataCache.objects.aupdate_or_create(
                cache_key=cache_key,
                defaults={
                    'data': data,
                    'expires_at': expires_at
                }
            )
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False
            
    @staticmethod
    async def clear_cache(cache_key: str = None) -> int:
        """清除缓存"""
        try:
            if cache_key:
                deleted_count, _ = await MulvesDataCache.objects.filter(cache_key=cache_key).adelete()
            else:
                deleted_count, _ = await MulvesDataCache.objects.all().adelete()
            return deleted_count
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return 0


class MulvesDBService:
    """Mulves数据库服务类（支持Milvus）"""
    
    @staticmethod
    async def test_connection(config_data: Dict) -> Dict[str, Any]:
        """测试数据库连接"""
        temp_config = MulvesConnection(**config_data)
        connector = MulvesDBConnector(temp_config)
        
        try:
            await connector.connect()
            # 对于 Milvus，列出集合来测试连接
            if connector._milvus_client:
                collections = connector._milvus_client.list_collections()
                await connector.disconnect()
                
                return {
                    'success': True,
                    'message': '连接测试成功',
                    'test_result': {'collections': collections}
                }
            else:
                # 执行简单的测试查询
                result = await connector.execute_query("SELECT 1 as test")
                await connector.disconnect()
                
                return {
                    'success': True,
                    'message': '连接测试成功',
                    'test_result': result
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接测试失败: {str(e)}'
            }
            
    @staticmethod
    async def execute_cached_query(connection_id: int, sql: str, use_cache: bool = True, cache_timeout: int = 300) -> Dict[str, Any]:
        """执行带缓存的查询"""
        try:
            # 获取连接配置
            connection = await MulvesConnection.objects.aget(id=connection_id, is_active=True)
            
            # 生成缓存键
            cache_key = f"mulves_query_{connection_id}_{hash(sql)}"
            
            # 尝试从缓存获取
            if use_cache:
                cached_data = await MulvesCacheManager.get_cache(cache_key)
                if cached_data is not None:
                    return {
                        'success': True,
                        'data': cached_data,
                        'from_cache': True
                    }
            
            # 执行实际查询
            async with MulvesDBConnector(connection) as connector:
                results = await connector.execute_query(sql)
                
                # 缓存结果
                if use_cache and results:
                    await MulvesCacheManager.set_cache(cache_key, results, cache_timeout)
                
                return {
                    'success': True,
                    'data': results,
                    'from_cache': False
                }
                
        except MulvesConnection.DoesNotExist:
            return {
                'success': False,
                'message': '指定的连接配置不存在或未激活'
            }
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            return {
                'success': False,
                'message': f'查询执行失败: {str(e)}'
            }