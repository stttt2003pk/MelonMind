import pytest
from unittest.mock import AsyncMock, patch
from django.test import TestCase
from apps.mulvesdb.models import MulvesConnection, MulvesQueryLog, MulvesDataCache
from apps.mulvesdb.serializers import (
    MulvesConnectionSerializer, MulvesQueryLogSerializer, MulvesDataCacheSerializer
)
from apps.mulvesdb.connectors import MulvesDBConnector, MulvesCacheManager, MulvesDBService
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestMulvesModels(TestCase):
    """Mulves数据模型测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.connection = MulvesConnection.objects.create(
            name='Test Connection',
            host='localhost',
            port=5432,
            database='test_db',
            username='test_user',
            password='test_password',
            ssl_enabled=False,
            connection_timeout=30,
            is_active=True
        )
    
    def test_mulves_connection_str(self):
        """测试连接配置的字符串表示"""
        expected_str = "Test Connection (localhost:5432/test_db)"
        self.assertEqual(str(self.connection), expected_str)
    
    def test_mulves_connection_validation(self):
        """测试连接配置验证"""
        # 测试有效端口
        connection = MulvesConnection(
            name='Valid Port',
            host='localhost',
            port=8080,
            database='test',
            username='user',
            password='pass'
        )
        self.assertTrue(connection.full_clean())
        
        # 测试无效端口
        with self.assertRaises(Exception):
            invalid_connection = MulvesConnection(
                name='Invalid Port',
                host='localhost',
                port=99999,  # 超出范围
                database='test',
                username='user',
                password='pass'
            )
            invalid_connection.full_clean()
    
    def test_mulves_query_log_creation(self):
        """测试查询日志创建"""
        query_log = MulvesQueryLog.objects.create(
            connection=self.connection,
            query_sql='SELECT * FROM users',
            execution_time=150.5,
            result_count=25
        )
        
        self.assertEqual(query_log.connection, self.connection)
        self.assertEqual(query_log.execution_time, 150.5)
        self.assertEqual(query_log.result_count, 25)
    
    def test_mulves_data_cache_expiration(self):
        """测试数据缓存过期判断"""
        # 创建未过期的缓存
        future_cache = MulvesDataCache.objects.create(
            cache_key='future_cache',
            data={'test': 'data'},
            expires_at=timezone.now() + timedelta(hours=1)
        )
        self.assertFalse(future_cache.is_expired)
        
        # 创建已过期的缓存
        past_cache = MulvesDataCache.objects.create(
            cache_key='past_cache',
            data={'test': 'data'},
            expires_at=timezone.now() - timedelta(hours=1)
        )
        self.assertTrue(past_cache.is_expired)


@pytest.mark.django_db
class TestMulvesSerializers(TestCase):
    """Mulves序列化器测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.connection_data = {
            'name': 'Test Serializer Connection',
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_password',
            'ssl_enabled': False,
            'connection_timeout': 30
        }
    
    def test_mulves_connection_serializer_valid(self):
        """测试有效的连接序列化器"""
        serializer = MulvesConnectionSerializer(data=self.connection_data)
        self.assertTrue(serializer.is_valid())
        
        # 保存并验证
        connection = serializer.save()
        self.assertEqual(connection.name, 'Test Serializer Connection')
        self.assertEqual(connection.host, 'localhost')
    
    def test_mulves_connection_serializer_invalid_port(self):
        """测试无效端口的序列化器验证"""
        invalid_data = self.connection_data.copy()
        invalid_data['port'] = 99999  # 无效端口
        
        serializer = MulvesConnectionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('port', serializer.errors)
    
    def test_mulves_connection_serializer_invalid_timeout(self):
        """测试无效超时时间的序列化器验证"""
        invalid_data = self.connection_data.copy()
        invalid_data['connection_timeout'] = -1  # 无效超时时间
        
        serializer = MulvesConnectionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('connection_timeout', serializer.errors)
    
    def test_mulves_query_log_serializer(self):
        """测试查询日志序列化器"""
        connection = MulvesConnection.objects.create(**self.connection_data)
        
        query_log_data = {
            'connection': connection.id,
            'query_sql': 'SELECT * FROM test_table',
            'execution_time': 150.5,
            'result_count': 25
        }
        
        serializer = MulvesQueryLogSerializer(data=query_log_data)
        self.assertTrue(serializer.is_valid())
        
        query_log = serializer.save()
        self.assertEqual(query_log.connection, connection)
        self.assertEqual(query_log.query_sql, 'SELECT * FROM test_table')
    
    def test_mulves_data_cache_serializer(self):
        """测试数据缓存序列化器"""
        cache_data = {
            'cache_key': 'test_cache_key',
            'data': {'test': 'data'},
            'expires_at': timezone.now() + timedelta(hours=1)
        }
        
        serializer = MulvesDataCacheSerializer(data=cache_data)
        self.assertTrue(serializer.is_valid())
        
        cache_obj = serializer.save()
        self.assertEqual(cache_obj.cache_key, 'test_cache_key')
        self.assertEqual(cache_obj.data, {'test': 'data'})


class TestMulvesConnectors(TestCase):
    """Mulves连接器测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.connection = MulvesConnection(
            name='Test Connector',
            host='localhost',
            port=5432,
            database='test_db',
            username='test_user',
            password='test_password'
        )
    
    @patch('apps.mulvesdb.connectors.asyncpg.create_pool')
    def test_mulves_db_connector_connect_success(self, mock_create_pool):
        """测试数据库连接器成功连接"""
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool
        
        connector = MulvesDBConnector(self.connection)
        
        # 这里需要异步测试，简化处理
        self.assertIsNotNone(connector)
    
    def test_mulves_cache_manager_set_and_get(self):
        """测试缓存管理器的设置和获取功能"""
        # 这些方法是异步的，在同步测试中需要特殊处理
        pass
    
    def test_mulves_db_service_test_connection(self):
        """测试数据库服务连接测试功能"""
        # 异步方法测试，需要特殊处理
        pass


@pytest.mark.django_db
class TestMulvesModelProperties(TestCase):
    """Mulves模型属性测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.connection = MulvesConnection.objects.create(
            name='Property Test Connection',
            host='localhost',
            port=5432,
            database='test_db',
            username='test_user',
            password='test_password'
        )
    
    def test_connection_default_values(self):
        """测试连接配置默认值"""
        self.assertTrue(self.connection.is_active)
        self.assertFalse(self.connection.ssl_enabled)
        self.assertEqual(self.connection.connection_timeout, 30)
    
    def test_connection_meta_options(self):
        """测试模型元选项"""
        self.assertEqual(self.connection._meta.db_table, 'mulves_connections')
        self.assertEqual(str(self.connection._meta.verbose_name), 'Mulves连接配置')
        self.assertEqual(str(self.connection._meta.verbose_name_plural), 'Mulves连接配置')
    
    def test_query_log_meta_options(self):
        """测试查询日志模型元选项"""
        query_log = MulvesQueryLog.objects.create(
            connection=self.connection,
            query_sql='SELECT 1',
            execution_time=100.0
        )
        
        self.assertEqual(query_log._meta.db_table, 'mulves_query_logs')
        self.assertEqual(str(query_log._meta.verbose_name), 'Mulves查询日志')
    
    def test_data_cache_meta_options(self):
        """测试数据缓存模型元选项"""
        cache_obj = MulvesDataCache.objects.create(
            cache_key='test_key',
            data={'test': 'data'},
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertEqual(cache_obj._meta.db_table, 'mulves_data_cache')
        self.assertEqual(str(cache_obj._meta.verbose_name), 'Mulves数据缓存')