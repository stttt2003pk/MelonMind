import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.mulvesdb.models import MulvesConnection, MulvesQueryLog, MulvesDataCache
from django.contrib.auth.models import User
import json


class MulvesDBTestCase(TestCase):
    """Mulves数据库App测试基类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = APIClient()
        self.client.login(username='testuser', password='testpass123')
        
        # 创建测试连接配置
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


@pytest.mark.django_db
class TestMulvesConnectionAPI(MulvesDBTestCase):
    """Mulves连接配置API测试"""
    
    def test_list_connections(self):
        """测试获取连接列表"""
        url = reverse('mulves-connection-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Connection')
    
    def test_create_connection(self):
        """测试创建连接配置"""
        url = reverse('mulves-connection-list')
        data = {
            'name': 'New Connection',
            'host': '192.168.1.100',
            'port': 5432,
            'database': 'new_db',
            'username': 'new_user',
            'password': 'new_password',
            'ssl_enabled': True,
            'connection_timeout': 60
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MulvesConnection.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Connection')
    
    def test_retrieve_connection(self):
        """测试获取单个连接详情"""
        url = reverse('mulves-connection-detail', kwargs={'pk': self.connection.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Connection')
        # 验证详细信息字段存在
        self.assertIn('query_count', response.data)
        self.assertIn('last_query_time', response.data)
    
    def test_update_connection(self):
        """测试更新连接配置"""
        url = reverse('mulves-connection-detail', kwargs={'pk': self.connection.pk})
        data = {
            'name': 'Updated Connection',
            'host': 'updated-host.com',
            'port': 5433,
            'database': 'updated_db',
            'username': 'updated_user',
            'password': 'updated_password',
            'ssl_enabled': True,
            'connection_timeout': 45
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.name, 'Updated Connection')
        self.assertEqual(self.connection.port, 5433)
    
    def test_delete_connection(self):
        """测试删除连接配置"""
        url = reverse('mulves-connection-detail', kwargs={'pk': self.connection.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MulvesConnection.objects.count(), 0)


@pytest.mark.django_db
class TestMulvesQueryAPI(MulvesDBTestCase):
    """Mulves查询API测试"""
    
    def test_execute_query_success(self):
        """测试成功执行查询"""
        url = reverse('mulves-query-list')
        data = {
            'connection_id': self.connection.id,
            'query_sql': 'SELECT * FROM users LIMIT 10',
            'use_cache': True,
            'cache_timeout': 300
        }
        
        response = self.client.post(url, data, format='json')
        
        # 注意：由于没有真实的数据库连接，这里会返回连接错误
        # 我们主要测试API结构和参数验证
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
    
    def test_execute_query_invalid_connection(self):
        """测试无效连接ID"""
        url = reverse('mulves-query-list')
        data = {
            'connection_id': 99999,  # 不存在的ID
            'query_sql': 'SELECT * FROM users',
            'use_cache': True,
            'cache_timeout': 300
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('连接配置不存在', response.data['message'])
    
    def test_execute_query_missing_params(self):
        """测试缺少必要参数"""
        url = reverse('mulves-query-list')
        data = {
            'query_sql': 'SELECT * FROM users'  # 缺少connection_id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('connection_id', response.data)


@pytest.mark.django_db
class TestMulvesQueryLogAPI(MulvesDBTestCase):
    """Mulves查询日志API测试"""
    
    def setUp(self):
        super().setUp()
        # 创建测试查询日志
        self.query_log = MulvesQueryLog.objects.create(
            connection=self.connection,
            query_sql='SELECT * FROM test_table',
            execution_time=150.5,
            result_count=25
        )
    
    def test_list_query_logs(self):
        """测试获取查询日志列表"""
        url = reverse('mulves-query-log-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['connection_name'], 'Test Connection')
    
    def test_filter_query_logs_by_connection(self):
        """测试按连接过滤查询日志"""
        url = reverse('mulves-query-log-list')
        response = self.client.get(url, {'connection_id': self.connection.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['connection'], self.connection.id)


@pytest.mark.django_db
class TestMulvesDataCacheAPI(MulvesDBTestCase):
    """Mulves数据缓存API测试"""
    
    def setUp(self):
        super().setUp()
        # 创建测试缓存数据
        from django.utils import timezone
        from datetime import timedelta
        
        self.cache_data = MulvesDataCache.objects.create(
            cache_key='test_cache_key',
            data={'test': 'data'},
            expires_at=timezone.now() + timedelta(hours=1)
        )
    
    def test_list_cache_data(self):
        """测试获取缓存数据列表"""
        url = reverse('mulves-data-cache-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['cache_key'], 'test_cache_key')
    
    def test_clear_all_cache(self):
        """测试清除所有缓存"""
        url = reverse('mulves-data-cache-clear-cache')
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['deleted_count'], 1)
    
    def test_clear_specific_cache(self):
        """测试清除特定缓存"""
        url = reverse('mulves-data-cache-clear-cache')
        response = self.client.delete(url, {'cache_key': 'test_cache_key'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


@pytest.mark.django_db
class TestMulvesConnectionStatusAPI(MulvesDBTestCase):
    """Mulves连接状态API测试"""
    
    def test_get_connection_status(self):
        """测试获取连接状态"""
        url = reverse('mulves-connection-connection-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Connection')
        self.assertTrue(response.data[0]['is_active'])


@pytest.mark.django_db
class TestMulvesTestConnectionAPI(MulvesDBTestCase):
    """Mulves连接测试API测试"""
    
    def test_test_connection_valid_params(self):
        """测试有效的连接参数"""
        url = reverse('mulves-connection-test-connection')
        data = {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_password',
            'ssl_enabled': False,
            'connection_timeout': 30
        }
        
        response = self.client.post(url, data, format='json')
        
        # 由于是测试环境，连接会失败，但我们验证API响应格式正确
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('message', response.data)
    
    def test_test_connection_invalid_params(self):
        """测试无效的连接参数"""
        url = reverse('mulves-connection-test-connection')
        data = {
            'host': 'localhost',
            'port': 99999,  # 无效端口
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_password'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('port', response.data)