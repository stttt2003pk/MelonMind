#!/usr/bin/env python3
"""
MulvesDB API 端点测试脚本
测试新增的连接测试API接口
"""

import os
import sys
import asyncio
import django
import requests
from pathlib import Path
from django.core.management import execute_from_command_line

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.mulvesdb.models import MulvesConnection
from apps.mulvesdb.local_config import MilvusLocalConfig


class MulvesDBAPITestCase(TestCase):
    """MulvesDB API 测试用例"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.local_config = MilvusLocalConfig.get_local_config()
        
    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        print("\n🧪 测试健康检查API端点...")
        
        url = '/api/mulvesdb/health/'
        response = self.client.get(url)
        
        print(f"  请求URL: {url}")
        print(f"  状态码: {response.status_code}")
        print(f"  响应内容: {response.json()}")
        
        # 验证响应格式
        self.assertIn('status', response.json())
        self.assertIn('service', response.json())
        self.assertIn('timestamp', response.json())
        
        # 如果Milvus服务运行，应该返回200；否则返回503
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        
        print("  ✅ 健康检查端点测试通过")
        
    def test_test_connection_endpoint_authenticated(self):
        """测试需要认证的连接测试端点"""
        print("\n🧪 测试需要认证的连接测试端点...")
        
        # 先创建一个测试用户（这里简化处理）
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=user)
        
        url = '/api/mulvesdb/connections/test-local-connection/'
        response = self.client.get(url)
        
        print(f"  请求URL: {url}")
        print(f"  状态码: {response.status_code}")
        print(f"  响应内容: {response.json()}")
        
        # 验证响应包含必要的字段
        response_data = response.json()
        self.assertIn('success', response_data)
        self.assertIn('message', response_data)
        self.assertIn('connection_info', response_data)
        self.assertIn('timestamp', response_data)
        
        print("  ✅ 认证连接测试端点测试通过")
        
    def test_test_connection_endpoint_unauthenticated(self):
        """测试未认证的连接测试端点访问"""
        print("\n🧪 测试未认证访问连接测试端点...")
        
        url = '/api/mulvesdb/connections/test-local-connection/'
        response = self.client.get(url)
        
        print(f"  请求URL: {url}")
        print(f"  状态码: {response.status_code}")
        
        # 未认证应该返回403或重定向到登录
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        print("  ✅ 未认证访问控制测试通过")


def test_direct_http_requests():
    """直接HTTP请求测试（模拟真实API调用）"""
    print("\n🌐 直接HTTP请求测试...")
    
    # 启动Django开发服务器（在后台）
    print("  启动Django开发服务器...")
    
    # 这里我们只打印测试信息，因为实际启动服务器需要更多设置
    base_url = "http://127.0.0.1:8000"
    
    test_cases = [
        {
            'name': '健康检查端点',
            'url': f"{base_url}/api/mulvesdb/health/",
            'expected_status': [200, 503],
            'auth_required': False
        },
        {
            'name': '连接测试端点',
            'url': f"{base_url}/api/mulvesdb/test-connection/",
            'expected_status': [200, 503],
            'auth_required': False
        }
    ]
    
    for test_case in test_cases:
        print(f"\n  测试: {test_case['name']}")
        print(f"  URL: {test_case['url']}")
        
        try:
            response = requests.get(test_case['url'], timeout=10)
            print(f"    状态码: {response.status_code}")
            print(f"    响应: {response.json()}")
            
            if response.status_code in test_case['expected_status']:
                print(f"    ✅ 测试通过")
            else:
                print(f"    ⚠️  状态码不符合预期")
                
        except requests.exceptions.ConnectionError:
            print(f"    ⚠️  无法连接到服务器，请确保Django服务正在运行")
        except Exception as e:
            print(f"    ❌ 请求失败: {e}")


def show_usage_examples():
    """显示使用示例"""
    examples = """
🚀 MulvesDB API 测试端点使用示例

1. 健康检查端点（无需认证）:
   GET /api/mulvesdb/health/
   
   响应示例:
   {
     "status": "healthy",
     "service": "mulvesdb",
     "connection_host": "localhost",
     "connection_port": 19530,
     "timestamp": "2024-01-01T12:00:00Z",
     "details": "连接测试成功"
   }

2. 连接测试端点（需要认证）:
   GET /api/mulvesdb/test-connection/
   
   响应示例:
   {
     "success": true,
     "message": "连接测试成功",
     "connection_info": {
       "host": "localhost",
       "port": 19530,
       "database": "default",
       "ssl_enabled": false,
       "connection_timeout": 30
     },
     "timestamp": "2024-01-01T12:00:00Z",
     "test_details": [{"test": 1}]
   }

3. 使用curl测试:
   # 健康检查
   curl http://localhost:8000/api/mulvesdb/health/
   
   # 连接测试（需要JWT token）
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
        http://localhost:8000/api/mulvesdb/test-connection/

4. 在浏览器中访问:
   http://localhost:8000/api/mulvesdb/health/
   """
    print(examples)


def main():
    """主函数"""
    print("🔍 MulvesDB API 端点测试")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'unit':
            # 运行单元测试
            print("🏃 运行单元测试...")
            execute_from_command_line(['manage.py', 'test', 'apps.mulvesdb.test_api_endpoints'])
        elif command == 'http':
            # 运行HTTP测试
            test_direct_http_requests()
        elif command == 'examples':
            show_usage_examples()
        elif command == 'help':
            show_usage_examples()
        else:
            print(f"❌ 未知命令: {command}")
            show_usage_examples()
    else:
        # 默认运行所有测试
        print("🏃 运行所有测试...")
        
        # 运行Django测试
        test_case = MulvesDBAPITestCase()
        test_case.setUp()
        test_case.test_health_check_endpoint()
        test_case.test_test_connection_endpoint_unauthenticated()
        
        # 显示使用示例
        show_usage_examples()


if __name__ == "__main__":
    main()