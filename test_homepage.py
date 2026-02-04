#!/usr/bin/env python
"""
测试HTML主页功能的脚本
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_homepage():
    """测试HTML主页访问"""
    client = Client()
    
    # 测试HTML主页
    print("_testing HTML homepage...")
    response = client.get('/')
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response['Content-Type']}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if '<title>MelonMind' in content:
            print("✅ HTML homepage test passed!")
        else:
            print("❌ HTML content check failed")
    else:
        print(f"❌ HTML homepage test failed with status {response.status_code}")

def test_api_home():
    """测试API首页"""
    client = Client()
    
    print("\n_testing API homepage...")
    response = client.get('/api/')
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response['Content-Type']}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        if 'message' in data and 'MelonMind API' in data['message']:
            print("✅ API homepage test passed!")
        else:
            print("❌ API content check failed")
    else:
        print(f"❌ API homepage test failed with status {response.status_code}")

def test_health_check():
    """测试健康检查接口"""
    client = Client()
    
    print("\n_testing health check...")
    response = client.get('/health/')
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        if 'status' in data and data['status'] == 'healthy':
            print("✅ Health check test passed!")
        else:
            print("❌ Health check content failed")
    else:
        print(f"❌ Health check test failed with status {response.status_code}")

if __name__ == '__main__':
    print("Starting homepage tests...\n")
    test_homepage()
    test_api_home()
    test_health_check()
    print("\nAll tests completed!")