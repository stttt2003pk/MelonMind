#!/usr/bin/env python
"""
简单的连通性测试脚本
用于测试MelonMind API的基本功能
"""

import requests
import json

def test_api_endpoints():
    """测试各个API端点"""
    base_url = "http://127.0.0.1:8000"
    
    # 测试的端点列表
    endpoints = [
        ("/api/", "默认主页"),
        ("/api/health/", "健康检查"),
        ("/api/agents/", "Agents API"),
        ("/api/knowledge/", "Knowledge Base API"),
        ("/admin/", "管理后台"),
    ]
    
    print("🔍 开始测试 MelonMind API 连通性...\n")
    
    for endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {description} ({url}) - 状态: {response.status_code}")
                if endpoint in ["/api/", "/api/health/"]:
                    try:
                        data = response.json()
                        print(f"   返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"   返回内容: {response.text[:200]}...")
            elif response.status_code == 404:
                print(f"❌ {description} ({url}) - 端点不存在 (404)")
            else:
                print(f"⚠️  {description} ({url}) - 状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {description} ({url}) - 连接失败，请确认服务器是否运行")
        except requests.exceptions.Timeout:
            print(f"⏰ {description} ({url}) - 请求超时")
        except Exception as e:
            print(f"💥 {description} ({url}) - 错误: {str(e)}")
        
        print()  # 空行分隔

def test_post_request():
    """测试POST请求（如果需要）"""
    print("📝 测试POST请求示例...")
    url = "http://127.0.0.1:8000/api/"
    
    try:
        response = requests.post(url, json={"test": "data"}, timeout=5)
        print(f"POST {url} - 状态: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"POST请求测试失败: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("멜론마인드(MelonMind) API 连通性测试")
    print("=" * 50)
    
    # 先测试基本连通性
    test_api_endpoints()
    
    # 如果需要，可以测试POST请求
    # test_post_request()
    
    print("테스트 완료! (Test completed!)")