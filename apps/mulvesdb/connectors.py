import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache
import psycopg2
from psycopg2.extras import RealDictCursor
from .schema import collection_schema_dict
from pymilvus import CollectionSchema

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
            
    def connect_sync(self) -> bool:
        """建立数据库连接（同步版本）"""
        try:
            logger.info(f"尝试连接到Milvus: {self.config.host}:{self.config.port}")
            logger.info(f"用户名: '{self.config.username}', 密码: '{self.config.password}'")
            
            if MILVUS_AVAILABLE:
                # 使用 Milvus 官方客户端
                # 只有当用户名和密码都不为空时才使用token认证
                token = None
                if self.config.username and self.config.password:
                    token = f"{self.config.username}:{self.config.password}"
                    logger.info(f"使用token认证: {token}")
                elif self.config.username:
                    token = self.config.username
                    logger.info(f"使用用户名认证: {token}")
                else:
                    logger.info("不使用认证")
                
                self._milvus_client = MilvusClient(
                    uri=f"http://{self.config.host}:{self.config.port}",
                    token=token
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
            
    def execute_query_sync(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """执行查询并返回结果（同步版本）"""
        if self._milvus_client:
            # 使用 Milvus 客户端执行查询
            start_time = datetime.now()
            try:
                # 对于 Milvus，我们执行集合列表查询作为健康检查
                collections = self._milvus_client.list_collections()
                results = [{'collections_count': len(collections), 'collections': collections}]
                
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

    def insert_milvus_data_sync(self, collection_name: str, data: List[Dict], 
                               enable_dedup: bool = True, document_id: Optional[int] = None) -> Dict[str, Any]:
        """向Milvus集合插入数据（同步版本，支持去重）
        
        Args:
            collection_name (str): 集合名称
            data (List[Dict]): 要插入的数据列表，每个字典代表一条记录
            enable_dedup (bool): 是否启用去重功能
            document_id (Optional[int]): 文档ID，用于去重计算
        
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
            
            # 处理去重逻辑
            original_count = len(data)
            filtered_data = data
            filtered_count = 0
            
            if enable_dedup and document_id:
                from apps.mulvesdb.utils import filter_duplicate_chunks
                filtered_data = filter_duplicate_chunks(data, document_id)
                filtered_count = original_count - len(filtered_data)
                logger.info(f"去重处理: 原始 {original_count} 条，过滤后 {len(filtered_data)} 条")
            
            # 插入数据
            result = self._milvus_client.insert(
                collection_name=collection_name,
                data=filtered_data
            )
            
            # 记录操作日志
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._log_query_sync(f"INSERT INTO {collection_name}", execution_time, len(filtered_data))
            
            return {
                'success': True,
                'insert_count': len(filtered_data),
                'original_count': original_count,
                'filtered_count': filtered_count,
                'ids': result.primary_keys if hasattr(result, 'primary_keys') else [],
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._log_query_sync(f"INSERT INTO {collection_name}", execution_time, error=str(e))
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
    
    def create_milvus_collection_sync(self, collection_name: str, schema: Dict) -> bool:
        """创建Milvus集合（同步版本）
        
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
            collection_schema = CollectionSchema(
                fields=collection_schema_dict['fields'],
                description=collection_schema_dict['description']
            )

            self._milvus_client.create_collection(
                collection_name=collection_name,
                schema=collection_schema,

            )
            
            logger.info(f"成功创建集合: {collection_name}")

            # 3. 准备索引参数（使用官方示例的 prepare_index_params 方式）
            index_params = self._milvus_client.prepare_index_params()

            # 4.1 添加向量字段（embedding）的索引
            # 索引类型：IVF_FLAT，度量方式：L2，nlist：128
            index_params.add_index(
                field_name="embedding",
                index_type="IVF_FLAT",  # 向量索引类型
                metric_type="L2",  # 度量类型（仅向量字段需要）
                params={"nlist": 128},  # IVF_FLAT 索引的核心参数
                index_name="embedding_ivf_flat_index"  # 索引名称（自定义）
            )

            # 4.2 添加标量字段（document_id）的索引
            # 索引类型：STL_SORT（整型字段常用）
            index_params.add_index(
                field_name="document_id",
                index_type="STL_SORT",  # 整型标量索引类型
                params={},  # STL_SORT 无需额外参数
                index_name="document_id_stl_sort_index"
            )

            # 4.3 添加标量字段（vector_id）的索引
            # 索引类型：TRIE（VARCHAR 字段常用）
            index_params.add_index(
                field_name="vector_id",
                index_type="TRIE",  # VARCHAR 标量索引类型
                params={},  # TRIE 无需额外参数
                index_name="vector_id_trie_index"
            )

            self._milvus_client.create_index(
                collection_name=collection_name,
                index_params=index_params
            )

            logger.info(f"集合 {collection_name} 及索引创建成功！")
            return True
            
        except Exception as e:
            logger.error(f"创建Milvus集合失败: {str(e)}")
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
    def test_connection(config_data: Dict) -> Dict[str, Any]:
        """测试数据库连接"""
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
    
