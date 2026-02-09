import asyncio
import asyncpg
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache
import psycopg2
from psycopg2.extras import RealDictCursor

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
        """建立数据库连接池（异步版本）"""
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
            
    def connect_sync(self) -> bool:
        """建立数据库连接（同步版本）"""
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
                # 使用 psycopg2 进行同步连接
                self._sync_conn = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    sslmode='require' if self.config.ssl_enabled else 'disable',
                    connect_timeout=self.config.connection_timeout
                )
                logger.info(f"成功连接到Mulves数据库: {self.config.name}")
                return True
        except Exception as e:
            logger.error(f"连接Mulves数据库失败 {self.config.name}: {str(e)}")
            raise ConnectionError(f"无法连接到Mulves数据库: {str(e)}")
            
    async def disconnect(self):
        """关闭数据库连接池（异步版本）"""
        if self._milvus_client:
            # Milvus 客户端不需要显式关闭
            self._milvus_client = None
            logger.info(f"已断开Milvus数据库连接: {self.config.name}")
        elif self._pool:
            await self._pool.close()
            self._pool = None
            logger.info(f"已断开Mulves数据库连接: {self.config.name}")
            
    def disconnect_sync(self):
        """关闭数据库连接（同步版本）"""
        if self._milvus_client:
            # Milvus 客户端不需要显式关闭
            self._milvus_client = None
            logger.info(f"已断开Milvus数据库连接: {self.config.name}")
        elif self._sync_conn:
            self._sync_conn.close()
            self._sync_conn = None
            logger.info(f"已断开Mulves数据库连接: {self.config.name}")
            
    async def execute_query(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """执行查询并返回结果（异步版本）"""
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
            
    def execute_query_sync(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """执行查询并返回结果（同步版本）"""
        if self._milvus_client:
            # 使用 Milvus 客户端执行查询
            start_time = datetime.now()
            try:
                # 对于 Milvus，我们执行健康检查而不是 SQL 查询
                result = self._milvus_client.health()
                results = [{'status': result}] if result else []
                
                # 记录查询日志
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                self._log_query_sync("HEALTH_CHECK", execution_time, len(results))
                
                return results
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                self._log_query_sync("HEALTH_CHECK", execution_time, error=str(e))
                logger.error(f"Milvus查询执行失败: {str(e)}")
                raise
        elif self._sync_conn:
            # 使用 psycopg2 执行传统 SQL 查询
            if not self._sync_conn:
                raise ConnectionError("数据库未连接")
                
            start_time = datetime.now()
            try:
                with self._sync_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                        
                    # 获取结果
                    results = [dict(row) for row in cursor.fetchall()]
                    
                    # 记录查询日志
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    self._log_query_sync(sql, execution_time, len(results))
                    
                    return results
                    
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                self._log_query_sync(sql, execution_time, error=str(e))
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
            
    async def insert_milvus_data(self, collection_name: str, data: List[Dict]) -> Dict[str, Any]:
        """向Milvus集合插入数据
        
        Args:
            collection_name (str): 集合名称
            data (List[Dict]): 要插入的数据列表，每个字典代表一条记录
        
        Returns:
            Dict[str, Any]: 插入结果信息
        """
        if not self._milvus_client:
            raise ConnectionError("Milvus客户端未连接")
            
        start_time = datetime.now()
        try:
            # 检查集合是否存在
            collections = self._milvus_client.list_collections()
            if collection_name not in collections:
                raise ValueError(f"集合 '{collection_name}' 不存在")
            
            # 插入数据
            result = self._milvus_client.insert(
                collection_name=collection_name,
                data=data
            )
            
            # 记录操作日志
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_query(f"INSERT INTO {collection_name}", execution_time, len(data))
            
            return {
                'success': True,
                'insert_count': len(data),
                'ids': result.primary_keys if hasattr(result, 'primary_keys') else [],
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_query(f"INSERT INTO {collection_name}", execution_time, error=str(e))
            logger.error(f"Milvus数据插入失败: {str(e)}")
            raise
    
    def _log_query_sync(self, sql: str, execution_time: float, result_count: int = None, error: str = None):
        """记录查询日志（同步版本）"""
        try:
            MulvesQueryLog.objects.create(
                connection=self.config,
                query_sql=sql[:1000],  # 限制长度
                execution_time=execution_time,
                result_count=result_count,
                error_message=error[:500] if error else None
            )
        except Exception as e:
            logger.error(f"记录查询日志失败: {str(e)}")
    
    async def create_milvus_collection(self, collection_name: str, schema: Dict) -> bool:
        """创建Milvus集合
        
        Args:
            collection_name (str): 集合名称
            schema (Dict): 集合schema定义
        
        Returns:
            bool: 创建是否成功
        """
        if not self._milvus_client:
            raise ConnectionError("Milvus客户端未连接")
            
        try:
            # 检查集合是否已存在
            collections = self._milvus_client.list_collections()
            if collection_name in collections:
                logger.warning(f"集合 '{collection_name}' 已存在")
                return True
            
            # 创建集合
            self._milvus_client.create_collection(
                collection_name=collection_name,
                schema=schema
            )
            
            logger.info(f"成功创建集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建Milvus集合失败: {str(e)}")
            raise
    
    async def drop_milvus_collection(self, collection_name: str) -> bool:
        """删除Milvus集合
        
        Args:
            collection_name (str): 集合名称
        
        Returns:
            bool: 删除是否成功
        """
        if not self._milvus_client:
            raise ConnectionError("Milvus客户端未连接")
            
        try:
            # 检查集合是否存在
            collections = self._milvus_client.list_collections()
            if collection_name not in collections:
                logger.warning(f"集合 '{collection_name}' 不存在")
                return True
            
            # 删除集合
            self._milvus_client.drop_collection(collection_name=collection_name)
            
            logger.info(f"成功删除集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除Milvus集合失败: {str(e)}")
            raise
    
    async def execute_milvus_vector_search(self, collection_name: str, vector_field: str, 
                                         query_vector: List[float], limit: int = 10) -> List[Dict]:
        """执行Milvus向量搜索"""
        if not self._milvus_client:
            raise ConnectionError("Milvus客户端未连接")
            
        try:
            # 执行向量搜索
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            result = self._milvus_client.search(
                collection_name=collection_name,
                data=[query_vector],
                anns_field=vector_field,
                search_params=search_params,
                limit=limit,
                output_fields=["*"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Milvus向量搜索失败: {str(e)}")
            raise
        
    async def get_milvus_collections_info(self) -> List[Dict]:
        """获取Milvus集合信息"""
        if not self._milvus_client:
            raise ConnectionError("Milvus客户端未连接")
            
        try:
            collections = self._milvus_client.list_collections()
            info_list = []
            
            for collection_name in collections:
                stats = self._milvus_client.get_collection_stats(collection_name)
                info_list.append({
                    'name': collection_name,
                    'row_count': stats.get('row_count', 0) if stats else 0
                })
            
            return info_list
            
        except Exception as e:
            logger.error(f"获取Milvus集合信息失败: {str(e)}")
            raise
    
    def get_milvus_collections_info_sync(self) -> List[Dict]:
        """获取Milvus集合信息（同步版本）"""
        if not self._milvus_client:
            raise ConnectionError("Milvus客户端未连接")
            
        try:
            collections = self._milvus_client.list_collections()
            info_list = []
            
            for collection_name in collections:
                stats = self._milvus_client.get_collection_stats(collection_name)
                info_list.append({
                    'name': collection_name,
                    'row_count': stats.get('row_count', 0) if stats else 0
                })
            
            return info_list
            
        except Exception as e:
            logger.error(f"获取Milvus集合信息失败: {str(e)}")
            raise
            
    async def _log_query(self, sql: str, execution_time: float, result_count: int = None, error: str = None):
        """记录查询日志（异步版本）"""
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
            
    def _log_query_sync(self, sql: str, execution_time: float, result_count: int = None, error: str = None):
        """记录查询日志（同步版本）"""
        try:
            MulvesQueryLog.objects.create(
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
        """获取缓存数据（异步版本）"""
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
    def get_cache_sync(cache_key: str) -> Optional[Dict]:
        """获取缓存数据（同步版本）"""
        try:
            cache_obj = MulvesDataCache.objects.get(cache_key=cache_key)
            if not cache_obj.is_expired:
                return cache_obj.data
            else:
                # 删除过期缓存
                cache_obj.delete()
                return None
        except MulvesDataCache.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None
            
    @staticmethod
    async def set_cache(cache_key: str, data: Dict, timeout: int = 300) -> bool:
        """设置缓存数据（异步版本）"""
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
    def set_cache_sync(cache_key: str, data: Dict, timeout: int = 300) -> bool:
        """设置缓存数据（同步版本）"""
        try:
            expires_at = timezone.now() + timedelta(seconds=timeout)
            MulvesDataCache.objects.update_or_create(
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
        """清除缓存（异步版本）"""
        try:
            if cache_key:
                deleted_count, _ = await MulvesDataCache.objects.filter(cache_key=cache_key).adelete()
            else:
                deleted_count, _ = await MulvesDataCache.objects.all().adelete()
            return deleted_count
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return 0
            
    @staticmethod
    def clear_cache_sync(cache_key: str = None) -> int:
        """清除缓存（同步版本）"""
        try:
            if cache_key:
                deleted_count, _ = MulvesDataCache.objects.filter(cache_key=cache_key).delete()
            else:
                deleted_count, _ = MulvesDataCache.objects.all().delete()
            return deleted_count
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return 0


class MulvesDBService:
    """Mulves数据库服务类（支持Milvus）"""
    
    @staticmethod
    async def test_connection(config_data: Dict) -> Dict[str, Any]:
        """测试数据库连接（异步版本）"""
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
    def test_connection_sync(config_data: Dict) -> Dict[str, Any]:
        """测试数据库连接（同步版本）"""
        temp_config = MulvesConnection(**config_data)
        connector = MulvesDBConnector(temp_config)
        
        try:
            connector.connect_sync()
            # 对于 Milvus，列出集合来测试连接
            if connector._milvus_client:
                collections = connector._milvus_client.list_collections()
                connector.disconnect_sync()
                
                return {
                    'success': True,
                    'message': '连接测试成功',
                    'test_result': {'collections': collections}
                }
            else:
                # 执行简单的测试查询
                result = connector.execute_query_sync("SELECT 1 as test")
                connector.disconnect_sync()
                
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
        """执行带缓存的查询（异步版本）"""
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
            
    @staticmethod
    def execute_cached_query_sync(connection_id: int, sql: str, use_cache: bool = True, cache_timeout: int = 300) -> Dict[str, Any]:
        """执行带缓存的查询（同步版本）"""
        try:
            # 获取连接配置
            connection = MulvesConnection.objects.get(id=connection_id, is_active=True)
            
            # 生成缓存键
            cache_key = f"mulves_query_{connection_id}_{hash(sql)}"
            
            # 尝试从缓存获取
            if use_cache:
                cached_data = MulvesCacheManager.get_cache_sync(cache_key)
                if cached_data is not None:
                    return {
                        'success': True,
                        'data': cached_data,
                        'from_cache': True
                    }
            
            # 执行实际查询
            connector = MulvesDBConnector(connection)
            try:
                connector.connect_sync()
                results = connector.execute_query_sync(sql)
                
                # 缓存结果
                if use_cache and results:
                    MulvesCacheManager.set_cache_sync(cache_key, results, cache_timeout)
                
                return {
                    'success': True,
                    'data': results,
                    'from_cache': False
                }
            finally:
                connector.disconnect_sync()
                
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
    
    @staticmethod
    async def insert_data_to_milvus(connection_id: int, collection_name: str, data: List[Dict], 
                                  enable_dedup: bool = True, document_id: Optional[int] = None) -> Dict[str, Any]:
        """向Milvus插入数据的服务方法（支持去重）
        
        Args:
            connection_id (int): 连接配置ID
            collection_name (str): 集合名称
            data (List[Dict]): 要插入的数据
            enable_dedup (bool): 是否启用去重功能
            document_id (Optional[int]): 文档ID
        
        Returns:
            Dict[str, Any]: 插入结果
        """
        try:
            # 获取连接配置
            connection = await MulvesConnection.objects.aget(id=connection_id, is_active=True)
            
            # 执行插入操作
            async with MulvesDBConnector(connection) as connector:
                result = await connector.insert_milvus_data(collection_name, data, enable_dedup, document_id)
                message = f'成功插入 {result["insert_count"]} 条记录'
                if result.get('filtered_count', 0) > 0:
                    message += f'（过滤 {result["filtered_count"]} 个重复块）'
                
                return {
                    'success': True,
                    'message': message,
                    'data': result
                }
                
        except MulvesConnection.DoesNotExist:
            return {
                'success': False,
                'message': '指定的连接配置不存在或未激活'
            }
        except Exception as e:
            logger.error(f"插入数据失败: {str(e)}")
            return {
                'success': False,
                'message': f'数据插入失败: {str(e)}'
            }
    
    @staticmethod
    async def create_milvus_collection_service(connection_id: int, collection_name: str, schema: Dict) -> Dict[str, Any]:
        """创建Milvus集合的服务方法
        
        Args:
            connection_id (int): 连接配置ID
            collection_name (str): 集合名称
            schema (Dict): 集合schema
        
        Returns:
            Dict[str, Any]: 创建结果
        """
        try:
            # 获取连接配置
            connection = await MulvesConnection.objects.aget(id=connection_id, is_active=True)
            
            # 执行创建操作
            async with MulvesDBConnector(connection) as connector:
                await connector.create_milvus_collection(collection_name, schema)
                return {
                    'success': True,
                    'message': f'成功创建集合: {collection_name}'
                }
                
        except MulvesConnection.DoesNotExist:
            return {
                'success': False,
                'message': '指定的连接配置不存在或未激活'
            }
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            return {
                'success': False,
                'message': f'集合创建失败: {str(e)}'
            }
    
    @staticmethod
    async def search_vectors_in_milvus(connection_id: int, collection_name: str, 
                                     vector_field: str, query_vector: List[float], 
                                     limit: int = 10) -> Dict[str, Any]:
        """在Milvus中搜索向量
        
        Args:
            connection_id (int): 连接配置ID
            collection_name (str): 集合名称
            vector_field (str): 向量字段名
            query_vector (List[float]): 查询向量
            limit (int): 返回结果数量限制
        
        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            # 获取连接配置
            connection = await MulvesConnection.objects.aget(id=connection_id, is_active=True)
            
            # 执行搜索操作
            async with MulvesDBConnector(connection) as connector:
                results = await connector.execute_milvus_vector_search(
                    collection_name, vector_field, query_vector, limit
                )
                return {
                    'success': True,
                    'message': f'搜索完成，返回 {len(results)} 条结果',
                    'data': results
                }
                
        except MulvesConnection.DoesNotExist:
            return {
                'success': False,
                'message': '指定的连接配置不存在或未激活'
            }
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return {
                'success': False,
                'message': f'向量搜索失败: {str(e)}'
            }