"""
快速测试Qwen API密钥有效性
"""

import os
import sys
from openai import OpenAI

def test_qwen_api():
    """测试Qwen API连接"""
    print("测试Qwen API连接...")
    
    api_key = os.environ.get('QWEN_API_KEY')
    if not api_key:
        print("❌ 未找到QWEN_API_KEY环境变量")
        return False
    
    print(f"✓ 找到API密钥: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # 创建客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 测试简单的embedding请求
        print("发送测试embedding请求...")
        response = client.embeddings.create(
            model="text-embedding-v1",
            input=["This is a test sentence for embedding."]
        )
        
        # 检查响应
        if response and response.data:
            embedding = response.data[0].embedding
            print(f"✓ 成功获得embedding")
            print(f"  向量维度: {len(embedding)}")
            print(f"  前5维数值: {[round(x, 4) for x in embedding[:5]]}")
            return True
        else:
            print("❌ API响应为空")
            return False
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Qwen API密钥验证测试")
    print("=" * 50)
    
    success = test_qwen_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Qwen API密钥验证通过！")
        print("可以使用真实embedding服务进行测试。")
    else:
        print("❌ Qwen API密钥验证失败！")
        print("建议检查API密钥是否正确，或使用mock服务进行测试。")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())